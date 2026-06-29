import ssl
import urllib.parse
import urllib.request
import pandas as pd
import streamlit as st
import products
import config
import styles  # <--- NEW: Imports your beautiful design file

# 🎨 PAGE CONFIGURATION
st.set_page_config(
    page_title="Moon & Melody Hub",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 APPLY THEME
styles.apply_custom_css()  # <--- NEW: Injects your brand colors and fonts

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
            elif "specialnotes/instructions" in cleaned:
                mapping[col] = "Special Notes/Instructions"
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


# --- 2. LOGIC: EDIT & DELETE ---
def trigger_edit_mode(row):
    """Parses the order data and fills the sidebar session state"""
    st.session_state.editing_mode = True
    st.session_state.editing_id = row.get('Order ID', '')
    
    # 1. Fill Text Inputs
    st.session_state.form_customer = row.get('Customer Name','')
    
    raw_contact = row.get('Customer Contact', '')
    if pd.isna(raw_contact) or raw_contact == "nan":
        st.session_state.form_contact = ""
    else:
        # Convert to string and remove ".0" if Google made it a float
        st.session_state.form_contact = str(raw_contact).replace(".0", "")
    
    st.session_state.form_notes = row.get('Special Notes/Instructions', '')
    
    # 2. Reset All Counters First
    for category, items_dict in products.CATALOG.items():
        if isinstance(items_dict, dict):
            for item_name in items_dict:
                st.session_state[f"qty_{item_name}"] = 0 
    
    # 3. Parse Items String (e.g. "2x Moon Dance\n1x Potato Pops")
    raw_items = str(row.get('Items', ''))
    print(f"🔍 DEBUG - raw_items: {raw_items}",flush=True)
    # Handle both newlines (new format) and commas (old format)
    if "\n" in raw_items:
        lines = raw_items.split('\n')
    else:
        lines = raw_items.split(',')

    for line in lines:
        print(f"🔍 DEBUG - lines list: {line}",flush=True)
        line = line.strip()
        if not line: continue
        
        # Expecting format "2x Item Name"
        parts = line.split('x ')
        if len(parts) >= 2:
            try:
                qty = int(parts[0].strip())
                name = parts[1].strip()
                name = name.replace(",","")

                print(f"qty is ---- {qty}",flush=True)
                print(f"name is ---- {name}",flush=True)
                
                # IMPORTANT: Updates the widget key directly
                # If the item exists in our products.py catalog, this will update the counter
                if f"qty_{name}" in st.session_state:
                    st.session_state[f"qty_{name}"] = qty
                    print("in session.state",flush=True)
                elif f"qty_{name}" not in st.session_state:
                    print("note in session.state",flush=True)
                    # Initialize it just in case logic runs before widget creation
                    st.session_state[f"qty_{name}"] = qty
            except:
                pass 
                
def cancel_edit_mode():
    """Resets sidebar to Create Mode"""
    st.session_state.editing_mode = False
    st.session_state.editing_id = None
    st.session_state.form_customer = ""
    st.session_state.form_contact = ""
    st.session_state.form_notes = ""
    for category, items_dict in products.CATALOG.items():
        if isinstance(items_dict, dict):
            for item_name in items_dict:
                st.session_state[f"qty_{item_name}"] = 0
    st.rerun()

def update_order_status(order_id, new_status):
    """Updates Status (Completed/Deleted/Pending)"""
    payload = {
        "action": "update_status",
        "sheet_id": config.SHEET_ID,
        "order_id": order_id,
        "new_status": new_status
    }
    try:
        qs = urllib.parse.urlencode(payload)
        req = urllib.request.Request(f"{config.MACRO_URL}?{qs}", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req): pass
        st.toast(f"Order #{order_id} marked as {new_status}!", icon="✅")
        st.rerun()
    except Exception as e:
        st.error(f"Update failed: {e}")

def save_edited_order(order_id, new_name, new_contact, new_items, new_notes, new_cost):
    """Sends edited details to Google Sheets"""
    local_ts = pd.Timestamp.now(tz="Asia/Kolkata")
    payload = {
        "action": "edit_order",
        "sheet_id": config.SHEET_ID,
        "order_id": order_id,
        "date": local_ts.strftime("%Y-%m-%d"),
        "time": local_ts.strftime("%H:%M:%S"),
        "name": new_name,
        "contact": new_contact,
        "items": new_items,
        "notes": new_notes,
        "cost": str(new_cost)
    }
    try:
        qs = urllib.parse.urlencode(payload)
        req = urllib.request.Request(f"{config.MACRO_URL}?{qs}", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req): pass
        
        # Reset mode after save
        cancel_edit_mode() 
        st.toast(f"Order #{order_id} Updated Successfully!", icon="💾")
    except Exception as e:
        st.error(f"Edit failed: {e}")


# --- 3. THE SUBMISSION HANDLER (CALLBACK) ---
def process_sidebar_submission(mode="create"):
    # A. Get Data
    customer_val = st.session_state.form_customer
    contact_val = st.session_state.form_contact
    notes_val = st.session_state.form_notes
    
    cart_items = {}
    running_total = 0.0
    for category, items_dict in products.CATALOG.items():
        if isinstance(items_dict, dict):
             for item_name, price in items_dict.items():
                qty = st.session_state.get(f"qty_{item_name}", 0)
                if qty > 0:
                    cart_items[item_name] = qty
                    running_total += (qty * price)

    # B. Validation
    if customer_val.strip() == "":
        st.session_state.error_msg = "Error: Missing Customer Name!"
        return 
    if not cart_items:
        st.session_state.error_msg = "Error: Basket is empty!"
        return 

    items_str_list = [f"{qty}x {name}" for name, qty in cart_items.items()]
    compiled_items = ",\n".join(items_str_list)
    
    # C. Execute based on Mode
    if mode == "edit":
        # UPDATE EXISTING
        save_edited_order(
            st.session_state.editing_id, 
            customer_val, 
            contact_val, 
            compiled_items,
            notes_val,
            running_total
        )
    else:
        # CREATE NEW
        local_ts = pd.Timestamp.now(tz="Asia/Kolkata")
        payload = {
            "sheet_id": config.SHEET_ID,
            "order_id": next_order_id,
            "date": local_ts.strftime("%Y-%m-%d"),
            "time": local_ts.strftime("%H:%M:%S"),
            "name": customer_val,
            "contact": contact_val,
            "items": compiled_items,
            "notes": notes_val,
            "cost": str(running_total),
            "status": "Pending",
        }
        try:
            qs = urllib.parse.urlencode(payload)
            req = urllib.request.Request(f"{config.MACRO_URL}?{qs}", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req): pass
            
            # Reset
            st.session_state.form_customer = ""
            st.session_state.form_contact = ""
            st.session_state.form_notes = ""
            for category, items_dict in products.CATALOG.items():
                if isinstance(items_dict, dict):
                    for p in items_dict: st.session_state[f"qty_{p}"] = 0
                
            st.session_state.success_msg = f"Order #{next_order_id} Saved!"
            st.rerun()
        except Exception as e:
            st.session_state.error_msg = f"Sync Failed: {e}"

# --- 4. CONFIRMATION DIALOG ---
@st.dialog("Confirm Order")
def show_confirmation_dialog(cart_items, total_cost, special_notes, mode):
    st.write("Items in Basket:")
    for item, qty in cart_items.items():
        st.write(f"- {qty}x {item}")
    st.divider()
    st.write(f"Special Notes/Instructions:")
    if not special_notes:
        st.write(f"None")
    else:
        st.write(f"{special_notes}")
    st.write(f"{special_notes}")
    st.markdown(f"### Total: ₹{total_cost:,.2f}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", width='stretch'): st.rerun()
    with col2:
        btn_txt = "Update Order" if mode == "edit" else "Create Order"
        if st.button(btn_txt, type="primary", width='stretch'):
            process_sidebar_submission(mode)
            st.rerun()

@st.dialog("Delete Order?")
def show_delete_dialog(order_id):
    st.warning(f"Delete Order #{order_id}?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", width='stretch'): st.rerun()
    with col2:
        if st.button("Delete", type="primary", width='stretch'):
            update_order_status(order_id, "Deleted")

@st.dialog("Edit Order?")
def show_edit_dialog(order_id, order_number):
    st.warning(f"Edit Order #{order_number}?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", width='stretch'): st.rerun()
    with col2:
        if st.button("Edit", type="primary", width='stretch'):
            trigger_edit_mode(order_id)
            st.rerun()


@st.dialog("Return to Work Queue?")
def show_return_to_work_queue_dialog(order_id, order_number):
    st.warning(f"Change status of #{order_number} from Completed to Pending?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", width='stretch'): st.rerun()
    with col2:
        if st.button("Change", type="primary", width='stretch'):
            update_order_status(order_id, "Pending")
            st.toast(f"Order #{order_number} updated successfully to pending status!")
            st.rerun()


# --- 5. SIDEBAR LAYOUT ---
# Initialize Session State Variables
if "editing_mode" not in st.session_state: st.session_state.editing_mode = False
if "form_customer" not in st.session_state: st.session_state["form_customer"] = ""
if "form_contact" not in st.session_state: st.session_state["form_contact"] = ""
if "form_notes" not in st.session_state: st.session_state["form_notes"] = ""

with st.sidebar:
    # 🎨 BRAND LOGO FROM STYLES.PY
    st.image(styles.LOGO_URL, width=60)
    
    # 🔄 HEADER LOGIC
    if st.session_state.editing_mode:
        st.title(f"Editing #{st.session_state.editing_id}")
        st.caption("Modify details below")
    else:
        col_header, col_refresh = st.columns([3, 1])
        with col_header: st.title("Log Order")
        with col_refresh: st.button(icon=":material/refresh:", label="", help="Refresh Data")
        #st.markdown(f"Next ID: **#{next_order_id}**")

    st.divider()
    
    if "error_msg" in st.session_state and st.session_state.error_msg:
        st.error(st.session_state.error_msg)
    if "success_msg" in st.session_state and st.session_state.success_msg:
        st.toast(st.session_state.success_msg, icon="🎉")
        st.session_state.success_msg = ""

    st.title("Customer Details")
    st.text_input("Name", key="form_customer")
    st.text_input("Mobile", key="form_contact")
    st.divider()

    current_cart = {}
    running_total = 0.0
    
    for category, items_dict in products.CATALOG.items():
        st.markdown(f"##### {category}")
        if isinstance(items_dict, dict):
            item_list = list(items_dict.items())
            for i in range(0, len(item_list), 2):
                cols = st.columns(2)
                batch = item_list[i:i+2]
                for j, (item_name, price) in enumerate(batch):
                    with cols[j]:
                        widget_key = f"qty_{item_name}"
                        if widget_key not in st.session_state: st.session_state[widget_key] = 0
                        
                        st.number_input(
                            f"{item_name}\n(₹{price:.0f})", 
                            min_value=0, max_value=50, step=1, key=widget_key, value=st.session_state[widget_key]
                        )
                        
                        qty = st.session_state[widget_key]
                        if qty > 0:
                            current_cart[item_name] = qty
                            running_total += (qty * price)
    
        st.divider()
        
    # 1. Inspect the value and force-heal it if it got mutated into a non-string
    if "form_notes" in st.session_state:
        # If it became None, NaN, or a float, convert it cleanly to a string
        if st.session_state["form_notes"] is None or not isinstance(st.session_state["form_notes"], str):
            st.session_state["form_notes"] = ""
        else:
            st.session_state["form_notes"] = ""

    special_notes = st.text_input("Special Notes/Instructions", key="form_notes")
    st.divider()
    st.markdown(f"### Total: ₹{running_total:,.2f}")

    # FOOTER BUTTONS
    if st.session_state.editing_mode:
        # EDIT MODE BUTTONS
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Cancel", width='stretch'):
                cancel_edit_mode()
        with c2:
            if st.button("Save Changes", type="primary", width='stretch'):
                if st.session_state.form_customer.strip() == "": st.error("Name required!")
                elif not current_cart: st.error("Basket empty!")
                else: show_confirmation_dialog(current_cart, running_total, special_notes, "edit")
    else:
        # CREATE MODE BUTTON
        if st.button("Submit", width='stretch'):
            if st.session_state.form_customer.strip() == "": st.error("Name required!")
            elif not current_cart: st.error("Basket empty!")
            else: show_confirmation_dialog(current_cart, running_total, special_notes, "create")

# --- 6. MAIN DASHBOARD ---
st.title("Moon & Melody Dashboard")

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

tab_queue, tab_completed, tab_charts = st.tabs(["Work Queue", "Completed Orders", "Analytics & History"])

with tab_queue:
    if df.empty:
        st.success("No pending orders! You are all caught up.")
        styles.celebrate()

    elif "Status" in df.columns:
        pending_orders = df[df["Status"] == "pending"]
        
        if pending_orders.empty:
            st.success("No pending orders! You are all caught up.")
            styles.celebrate()
        else:
            cols = st.columns(3)
            for idx, (_, row) in enumerate(pending_orders.iterrows()):
                col_idx = idx % 3
                with cols[col_idx]:
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.markdown(f"**#{row.get('Order ID')}**")

                        with c2:
                            # ✏️ EDIT BUTTON - Triggers Sidebar Population
                            if st.button(icon=":material/edit:", label="" , key=f"edit_{row['Order ID']}", help="Edit in Sidebar", width='stretch'):
                                show_edit_dialog(row,row['Order ID']);
                                
                        with c3:
                            if st.button(icon=":material/delete:", label="", key=f"del_{row['Order ID']}", help="Delete Order", width='stretch'):
                                show_delete_dialog(row['Order ID'])
                        
                        st.markdown(f"### {row.get('Customer Name', 'Unknown')}")
                        st.markdown(f"{row.get('Customer Contact', '-')}")
                        st.markdown("---")
                        
                        raw_items = str(row.get('Items', ''))
                        if "\n" in raw_items:
                            items_text = raw_items.replace(",\n", "\n- ")
                        else:
                            items_text = raw_items.replace(",", "\n- ")
                            
                        st.markdown(f"**Items:**\n- {items_text}")
                        st.markdown("---");

                        raw_notes = row.get('Special Notes/Instructions', '')
                        # 2. Check if it's a Pandas NaN object, an empty string, or the text "nan"
                        if pd.isna(raw_notes) or str(raw_notes).strip().lower() in ["nan", ""]:
                            special_notes = "None"
                        else:
                            special_notes = str(raw_notes).strip()

                        st.markdown(f"**Special Notes:**")
                        st.markdown(f"{special_notes}")
                        st.markdown(f"### ₹{row.get('Cost', 0.0):,.0f}")
                        
                        btn_key = f"done_{row.get('Order ID')}_{idx}"
                        if st.button("Done", key=btn_key, width='stretch'):
                            update_order_status(row['Order ID'], "Completed")

with tab_completed:
    if df.empty:
        st.success("Complete orders to see them here!")

    elif "Status" in df.columns:
        completed_orders = df[df["Status"] == "completed"]
        
        if completed_orders.empty:
            st.success("Complete orders to see them here!")

        else:
            cols = st.columns(3)
            for idx, (_, row) in enumerate(completed_orders.iterrows()):
                col_idx = idx % 3
                with cols[col_idx]:
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        c1.markdown(f"**#{row.get('Order ID')}**")

                        with c2:
                            # ✏️ BACK BUTTON - Triggers State of Completed Order to Pending
                            if st.button(icon=":material/arrow_back:", label="" , key=f"edit_{row['Order ID']}", help="Return to Work Queue", width='stretch'):
                                show_return_to_work_queue_dialog(row,row['Order ID']);

                        st.markdown(f"### {row.get('Customer Name', 'Unknown')}")
                        st.markdown(f"{row.get('Customer Contact', '-')}")
                        st.markdown("---")
                        
                        raw_items = str(row.get('Items', ''))
                        if "\n" in raw_items:
                            items_text = raw_items.replace(",\n", "\n- ")
                        else:
                            items_text = raw_items.replace(",", "\n- ")
                            
                        st.markdown(f"**Items:**\n- {items_text}")
                        st.markdown("---");

                        raw_notes = row.get('Special Notes/Instructions', '')
                        # 2. Check if it's a Pandas NaN object, an empty string, or the text "nan"
                        if pd.isna(raw_notes) or str(raw_notes).strip().lower() in ["nan", ""]:
                            special_notes = "None"
                        else:
                            special_notes = str(raw_notes).strip()

                        st.markdown(f"**Special Notes:**")
                        st.markdown(f"{special_notes}")
                        st.markdown(f"### ₹{row.get('Cost', 0.0):,.0f}")
                        
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
                width='stretch',
                hide_index=True
            )
        else:
            st.info("Complete some orders to see your analytics!")
