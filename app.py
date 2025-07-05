import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd
import json

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
service_account_info = json.loads(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
client = gspread.authorize(creds)

# --- Google Sheets ---
sheet = client.open("Fabric Inventory System")
fabric_master = sheet.worksheet("Fabric_Master")
inward_sheet = sheet.worksheet("Inward")
outward_sheet = sheet.worksheet("Outward")
fabrics = [cell for cell in fabric_master.col_values(1) if cell.lower() != "fabric name"]

# --- UI ---
st.set_page_config(page_title="Fabric Inventory", layout="centered")
st.title("🧵 Fabric Inventory System")

tab1, tab2, tab3 = st.tabs(["➕ Add Inward", "➖ Add Outward", "📊 View Stock"])

# --- Inward ---
with tab1:
    st.subheader("📥 Add Inward Entry")
    fabric = st.selectbox("Select Fabric", fabrics)
    qty = st.number_input("Quantity (in rolls)", min_value=1, step=1)
    party = st.text_input("Party Name")

    if st.button("Add Inward"):
        if fabric and qty and party:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            date = datetime.now().strftime("%Y-%m-%d")
            inward_sheet.append_row([timestamp, date, fabric, qty, party])
            st.success(f"Inward entry added: {qty} rolls of {fabric} from {party}")
        else:
            st.error("Please fill all fields")

# --- Outward ---
with tab2:
    st.subheader("📤 Add Outward Entry")

    fabric = st.selectbox("Select Fabric", fabrics, key="out_fabric")
    challan = st.text_input("Challan No.")
    qty = st.number_input("Quantity (in rolls)", min_value=1, step=1, key="out_qty")

    # Check current stock for this fabric
    inward_qty = sum(int(row["Qty"]) for row in inward_data if row["Fabric"] == fabric)
    outward_qty = sum(int(row["Qty"]) for row in outward_data if row["Fabric"] == fabric)
    current_stock = inward_qty - outward_qty

    st.markdown(f"🧮 Current Stock: **{current_stock}** rolls")

    if st.button("Add Outward"):
        if not challan:
            st.error("❌ Please enter a challan number.")
        elif qty > current_stock:
            st.error(f"❌ Not enough stock! You have only {current_stock} rolls of {fabric}.")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            date = datetime.now().strftime("%Y-%m-%d")
            outward_sheet.append_row([timestamp, date, fabric, qty, challan])
            st.success(f"✅ Outward entry added: {qty} rolls of {fabric}, Challan No: {challan}")


# --- Stock ---
with tab3:
    st.subheader("📦 Current Stock Summary")

    inward_data = inward_sheet.get_all_records()
    outward_data = outward_sheet.get_all_records()
    stock_summary = {fabric: 0 for fabric in fabrics}

    for row in inward_data:
        if row["Fabric"] in stock_summary:
            stock_summary[row["Fabric"]] += int(row["Qty"])

    for row in outward_data:
        if row["Fabric"] in stock_summary:
            stock_summary[row["Fabric"]] -= int(row["Qty"])

    df = pd.DataFrame([{"Fabric": k, "Current Stock": v} for k, v in stock_summary.items()])
    st.dataframe(df, use_container_width=True)
