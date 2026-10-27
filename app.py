import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Duka la Dawa System", page_icon="💊", layout="wide")

# --- INITIALIZE DATABASE & CART IN SESSION STATE ---
if "inventory" not in st.session_state:
    if os.path.exists("inventory.csv"):
        st.session_state.inventory = pd.read_csv("inventory.csv")
    else:
        st.session_state.inventory = pd.DataFrame(columns=[
            "ID", "Drug Name", "Category", "Cost Price (TZS)", 
            "Selling Price (TZS)", "Stock Qty", "Expiry Date"
        ])

if "sales_df" not in st.session_state:
    if os.path.exists("sales.csv"):
        st.session_state.sales_df = pd.read_csv("sales.csv")
    else:
        st.session_state.sales_df = pd.DataFrame(columns=[
            "Sale ID", "Date", "Drug Name", "Qty Sold", 
            "Total Price (TZS)", "Seller", "Payment Method", 
            "Patient Name", "Prescriber", "Dosage Instructions"
        ])

if "cart" not in st.session_state:
    st.session_state.cart = []

# Helper function to save data to CSV files
def save_data():
    st.session_state.inventory.to_csv("inventory.csv", index=False)
    st.session_state.sales_df.to_csv("sales.csv", index=False)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("💊 Duka la Dawa POS")
app_mode = st.sidebar.selectbox("Choose Mode", ["🛒 Seller Point of Sale (POS)", "🔒 Admin Dashboard"])

# ==========================================
# 1. SELLER POINT OF SALE (POS)
# ==========================================
if app_mode == "🛒 Seller Point of Sale (POS)":
    st.title("🛒 Pharmacy Sales Counter")
    st.markdown("Search medicines, calculate dosages, record patient prescriptions, and manage customer checkouts.")

    if st.session_state.inventory.empty:
        st.warning("No medicines in inventory yet. Please ask the Admin to add stock first.")
    else:
        col1, col2 = st.columns([1.2, 1.8])
        
        # --- LEFT COLUMN: ITEM SELECTION & DOSAGE ---
        with col1:
            st.subheader("1. Select & Add Item")
            
            search_query = st.text_input("🔍 Search medicine by name or category:")
            available_drugs = st.session_state.inventory[st.session_state.inventory['Stock Qty'] > 0].copy()
            
            if search_query:
                available_drugs = available_drugs[
                    available_drugs['Drug Name'].astype(str).str.contains(search_query, case=False, na=False) |
                    available_drugs['Category'].astype(str).str.contains(search_query, case=False, na=False)
                ]

            drug_options = available_drugs['Drug Name'].tolist()
            
            if not drug_options:
                st.error("No matching medicines currently in stock!")
            else:
                selected_drug = st.selectbox("Select Medicine", drug_options)
                
                drug_row = available_drugs[available_drugs['Drug Name'] == selected_drug].iloc[0]
                current_stock = int(drug_row['Stock Qty'])
                unit_price = float(drug_row['Selling Price (TZS)'])
                
                st.info(f"Price: **TSh {unit_price:,.0f}** | In Stock: **{current_stock} units**")
                
                # Dosage Calculator Block
                st.markdown("---")
                st.markdown("##### 📐 Dosage & Quantity Calculator")
                
                use_calculator = st.checkbox("Use Dosage Calculator (Auto-count Qty)", value=True)
                
                if use_calculator:
                    dose_freq = st.selectbox(
                        "Dose Frequency", 
                        [
                            "OD (Once daily - 1x/day)", 
                            "BD (Twice daily - 2x/day)", 
                            "TDS (Three times daily - 3x/day)", 
                            "QID (Four times daily - 4x/day)", 
                            "STAT (Single dose immediately)", 
                            "PRN (As needed / Custom)"
                        ]
                    )
                    
                    freq_multiplier_map = {
                        "OD (Once daily - 1x/day)": 1,
                        "BD (Twice daily - 2x/day)": 2,
                        "TDS (Three times daily - 3x/day)": 3,
                        "QID (Four times daily - 4x/day)": 4,
                        "STAT (Single dose immediately)": 1,
                        "PRN (As needed / Custom)": 1
                    }
                    multiplier = freq_multiplier_map[dose_freq]
                    
                    days = st.number_input("Duration (Number of Days)", min_value=1, max_value=30, value=3)
                    units_per_dose = st.number_input("Units per Dose (e.g., 1 or 2 tablets)", min_value=1, max_value=10, value=1)
                    
                    calculated_qty = multiplier * days * units_per_dose
                    st.caption(f"💡 Calculated Quantity: **{calculated_qty} units** ({units_per_dose} unit(s) × {multiplier} times/day × {days} days)")
                    
                    default_qty = min(calculated_qty, current_stock)
                    dosage_note = f"{dose_freq.split(' ')[0]} for {days} days"
                else:
                    default_qty = 1
                    dosage_note = st.text_input("Dosage Instructions (Optional):", value="")

                final_qty = st.number_input("Quantity to Add to Cart", min_value=1, max_value=current_stock, value=default_qty)
                
                if st.button("➕ Add Item to Cart", type="secondary"):
                    item_total = final_qty * unit_price
                    st.session_state.cart.append({
                        "Drug Name": selected_drug,
                        "Unit Price (TZS)": unit_price,
                        "Qty": final_qty,
                        "Dosage Instructions": dosage_note,
                        "Subtotal (TZS)": item_total
                    })
                    st.success(f"Added {selected_drug} (x{final_qty}) to cart!")
                    st.rerun()

        # --- RIGHT COLUMN: CART & CHECKOUT ---
        with col2:
            st.subheader("2. Customer Cart & Professional Checkout")
            
            c1, c2 = st.columns(2)
            with c1:
                seller_name = st.text_input("Cashier / Seller:", value="Staff 1")
            with c2:
                payment_method = st.selectbox("Payment Method", ["Cash", "M-Pesa", "Tigo Pesa", "Airtel Money", "Credit (Mkopo)"])
            
            c3, c4 = st.columns(2)
            with c3:
                patient_name = st.text_input("Patient Name (Optional):", value="")
            with c4:
                prescriber = st.text_input("Prescriber / Doctor (Optional):", value="")

            if not st.session_state.cart:
                st.info("🛒 The cart is empty. Select medicines on the left to build the order.")
            else:
                cart_df = pd.DataFrame(st.session_state.cart)
                
                st.dataframe(
                    cart_df[["Drug Name", "Qty", "Unit Price (TZS)", "Dosage Instructions", "Subtotal (TZS)"]], 
                    use_container_width=True
                )
                
                total_bill = cart_df["Subtotal (TZS)"].sum()
                st.markdown(f"## **Total Bill: TSh {total_bill:,.0f}**")
                
                col_clear, col_checkout = st.columns([1, 2])
                
                with col_clear:
                    if st.button("🗑️ Clear Cart"):
                        st.session_state.cart = []
                        st.rerun()

                with col_checkout:
                    if st.button("✅ Complete Sale & Checkout", type="primary"):
                        sale_id = "S-" + str(len(st.session_state.sales_df) + 1001)
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                        
                        # Process items and deduct stock
                        for item in st.session_state.cart:
                            d_name = item["Drug Name"]
                            qty_sold = item["Qty"]
                            total_p = item["Subtotal (TZS)"]
                            instructions = item["Dosage Instructions"]
                            
                            idx = st.session_state.inventory[st.session_state.inventory['Drug Name'] == d_name].index[0]
                            st.session_state.inventory.at[idx, 'Stock Qty'] -= qty_sold
                            
                            new_sale = pd.DataFrame([{
                                "Sale ID": sale_id,
                                "Date": now_str,
                                "Drug Name": d_name,
                                "Qty Sold": qty_sold,
                                "Total Price (TZS)": total_p,
                                "Seller": seller_name,
                                "Payment Method": payment_method,
                                "Patient Name": patient_name if patient_name else "Walk-in",
                                "Prescriber": prescriber if prescriber else "Self / OTC",
                                "Dosage Instructions": instructions
                            }])
                            st.session_state.sales_df = pd.concat([st.session_state.sales_df, new_sale], ignore_index=True)

                        save_data()
                        st.session_state.cart = []
                        st.success(f"Transaction {sale_id} completed via {payment_method}! Total Paid: TSh {total_bill:,.0f}")
                        st.balloons()
                        st.rerun()

# ==========================================
# 2. ADMIN DASHBOARD
# ==========================================
elif app_mode == "🔒 Admin Dashboard":
    st.title("🔒 Admin Management & Reports")
    
    admin_pin = st.text_input("Enter Admin PIN (Default PIN: 1234)", type="password")
    
    if admin_pin == "1234":
        st.success("Access Granted!")
        
        tab1, tab2, tab3 = st.tabs(["📊 Sales Reports", "📦 Inventory Control", "➕ Add New Drug"])
        
        # TAB 1: REPORTS
        with tab1:
            st.subheader("Financial & Payment Breakdown")
            
            if st.session_state.sales_df.empty:
                st.info("No sales recorded yet.")
            else:
                total_revenue = st.session_state.sales_df['Total Price (TZS)'].sum()
                total_items_sold = st.session_state.sales_df['Qty Sold'].sum()
                total_transactions = st.session_state.sales_df['Sale ID'].nunique()
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Revenue", f"TSh {total_revenue:,.0f}")
                m2.metric("Items Sold", total_items_sold)
                m3.metric("Total Bills", total_transactions)
                
                st.markdown("### Revenue by Payment Method")
                if 'Payment Method' in st.session_state.sales_df.columns:
                    payment_summary = st.session_state.sales_df.groupby('Payment Method')['Total Price (TZS)'].sum().reset_index()
                    st.dataframe(payment_summary, use_container_width=True)
                
                st.markdown("### Detailed Transaction Log")
                st.dataframe(st.session_state.sales_df, use_container_width=True)
                
                st.download_button("📥 Download Sales Report (CSV)", st.session_state.sales_df.to_csv(index=False), "sales_report.csv", "text/csv")

        # TAB 2: INVENTORY CONTROL
        with tab2:
            st.subheader("Manage Current Stock & Expiry Dates")
            if st.session_state.inventory.empty:
                st.info("Inventory is empty.")
            else:
                st.dataframe(st.session_state.inventory, use_container_width=True)
                st.download_button("📥 Download Inventory List (CSV)", st.session_state.inventory.to_csv(index=False), "inventory_stock.csv", "text/csv")

        # TAB 3: ADD NEW DRUG
        with tab3:
            st.subheader("Add New Medicine to Inventory")
            
            with st.form("add_drug_form", clear_on_submit=True):
                d_name = st.text_input("Drug Name (e.g., Amoxicillin 500mg)")
                d_category = st.selectbox("Category", ["Painkillers", "Antibiotics", "Antimalarials", "Supplements", "First Aid", "Syrups", "Other"])
                d_cost = st.number_input("Buying / Cost Price per Unit (TZS)", min_value=0.0, step=100.0)
                d_selling = st.number_input("Selling Price per Unit (TZS)", min_value=0.0, step=100.0)
                d_qty = st.number_input("Initial Stock Quantity", min_value=0, step=1)
                d_expiry = st.date_input("Expiry Date")
                
                submitted = st.form_submit_button("Save Medicine")
                
                if submitted:
                    if d_name.strip() != "":
                        d_id = "DRG-" + str(len(st.session_state.inventory) + 101)
                        new_drug = pd.DataFrame([{
                            "ID": d_id,
                            "Drug Name": d_name.strip(),
                            "Category": d_category,
                            "Cost Price (TZS)": d_cost,
                            "Selling Price (TZS)": d_selling,
                            "Stock Qty": d_qty,
                            "Expiry Date": str(d_expiry)
                        }])
                        
                        st.session_state.inventory = pd.concat([st.session_state.inventory, new_drug], ignore_index=True)
                        save_data()
                        st.success(f"✅ Successfully added '{d_name}' to inventory!")
                        st.rerun()
                    else:
                        st.error("Please enter a valid Drug Name before saving.")
    elif admin_pin != "":
        st.error("Incorrect PIN. Default PIN is 1234.")
