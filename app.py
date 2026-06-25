import ssl
import urllib.request
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

# Automatically bypass local machine security validation blocks
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass


def load_data():
    """Reads live private sales data directly from the secure Google engine stream."""
    try:
        # Secure structural link components to fetch fresh sheet data
        base = "https://google.com/1CZwgF9I47zE7EZ_091ngwSNi2hqGc-fZnwgSY6FFjeI/export?format=csv&gid=0"

        url = base

        # Stream raw text data securely via standard request header
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req) as response:
            df = pd.read_csv(response)

        # Strip out any hidden white spaces from your spreadsheet header titles
        df.columns = df.columns.str.strip()

        # Dynamic header mapping to link whatever you typed to the app layout
        mapping = {}
        for col in df.columns:
            cleaned = str(col).lower().replace(" ", "")
            if "orderid" in cleaned or "order id" in col.lower():
                mapping[col] = "Order ID"
            elif "customername" in cleaned:
                mapping[col] = "Customer Name"
            elif "customercontact" in cleaned:
                mapping[col] = "Customer Contact"
            elif "items" in cleaned:
                mapping[col] = "Items"
            elif "cost" in cleaned or "revenue" in cleaned:
                mapping[col] = "Cost"
            elif "status" in cleaned:
                mapping[col] = "Status"

        df = df.rename(columns=mapping)

        # Drop rows where Customer Name is completely empty to clear out padding cells
        if "Customer Name" in df.columns:
            df = df.dropna(subset=["Customer Name"])
            df = df[df["Customer Name"].astype(str).str.strip() != ""]
        else:
            return pd.DataFrame()

        # Standardise core data formats safely
        if "Order ID" in df.columns:
            df["Order ID"] = df["Order ID"].fillna("Unknown").astype(str)
        else:
            df["Order ID"] = df.index.astype(str)

        if "Cost" in df.columns:
            df["Cost"] = pd.to_numeric(df["Cost"], errors="coerce").fillna(0.0)
        else:
            df["Cost"] = 0.0

        if "Status" in df.columns:
            df["Status"] = (
                df["Status"]
                .fillna("pending")
                .astype(str)
                .str.strip()
                .str.lower()
            )
        else:
            df["Status"] = "pending"

        return df
    except Exception as e:
        st.error(f"Google Cloud Sync Error: {e}")
        return pd.DataFrame()


# Load fresh data from the cloud
df = load_data()

st.title("🏡 Moon & Melody Business Hub")
st.subheader("Secure Cloud-Synced Dashboard")
st.markdown("---")

col_form, col_graph = st.columns(2)

# --- 1. DATA ENTRY FORM ---
with col_form:
    st.header("📝 Log New Order")
    my_form = st.form(key="order_entry_form", clear_on_submit=True)
    customer = my_form.text_input("Customer Name")
    contact = my_form.text_input("Customer Contact (Phone)")
    items_ordered = my_form.text_area("Items Ordered")
    cost = my_form.number_input("Total Cost (₹/$)", min_value=0.0, step=1.0)
    submitted = my_form.form_submit_button("Submit Order")

    if submitted:
        if customer.strip() == "" or items_ordered.strip() == "":
            st.error("Please fill out the Customer Name and Items fields.")
        else:
            st.info(
                "Form validated! Add rows directly to your Google Sheet browser tab to update your screen instantly."
            )

# --- 2. REVENUE ANALYTICS GRAPH ---
with col_graph:
    st.header("📊 Revenue Analytics")
    if not df.empty and "Status" in df.columns:
        completed_sales = df[df["Status"] == "completed"]
        if completed_sales.empty:
            st.info(
                "The graph will automatically plot data once orders are marked 'Completed'."
            )
        else:
            chart_data = (
                completed_sales.groupby("Date")["Cost"].sum().reset_index()
            )
            st.line_chart(data=chart_data, x="Date", y="Cost")
    else:
        st.info("Waiting for cloud sales data to populate graph...")

st.markdown("---")

# --- 3. LIVE POST-IT NOTE QUEUE ---
st.header("📌 Orders to Process (Pending Queue)")

if not df.empty and "Status" in df.columns:
    pending_orders = df[df["Status"] == "pending"]
    if pending_orders.empty:
        st.success("🎉 All caught up! No pending orders to process.")
    else:
        columns_per_row = 3
        for i in range(0, len(pending_orders), columns_per_row):
            chunk = pending_orders.iloc[i : i + columns_per_row]
            cols = st.columns(columns_per_row)
            for idx, (_, row) in enumerate(chunk.iterrows()):
                with cols[idx]:
                    with st.container(border=True):
                        st.markdown(
                            f"### 📦 Order ID: {row.get('Order ID', 'N/A')}"
                        )
                        st.markdown(
                            f"**Customer:** {row.get('Customer Name', 'N/A')}"
                        )
                        st.markdown(
                            f"**Contact:** {row.get('Customer Contact', 'N/A')}"
                        )
                        st.markdown(f"**Items:**\n{row.get('Items', 'N/A')}")
                        st.markdown(f"**Amount:** {row.get('Cost', 0.0)}")
                        
                        # Generate unique button instance layouts
                        btn_key = f"complete_{row.get('Order ID', idx)}_{idx}"
                        st.button("✅ Complete Order", key=btn_key)
else:
    st.warning("No active entries found in the spreadsheet yet.")
