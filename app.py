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

# --- Google Sheet References ---
sheet = client.open("Fabric Inventory System")
fabric_master = sheet.worksheet("Fabric_Master")
inward_sheet = sheet.worksheet("Inward")
outward_sheet = sheet.worksheet("Outward")

fabrics = [cell for cell in fabric_master.col_values(1) if cell.lower() != "fabric name"]

# ✅ Load inventory data once to reuse
inward_data = inward_sheet.get_all_records()
outward_data = outward_sheet.get_all_records()

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Fabric Inventory", layout="centered")
st.title("🧵 Fabric Inventory System")

tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Inward", "➖ Add Outward", "📊 View Stock", "📝 Edit Entry"])


# --- ➕ Inward Entry Tab ---
with tab1:
    st.subheader("📥 Add Inward Entry")

    fabric = st.selectbox("Select Fabric", fabrics)
    qty = st.number_input("Quantity (in rolls)", min_value=1, step=1, format="%d")
    party = st.text_input("Party Name")

    if st.button("Add Inward"):
        if fabric and qty and party:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            date = datetime.now().strftime("%Y-%m-%d")
            inward_sheet.append_row([timestamp, date, fabric, qty, party])
            st.success(f"✅ Inward entry added: {qty} rolls of {fabric} from {party}")
        else:
            st.error("❌ Please fill in all fields.")

# --- ➖ Outward Entry Tab ---
with tab2:
    st.subheader("📤 Add Outward Entry")

    fabric_out = st.selectbox("Select Fabric", fabrics, key="out_fabric")
    challan = st.text_input("Challan No.")
    qty_out = st.number_input("Quantity (in rolls)", min_value=1, step=1, format="%d", key="out_qty")

    # Calculate current stock
    inward_qty = sum(int(row["Qty"]) for row in inward_data if row["Fabric"] == fabric_out)
    outward_qty = sum(int(row["Qty"]) for row in outward_data if row["Fabric"] == fabric_out)
    current_stock = inward_qty - outward_qty

    st.markdown(f"📦 **Current Stock** for _{fabric_out}_: `{current_stock}` rolls")

    if st.button("Add Outward"):
        if not challan:
            st.error("❌ Please enter a challan number.")
        elif qty_out > current_stock:
            st.error(f"❌ Not enough stock! You only have {current_stock} rolls of {fabric_out}.")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            date = datetime.now().strftime("%Y-%m-%d")
            outward_sheet.append_row([timestamp, date, fabric_out, qty_out, challan])
            st.success(f"✅ Outward entry added: {qty_out} rolls of {fabric_out}, Challan No: {challan}")

# --- 📊 Stock Summary Tab ---
with tab3:
    st.subheader("📦 Current Stock Summary")

    stock_summary = {fabric: 0 for fabric in fabrics}

    for row in inward_data:
        if row["Fabric"] in stock_summary:
            stock_summary[row["Fabric"]] += int(row["Qty"])

    for row in outward_data:
        if row["Fabric"] in stock_summary:
            stock_summary[row["Fabric"]] -= int(row["Qty"])

    df = pd.DataFrame([{"Fabric": k, "Current Stock": v} for k, v in stock_summary.items()])
    st.dataframe(df, use_container_width=True)

with tab4:
    st.subheader("📝 Edit Entry")

    entry_type = st.radio("Select Entry Type", ["Inward", "Outward"], key="edit_type")
    target_sheet = inward_sheet if entry_type == "Inward" else outward_sheet
    data = inward_data if entry_type == "Inward" else outward_data

    if len(data) == 0:
        st.warning("No entries available to edit.")
    else:
        df = pd.DataFrame(data)
        df_display = df.tail(5).reset_index(drop=True)

        display_options = [
            f"{entry_type} | {row['Fabric']} | {row['Qty']} rolls"
            for _, row in df_display.iterrows()
        ]
        selected_row = st.selectbox("Select an entry to edit", options=range(len(display_options)),
                                    format_func=lambda x: display_options[x],
                                    key="entry_selector")

        row_to_edit = df_display.iloc[selected_row]
        row_number = len(data) - 5 + selected_row + 2

        st.write("Original Entry:")
        st.write(row_to_edit)

        fabric_edit = st.selectbox("Fabric", fabrics,
                                   index=fabrics.index(row_to_edit["Fabric"]),
                                   key="edit_fabric")
        qty_edit = st.number_input("Quantity", min_value=1, step=1,
                                   value=int(row_to_edit["Qty"]),
                                   key="edit_qty")

        if entry_type == "Inward":
            party_value = row_to_edit.get("Party", "")
            party_edit = st.text_input("Party Name", value=party_value, key="edit_party")
        else:
            challan_value = str(row_to_edit.get("Challan No.", ""))
            challan_edit = st.text_input("Challan No.", value=challan_value, key="edit_challan")

        if st.button("Update Entry", key="update_button"):
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                date = datetime.now().strftime("%Y-%m-%d")
                new_row = [timestamp, date, fabric_edit, qty_edit, party_edit if entry_type == "Inward" else challan_edit]
                target_sheet.update(f"A{row_number}:E{row_number}", [new_row])
                st.success("✅ Entry updated successfully!")
            except Exception as e:
                st.error(f"❌ Failed to update: {e}")
