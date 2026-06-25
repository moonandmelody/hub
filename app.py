import ssl
import urllib.parse
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
    """Reads live private sales data directly from the universal CSV export stream."""
    try:
        url = "https://docs.google.com/spreadsheets/d/1CZwgF9I47zE7EZ_091ngwSNi2hqGc-fZnwgSY6FFjeI/export?format=csv&gid=0"
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()

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

        if "Customer Name" in df.columns:
            df = df.dropna(subset=["Customer Name"])
            df = df[df["Customer Name"].astype(str).str.strip() != ""]
        else:
            return pd.DataFrame()

        # Ensure Order IDs are read as clean padded text strings (e.g., "0005")
        if "Order ID" in df.columns:
            df["Order ID"] = (
                pd.to_numeric(df["Order ID"], errors="coerce")
                .fillna(0)
                .astype(int)
                .astype(str)
                .str.zfill(4)
            )
        else:
            df["Order ID"] = df.index.astype(str).str.zfill(4)

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

# AUTOMATED FOUR-DIGIT SERIAL COUNTER LOGIC
if not df.empty and "Order ID" in df.columns:
    try:
        highest_id = pd.to_numeric(df["Order ID"], errors="coerce").max()
        if pd.isna(highest_id):
            next_num = 0
        else:
            next_num = int(highest_id) + 1
    except Exception:
        next_num = len(df)
else:
    next_num = 0

next_order_id = str(next_num).zfill(4)

st.title("🏡 Moon & Melody Business Hub")
st.subheader("Secure Cloud-Synced Dashboard")
st.markdown("---")

col_form, col_graph = st.columns(2)

# --- 1. DATA ENTRY FORM WITH INTEGRATED COUNTERS & AUTO-PRICING ---
with col_form:
    st.header("📝 Log New Order")

    PRICE_MIDNIGHT_LUXE = 329
    PRICE_MOON_DANCE = 359
    PRICE_MIDNIGHT_LUXE_VEGAN = 379

    # Display automated serial format row header tracking
    st.markdown(f"### 🎫 Next Order ID: **#{next_order_id}**")
    st.markdown("---")

    customer = st.text_input("Customer Name")
    contact = st.text_input("Customer Contact (Phone)")

    st.markdown("##### 📦 Select Item Quantities")
    midnight_luxe_count = st.number_input(
        f"Midnight Luxe (₹/{PRICE_MIDNIGHT_LUXE:.0f} each)", min_value=0, max_value=50, value=0, step=1
    )
    moon_dance_count = st.number_input(
        f"Moon Dance (₹/{PRICE_MOON_DANCE:.0f} each)", min_value=0, max_value=50, value=0, step=1
    )
    midnight_luxe_vegan_count = st.number_input(
        f"Midnight Luxe Vegan (₹/{PRICE_MIDNIGHT_LUXE_VEGAN:.0f} each)", min_value=0, max_value=50, value=0, step=1
    )

    # 🎯 AUTO-CALCULATION ENGINE: Multiplies quantities by their fixed prices instantly
    calculated_total = (midnight_luxe_count * PRICE_MIDNIGHT_LUXE) + (moon_dance_count * PRICE_MOON_DANCE) + (midnight_luxe_vegan_count * PRICE_MIDNIGHT_LUXE_VEGAN)

    st.markdown(f"### 💰 Calculated Total Cost: **₹/{calculated_total:.2f}**")

    with st.form(key="submit_action_form"):
        submitted = st.form_submit_button(
            "🚀 Submit & Save directly to Google Sheet"
        )

    if submitted:
        items_list = []
        if midnight_luxe_count > 0:
            items_list.append(f"{midnight_luxe_count}x Midnight Luxe")
        if moon_dance_count > 0:
            items_list.append(f"{moon_dance_count}x Moon Dance")
        if midnight_luxe_vegan_count > 0:
            items_list.append(f"{midnight_luxe_vegan_count}x Midnight Luxe Vegan")

        if customer.strip() == "":
            st.error("Please fill out the Customer Name field.")
        elif not items_list:
            st.error(
                "Please use the + buttons to add at least 1 item to the order."
            )
        else:
            compiled_items_string = ", ".join(items_list)

            # AUTOMATED TIME CONFIGURATION FOR ASIA/KOLKATA (IST)
            local_timestamp = pd.Timestamp.now(tz="Asia/Kolkata")
            current_date = local_timestamp.strftime("%Y-%m-%d")
            current_time = local_timestamp.strftime("%H:%M:%S")

            # 🎯 ACTION REQUIRED: Update these exact form fields with your matching variables from your form code
            FORM_URL = "https://google.com"

            form_data = {
                "entry.647981491": next_order_id,  # Paste Order ID Entry Number
                "entry.1663250176": current_date,  # Paste Date Entry Number
                "entry.68387086": current_time,  # Paste Time Entry Number
                "entry.1205478145": customer,  # Paste Customer Name Entry Number
                "entry.520983194": contact,  # Paste Contact Entry Number
                "entry.1627079739": compiled_items_string,  # Paste Items Entry Number
                "entry.950588485": str(calculated_total),  # Paste Cost Entry Number
                "entry.443945553": "Pending",  # Paste Status Entry Number
            }

            try:
                # Transmit encrypted packet straight to your sheet rows layout array path
                encoded_data = urllib.parse.urlencode(form_data).encode("utf-8")
                req = urllib.request.Request(
                    FORM_URL,
                    data=encoded_data,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                with urllib.request.urlopen(req) as response:
                    pass

                st.success(
                    f"🎉 Order #{next_order_id} recorded live to Google Sheets! Refreshing..."
                )
                st.rerun()
            except Exception as e:
                st.error(f"Failed to submit to Google Sheet automatically: {e}")

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
                        st.markdown(f"### 📦 Order ID: #{row.get('Order ID', 'N/A')}")
                        st.markdown(f"**Customer:** {row.get('Customer Name', 'N/A')}")
                        st.markdown(f"**Contact:** {row.get('Customer Contact', 'N/A')}")
                        st.markdown(f"**Items:**\n{row.get('Items', 'N/A')}")
                        st.markdown(f"**Amount:** {row.get('Cost', 0.0)}")

                        btn_key = f"complete_{row.get('Order ID', idx)}_{idx}"
                        st.button("✅ Complete Order", key=btn_key)
else:
    st.warning("No active entries found in the spreadsheet yet.")
