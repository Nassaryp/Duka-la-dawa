import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Duka la Dawa System", page_icon="💊", layout="wide")

# --- INITIALIZE DATABASE IN SESSION STATE ---
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
            "Total Price (TZS)", "Seller"
        ])

# Helper function to save to CSV
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
    st.markdown("Search for medicines, check stock, and record customer purchases.")

    if st.session_state.inventory.empty:
        st.warning("No medicines in inventory yet. Please ask the Admin to add stock first.")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Available Medicines")
            search_query = st.text_input("🔍 Search drug by name or category:")
            
            filtered_inv = st.session_state.inventory.copy()
            if search_query:
                filtered_inv = filtered_inv[
                    filtered_inv['Drug Name'].astype(str).str.contains(search_query, case=False, na=False) |
                    filtered_inv['Category'].astype(str).str.contains(search_query, case=False, na=False)
                ]
            
            st.dataframe(filtered_inv[['ID', 'Drug Name', 'Category', 'Selling Price (TZS)', 'Stock Qty', 'Expiry Date']], use_container_width=True)

        with col2:
            st.subheader("New Sale Checkout")
            seller_name = st.text_input("Seller Name / Cashier:", value="Staff 1")
            
            # Select Drug
            available_drugs = st.session_state.inventory[st.session_state.inventory['Stock Qty'] > 0]
            drug_options = available_drugs['Drug Name'].tolist()
            
            if not drug_options:
                st.error("All items are currently out of stock!")
            else:
                selected_drug = st.selectbox("Select Medicine", drug_options)
                
                # Get drug details
                drug_row = available_drugs[available_drugs['Drug Name'] == selected_drug].iloc[0]
                max_stock = int(drug_row['Stock Qty'])
                unit_price = float(drug_row['Selling Price (TZS)'])
                
                st.info(f"Price: **TSh {unit_price:,.0f}** | In Stock: **{max_stock} units**")
                
                qty_to_sell = st.number_input("Quantity to Sell", min_value=1, max_value=max_stock, value=1)
                total_amount = qty_to_sell * unit_price
                
                st.markdown(f"### Total: TSh {total_amount:,.0f}")
                
                if st.button("Complete Sale & Print Receipt", type="primary"):
                    # Update Inventory Stock
                    idx = st.session_state.inventory[st.session_state.inventory['Drug Name'] == selected_drug].index[0]
                    st.session_state.inventory.at[idx, 'Stock Qty'] -= qty_to_sell
                    
                    # Record Sale
                    new_sale = pd.DataFrame([{
                        "Sale ID": "S-" + str(len(st.session_state.sales_df) + 1001),
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Drug Name": selected_drug,
                        "Qty Sold": qty_to_sell,
                        "Total Price (TZS)": total_amount,
                        "Seller": seller_name
                    }])
                    
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, new_sale], ignore_index=True)
                    save_data()
                    
                    st.success(f"Sale completed successfully! Total: TSh {total_amount:,.0f}")
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
            st.subheader("Financial & Sales Performance")
            
            if st.session_state.sales_df.empty:
                st.info("No sales recorded yet.")
            else:
                total_revenue = st.session_state.sales_df['Total Price (TZS)'].sum()
                total_items_sold = st.session_state.sales_df['Qty Sold'].sum()
                total_transactions = len(st.session_state.sales_df)
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Revenue", f"TSh {total_revenue:,.0f}")
                m2.metric("Items Sold", total_items_sold)
                m3.metric("Total Transactions", total_transactions)
                
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
                d_name = st.text_input("Drug Name (e.g., Paracetamol 500mg)")
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
