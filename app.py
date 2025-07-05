# app.py

import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
import json
from io import StringIO

service_account_info = json.loads(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)

client = gspread.authorize(creds)

# Connect to Google Sheet
sheet = client.open("Fabric Inventory System")
fabric_master = sheet.worksheet("Fabric_Master")
inward_sheet = sheet.worksheet("Inward")
outward_sheet = sheet.worksheet("Outward")

# Get fabric list
fabrics = [cell for cell in fabric_master.col_values(1) if cell.lower() != "fabric name"]

# --- Streamlit UI ---
st.set_page_config(page_title="Fabric Inventory", layout="centered")
st.title("🧵 Fabric Inventory System")

menu = st.sidebar.radio("Select Action", ["📥 Add Inward Entry", "📤 Add Outward Entry", "📊 View Current Stock"])

def add_inward():
    st.header("📥 Add Inward Entry")
    fabric = st.selectbox("Select Fabric", fabrics)
    qty = st.number_input("Quantity (rolls)", min_value=1, step=1)
    party = st.text_input("Party Name")
    if st.button("Submit Inward Entry"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date = datetime.now().strftime("%Y-%m-%d")
        inward_sheet.append_row([timestamp, date, fabric, qty, party])
        st.success(f"Inward entry added for {fabric} ({qty} rolls) from {party}")

def add_outward():
    st.header("📤 Add Outward Entry")
    fabric = st.selectbox("Select Fabric", fabrics)
    qty = st.number_input("Quantity (rolls)", min_value=1, step=1)
    challan = st.text_input("Challan Number")
    if st.button("Submit Outward Entry"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date = datetime.now().strftime("%Y-%m-%d")
        outward_sheet.append_row([timestamp, date, fabric, qty, challan])
        st.success(f"Outward entry added for {fabric} ({qty} rolls), Challan No: {challan}")

def view_stock():
    st.header("📊 Current Fabric Stock")
    inward_data = inward_sheet.get_all_records()
    outward_data = outward_sheet.get_all_records()
    stock_summary = {fabric: 0 for fabric in fabrics}

    for row in inward_data:
        if row['Fabric'] in stock_summary:
            stock_summary[row['Fabric']] += int(row['Qty'])
    for row in outward_data:
        if row['Fabric'] in stock_summary:
            stock_summary[row['Fabric']] -= int(row['Qty'])

    df = pd.DataFrame([{'Fabric': k, 'Current Stock': v} for k, v in stock_summary.items()])
    st.table(df)

if menu == "📥 Add Inward Entry":
    add_inward()
elif menu == "📤 Add Outward Entry":
    add_outward()
elif menu == "📊 View Current Stock":
    view_stock()
