import ssl
import urllib.parse
import urllib.request
import pandas as pd
import streamlit as st
import products
import config

# 🎨 PAGE CONFIGURATION
st.set_page_config(
    page_title="Moon & Melody Hub",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Bypass local machine security validation blocks
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass


# --- 1. CORE FUNCTIONS ---

def load_data():
    """Reads live private sales data directly from the universal CSV export stream."""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{config.SHEET_ID}/export?format=csv&gid=0"
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

        # Format Columns
        if "Order ID" in df.columns:
            df["Order ID"] = pd.to_numeric(df["Order ID"], errors="coerce").fillna(0).astype(int).astype(str).str.zfill(4)
        else:
            df["Order ID"] = df.index.astype(str).str.zfill(4)

        if "Cost" in df.columns:
            df["Cost"] = pd.to_numeric(df["Cost"], errors="coerce").fillna(0.0)
        else:
            df["Cost"] = 0.0

        if "Status" in df.columns:
            df["Status"] = df["Status"].fillna("pending").astype(str).str.strip().str.lower()
        else:
            df["Status"] = "pending"

        return df
    except Exception as e:
        st.error(f"Google Cloud Sync Error: {e}")
        return pd.DataFrame()


# --- 2. CONFIRMATION POP-UP LOGIC ---
@st.dialog("⚠️ Confirm Order Details")
def show_confirmation_dialog(order_id, customer, contact, cart_items, total_cost):
    st.write(f"**Order ID:** #{order_id}")
    st.write(f"**Customer:** {customer}")
    st.write(f"**Contact:** {contact}")
    st.divider()
    st.write("**Items in Basket:**")
    for item, qty in cart_items.items():
        st.write(f"- {qty}x {item}")
    
    st.divider()
    st.markdown(f"### Total: ₹{total_cost:,.2f}")
    
    st.warning("Are you sure you want to save this to Google Sheets?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun() # Closes the modal without doing anything
            
    with col2:
        if st.button("✅ Yes, Write Data", type="primary", use_container_width=True):
            # --- EXECUTE SAVE LOGIC ---
            items_str_list = [f"{qty}x {name}" for name, qty in cart_items.items()]
            compiled_items = ", ".join(items_str_list)
            local_ts = pd.Timestamp.now(tz="Asia/Kolkata")
            
            payload = {
                "sheet_id": config.SHEET_ID,
                "order_id": order_id,
                "date": local_ts.strftime("%Y-%m-%d"),
                "time": local_ts.strftime("%H:%M:%S"),
                "name": customer,
                "contact": contact,
                "items": compiled_items,
                "cost": str(total_cost),
                "status": "Pending",
            }
            
            try:
                qs = urllib.parse.urlencode(payload)
                req = urllib.request.Request(f"{config.MACRO_URL}?{qs}", headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req) as response:
                    pass
                
                # CLEAR FORM
                st.session_state.form_customer = ""
                st.session_state.form_contact = ""
                for p in products.CATALOG:
                    st.session_state[f"qty_{p}"] = 0
                
                st.session_state.success_msg = f"Order #{order_id} Saved Successfully!"
                st.rerun()
                
            except Exception as e:
                st.error(f"Sync Failed: {e}")


# --- 3. MAIN APP LOGIC ---

df = load_data()

# Calc Next ID
if not df.empty and "Order ID" in df.columns:
    try:
        highest_id = pd.to_numeric(df["Order ID"], errors="coerce").max()
        if pd.isna(highest_id): next_num = 1
        else: next_num = int(highest_id) + 1
    except: next_num = len(df)
else:
    next_num = 1
next_order_id = str(next_num).zfill(4)


# --- SIDEBAR UI ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3222/3222642.png", width=50)
    st.title("Log New Order")
    
    # Success Message Handler
    if "success_msg" in st.session_state and st.session_state.success_msg:
        st.success(st.session_state.success_msg)
        st.session_state.success_msg = "" # Clear after showing

    st.markdown(f"Next ID: **#{next_order_id}**")
    st.divider()

    # Inputs
    if "form_customer" not in st.session_state: st.session_state["form_customer"] = ""
    if "form_contact" not in st.session_state: st.session_state["form_contact"] = ""

    customer = st.text_input("👤 Customer Name", key="form_customer")
    contact = st.text_input("📞 Contact (Phone)", key="form_contact")

    st.markdown("### 🛍️ Basket")
    
    cart_items = {}
    running_total = 0.0
    
    for item_name, price in products.CATALOG.items():
        widget_key = f"qty_{item_name}"
        if widget_key not in st.session_state: st.session_state[widget_key] = 0
        
        qty = st.number_input(f"{item_name} (₹{price:.0f})", min_value=0, max_value=50, step=1, key=widget_key)
        if qty > 0:
            cart_items[item_name] = qty
            running_total += (qty * price)

    st.divider()
    st.markdown(f"**Total: ₹{running_total:,.2f}**")
    
    # REVIEW BUTTON (Triggers the Dialog)
    if st.button("🚀 Review & Submit", use_container_width=True):
        if customer.strip() == "":
            st.error("⚠️ Customer Name is required!")
        elif not cart_items:
            st.error("⚠️ Basket is empty!")
        else:
            # Open the confirmation pop-up
            show_confirmation_dialog(next_order_id, customer, contact, cart_items, running_total)


# --- MAIN DASHBOARD ---
st.title("🌙 Moon & Melody Hub")

if not df.empty:
    pending_count = len(df[df["Status"] == "pending"])
    completed_df = df[df["Status"] == "completed"]
    total_rev = completed_df["Cost"].sum() if not completed_df.empty else 0.0
else:
    pending_count = 0
    total_rev = 0.0

m1, m2, m3 = st.columns(3)
m1.metric("Pending Orders", f"{pending_count}", delta_color="inverse")
m2.metric("Total Revenue", f"₹{total_rev:,.0f}")
m3.metric("Completed Orders", f"{len(df[df['Status']=='completed'])}")

st.divider()

tab_queue, tab_charts = st.tabs(["📌 Work Queue", "📊 Analytics & History"])

with tab_queue:
    if not df.empty and "Status" in df.columns:
        pending_orders = df[df["Status"] == "pending"]
        
        if pending_orders.empty:
            st.success("✨ No pending orders! You are all caught up.")
            st.balloons()
        else:
            cols = st.columns(3)
            for idx, (_, row) in enumerate(pending_orders.iterrows()):
                col_idx = idx % 3
                with cols[col_idx]:
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        c1.markdown(f"**#{row.get('Order ID')}**")
                        c2.markdown("🟠")
                        
                        st.markdown(f"### {row.get('Customer Name', 'Unknown')}")
                        st.caption(f"📞 {row.get('Customer Contact', '-')}")
                        st.markdown("---")
                        
                        items_text = row.get('Items', '').replace(",", "\n- ")
                        st.markdown(f"**Items:**\n- {items_text}")
                        st.markdown(f"### ₹{row.get('Cost', 0.0):,.0f}")
                        
                        btn_key = f"done_{row.get('Order ID')}_{idx}"
                        if st.button("✅ Mark Done", key=btn_key, use_container_width=True):
                            upd_load = {
                                "action": "update_status",
                                "sheet_id": config.SHEET_ID,
                                "order_id": row.get("Order ID")
                            }
                            try:
                                u_qs = urllib.parse.urlencode(upd_load)
                                u_req = urllib.request.Request(f"{config.MACRO_URL}?{u_qs}", headers={"User-Agent": "Mozilla/5.0"})
                                with urllib.request.urlopen(u_req):
                                    pass
                                st.toast(f"Order #{row.get('Order ID')} Completed!", icon="✅")
                                st.rerun()
                            except Exception as e:
                                st.error("Update failed")

with tab_charts:
    if not df.empty and "Status" in df.columns:
        completed = df[df["Status"] == "completed"]
        if not completed.empty:
            st.subheader("Daily Revenue Trend")
            daily = completed.groupby("Date")["Cost"].sum().reset_index()
            st.bar_chart(daily, x="Date", y="Cost", color="#90EE90")
            
            st.subheader("Order History")
            st.dataframe(
                completed[["Date", "Order ID", "Customer Name", "Items", "Cost"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Complete some orders to see your analytics!")

