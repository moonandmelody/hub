import ssl
import urllib.parse
import urllib.request
import pandas as pd
import streamlit as st
import products
import config
import styles  # <--- NEW: Imports your beautiful design file
import order_packaging as pkg
import datetime
import date_config as dt_cfg
import requests
import inventory

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
        # Use the direct Google CSV export link as your source of truth
        url = f"https://docs.google.com/spreadsheets/d/{config.SHEET_ID}/export?format=csv&gid=0"
        df_raw = None
        
        try:
            # 1. Fetch direct raw CSV dataset
            df_raw = pd.read_csv(url)
            print(f"📡 DEBUG - Fetch raw data success. Columns: {list(df_raw.columns)}", flush=True)
        except Exception as e:
            # ✅ FIXED: Changed st.print to standard print
            print(f"❌ DEBUG - Failed to fetch raw CSV data: {e}", flush=True)
            
            # Fallback to Macro URL if the direct CSV link fails
            try:
                df_raw = pd.read_csv(f"{url}?action=get_data")
            except Exception as macro_err:
                print(f"❌ DEBUG - Macro backup link also failed: {macro_err}", flush=True)
        
        # 2. THE ABSOLUTE GUARDRAIL MODULATOR
        if df_raw is not None and not df_raw.empty:
            # If Pandas read all columns into ONE single key string because of a tab separation issue:
            if len(df_raw.columns) == 1 or "\t" in "".join(df_raw.columns.astype(str)):
                # Force-reload the entire dataset specifying the tab character delimiter explicitly
                if "docs.google.com" in url:
                    df = pd.read_csv(url, sep="\t")
                else:
                    df = pd.read_csv(f"{config.MACRO_URL}?action=get_data", sep="\t")
            else:
                df = df_raw.copy()
                
            # Standardize all column names by stripping trailing formatting codes (\r, spaces)
            df.columns = [str(col).strip() for col in df.columns]
        else:
            # 3. Emergency Safe Template: If your sheet has 0 rows, pre-build your exact columns
            df = pd.DataFrame(columns=[
                "Order ID", "Date", "Time", "Customer Name", "Customer Contact", 
                "Items", "Packaging Items", "Special Notes/Instructions", "Cost", 
                "Packaging Cost", "Status", "Type of Order", "Delivery Date", "Delivery Time",
                "Previous Date", "Previous Time", "Previous Items", "Previous Notes/Instructions"
            ])
            
        # Display the active discovered column array in your Streamlit sidebar
        df = df.loc[:, ~df.columns.duplicated()]

        # 4. FLEXIBLE MAPPING SYSTEM (Accounts for spaces, tabs, and casing variations)
        mapping = {}
        for col in df.columns:
            cleaned = str(col).lower().replace(" ", "").replace("\t", "").replace("\r", "")
            if "orderid" in cleaned or "order id" in str(col).lower():
                mapping[col] = "Order ID"
            elif "customername" in cleaned or "customer name" in str(col).lower():
                mapping[col] = "Customer Name"
            elif "customercontact" in cleaned or "customer contact" in str(col).lower():
                mapping[col] = "Customer Contact"
            elif "items" in cleaned:
                mapping[col] = "Items"
            elif "specialnotes/instructions" in cleaned or "specialnotes" in cleaned:
                mapping[col] = "Special Notes/Instructions"
            elif "cost" in cleaned or "revenue" in cleaned:
                mapping[col] = "Cost"
            elif "status" in cleaned:
                mapping[col] = "Status"
            elif "typeoforder" in cleaned:
                mapping[col] = "Type of Order"
            elif "packagingcost" in cleaned:
                mapping[col] = "Packaging Cost"
            elif "deliverydate" in cleaned:
                mapping[col] = "Delivery Date"
            elif "deliverytime" in cleaned:
                mapping[col] = "Delivery Time"

        df = df.rename(columns=mapping)

        df = df.loc[:, ~df.columns.duplicated()]

        # 5. DATA CLEANING & REPAIRS
        if "Customer Name" in df.columns:
            df = df.dropna(subset=["Customer Name"])
            df = df[df["Customer Name"].astype(str).str.strip() != ""]
        else:
            # Instead of returning a blank dataframe, keep the structure intact with empty rows
            print("⚠️ WARNING: 'Customer Name' column could not be mapped!", flush=True)
            # Inject a blank column name temporarily so the file structure doesn't crash your metrics
            df["Customer Name"] = ""

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

        if "Type of Order" in df.columns:
            df["Type of Order"] = df["Type of Order"].fillna("preorder").astype(str).str.strip().str.lower().replace("-","")
        else:
            df["Type of Order"] = "preorder"

        return df
    except Exception as e:
        st.error(f"Google Cloud Sync Error: {e}")
        return pd.DataFrame(columns=["Status", "Cost", "Order ID", "Customer Name"]) # Keep basic structural fallbacks

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

if "current_view" not in st.session_state:
    st.session_state.current_view = "dashboard"

if st.session_state.current_view == "entry_form":
    # Layout for the dedicated workspace header
    header_col, close_col = st.columns([4, 1])
    with header_col:
        st.title("📝 New Inventory Entry")
        st.write("Complete your updates in the interactive panel below.")
    with close_col:
        # Secure, functioning close button that switches state back immediately
        if st.button("✖️ Close Panel", use_container_width=True, type="primary"):
            st.session_state.current_view = "dashboard"
            st.rerun()

    st.markdown("---");

    st.components.v1.iframe(config.INVENTORY_LINK, height=700, scrolling=True)
    
    # Bottom alternative exit button
    if st.button("🔄 Sync & Return to Dashboard", use_container_width=True):
        st.session_state.current_view = "dashboard"
        st.rerun()
        

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

    raw_delivery_date = row.get('Delivery Date', '')

    if pd.isna(raw_delivery_date) or str(raw_delivery_date).strip().lower() in ["nan", "", "none"]:
        # Fallback to current calendar date if the sheet field cell is empty
        st.session_state["form_date"] = datetime.date.today()
    else:
        try:
            # Check if Pandas already natively converted it to a datetime/date object
            if isinstance(raw_delivery_date, datetime.date):
                st.session_state["form_date"] = raw_delivery_date
            elif isinstance(raw_delivery_date, pd.Timestamp):
                st.session_state["form_date"] = raw_delivery_date.date()
            else:
                # Clean and parse string dates formatted as YYYY-MM-DD from Google Sheets
                clean_date_str = str(raw_delivery_date).strip().split("T")[0] # Cleans off any trailing time stamps
                st.session_state["form_date"] = datetime.datetime.strptime(clean_date_str, "%Y-%m-%d").date()
        except Exception as e:
            print(f"⚠️ Date conversion failed for raw value '{raw_delivery_date}': {e}", flush=True)
            st.session_state["form_date"] = datetime.date.today()
    
    st.session_state["form_time_slot"] = str(row.get('Delivery Time', dt_cfg.TIME_SLOTS[0])).strip()

    
    # 2. Reset All Counters First
    for category, items_dict in products.CATALOG.items():
        if isinstance(items_dict, dict):
            for item_name in items_dict:
                st.session_state[f"qty_{item_name}"] = 0 
    
    # 3. Parse Items String safely
    # 1. Fetch the items structure
    items_data = row.get('Items', '')

    # 2. CRITICAL FIX: Extract the raw string from the Pandas Series
    if hasattr(items_data, "iloc"):
        # If it is a Series object, grab the very first row value safely
        raw_items = str(items_data.iloc[0]) if len(items_data) > 0 else ""
    elif isinstance(items_data, list) or hasattr(items_data, "values"):
        # Fallback to extract scalar strings out of nested array blocks
        try:
            raw_items = str(items_data[0])
        except:
            raw_items = str(items_data)
    else:
        # If it is already a regular text cell, use it as is
        raw_items = str(items_data)

    # 3. Clean out dirty data artifacts or missing values completely
    raw_items = raw_items.strip()
    if raw_items.lower() in ["nan", "none", ""]:
        raw_items = ""

    # Now this print statement will output a clean, pure string on your console!
    print(f"🔍 DEBUG - CLEAN raw_items: {raw_items}", flush=True)

    # Handle both newlines (new format) and commas (old format)
    if "\n" in raw_items:
        lines = raw_items.split('\n')
    else:
        lines = raw_items.split(',')

    for line in lines:
        print(f"🔍 DEBUG - lines list: {lines}",flush=True)
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

if st.session_state.get("execute_edit_load", False):
    # 1. Fetch the stored row data
    row_to_load = st.session_state.pop("selected_row_to_edit")
    st.session_state.pop("execute_edit_load") # Reset the trigger flag
    
    # 2. Run your original parsing function natively in the main script context!
    trigger_edit_mode(row_to_load)

                
def cancel_edit_mode():
    """Resets sidebar to Create Mode"""
    st.session_state.editing_mode = False
    st.session_state.editing_id = ""
    
    st.session_state.form_customer = ""
    st.session_state.form_contact = ""
    st.session_state.form_notes = ""
    st.session_state.form_date = ""
    st.session_state["form_time_slot"] = dt_cfg.TIME_SLOTS[0]
    for category, items_dict in products.CATALOG.items():
        if isinstance(items_dict, dict):
            for item_name in items_dict:
                st.session_state[f"qty_{item_name}"] = 0
    #st.rerun()

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

def save_edited_order(order_id, new_name, new_contact, new_items, packaging_breakdown, new_notes, new_cost, packaging_total, new_delivery_date, new_delivery_time):
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
        "packaging": packaging_breakdown,
        "notes": new_notes,
        "cost": str(new_cost),
        "packagingCost": str(packaging_total),
        "deliveryDate": new_delivery_date,
        "deliveryTime": new_delivery_time
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

def calculate_order_packaging(current_cart):
    """
    Calculates packaging fees by analyzing current_cart items 
    against the rules dynamically generated in packaging.py
    """
    packaging_total = 0.0
    packaging_breakdown = []
    
    liquid_items = {}
    food_items = {}
    
    # 1. Separate current cart items using the generated rules mapping
    for item_name, qty in current_cart.items():
        item_name = str(item_name).strip().lower()
        rule = pkg.PACKAGING_RULES.get(item_name)
        print(f"rule inside is {rule}",flush=True)
        if not rule:
            continue  # Safeguard if an item is not found
            
        if rule["type"] == "liquid":
            liquid_items[item_name] = qty
            print(f"liquid_items[item_name] {liquid_items[item_name]} = qty {qty}",flush=True)
        elif rule["type"] == "food":
            food_items[item_name] = {
                "qty": qty,
                "packaging_type": rule.get("packaging_type")
            }
            print(f"food_items -------------- {food_items}",flush=True)
            
    # 2. Liquid Logic: Maximize Big Cartons (holds 2), remainder to Small Carton
    for item_name, qty in liquid_items.items():
        big_cartons = qty // 2
        small_cartons = qty % 2
        
        item_cost = (big_cartons * pkg.BIG_CARTON) + (small_cartons * pkg.SMALL_CARTON)
        packaging_total += item_cost
        
        parts = []
        if big_cartons > 0: parts.append(f"{big_cartons}x Big Carton")
        if small_cartons > 0: parts.append(f"{small_cartons}x Small Carton")
        
        #packaging_breakdown.append(f"{' + '.join(parts)} ({item_name}): ₹{str(item_cost)}")
        packaging_breakdown.append(f"{' + '.join(parts)}: ₹{str(item_cost)}")
        print(f"packaging_breakdown in liquids is -------------- {packaging_breakdown}",flush=True)
        
    # 3. Food Logic: Standard linear multiplication per item packaging cost
    for item_name, info in food_items.items():
        item_name = str(item_name).strip().lower()
        print(f"item_name -------food------- {item_name}",flush=True)
        print(f"info -------food------- {info}",flush=True)
        if "LONG_BOX_WITH_WINDOW" in info["packaging_type"]:
            # IF IT'S A LONG BOX THEN WE SEND A SMALL DIP CUP
            item_cost = info["qty"] * getattr(pkg, info["packaging_type"]) + pkg.SMALL_DIP_CUP
            print(f"item_cost -------food--with dip cup----- {item_cost}",flush=True)
            packaging_total += item_cost
            print(f"packaging_total -------food---with dip cup---- {packaging_total}",flush=True)
            #packaging_breakdown.append(f"{info['qty']}x Long Box with Window & Dip ({item_name}): ₹{str(item_cost)}")
            packaging_breakdown.append(f"{info['qty']}x Long Box with Window & Dip: ₹{str(item_cost)}")
        elif "SQUARE_BOX" in info["packaging_type"]:
            item_cost = info["qty"] * getattr(pkg, info["packaging_type"])
            print(f"item_cost -------square box------- {item_cost}",flush=True)
            packaging_total += item_cost
            print(f"packaging_total ------square box-------- {packaging_total}",flush=True)
            #packaging_breakdown.append(f"{info['qty']}x Square Box ({item_name}): ₹{str(item_cost)}")
            packaging_breakdown.append(f"{info['qty']}x Square Box: ₹{str(item_cost)}")
        elif "SMALL_DIP_CUP" in info["packaging_type"]:
            item_cost = info["qty"] * getattr(pkg, info["packaging_type"])
            print(f"item_cost -------small dip cup------- {item_cost}",flush=True)
            packaging_total += item_cost
            print(f"packaging_total ------small dip cup-------- {packaging_total}",flush=True)
            #packaging_breakdown.append(f"{info['qty']}x Small Dip Cup ({item_name}): ₹{str(item_cost)}")
            packaging_breakdown.append(f"{info['qty']}x Small Dip Cup: ₹{str(item_cost)}")
        else:
            item_cost = info["qty"] * getattr(pkg, info["packaging_type"])
            print(f"item_cost -------big dip cup------- {item_cost}",flush=True)
            packaging_total += item_cost
            print(f"packaging_total ------big dip cup-------- {packaging_total}",flush=True)
            #packaging_breakdown.append(f"{info['qty']}x Big Dip Cup ({item_name}): ₹{str(item_cost)}")
            packaging_breakdown.append(f"{info['qty']}x Big Dip Cup: ₹{str(item_cost)}")
            
        if item_cost > 0:
            print(f"pricing breakdown is -------food------- {packaging_breakdown}",flush=True)
            
    return packaging_total, packaging_breakdown


# --- 3. THE SUBMISSION HANDLER (CALLBACK) ---
def process_sidebar_submission(packaging_breakdown, packaging_total, mode="create"):
    # A. Get Data
    customer_val = st.session_state.form_customer
    contact_val = st.session_state.form_contact
    notes_val = st.session_state.form_notes
    delivery_date = st.session_state.form_date
    delivery_time = st.session_state.form_time_slot
    type_of_order = st.session_state.form_order

    print(f"type_of_order is {type_of_order}", flush=True)
    
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
    if not delivery_date:
        st.session_state.error_msg = "Error: Select a delivery date"
        return
    if not delivery_time:
        st.session_state.error_msg = "Error: Select a delivery time slot"
        return
    

    items_str_list = [f"{qty}x {name}" for name, qty in cart_items.items()]
    compiled_items = ",\n".join(items_str_list)

    compiled_packaging_str_list = ",\n".join(packaging_breakdown)
    
    # C. Execute based on Mode
    if mode == "edit":
        # UPDATE EXISTING
        save_edited_order(
            st.session_state.editing_id, 
            customer_val, 
            contact_val, 
            compiled_items,
            compiled_packaging_str_list,
            notes_val,
            running_total,
            packaging_total,
            delivery_date,
            delivery_time
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
            "packaging": compiled_packaging_str_list,
            "notes": notes_val,
            "cost": str(running_total),
            "packagingCost": str(packaging_total),
            "status": "Pending",
            "typeOfOrder": type_of_order,
            "deliveryDate": delivery_date,
            "deliveryTime": delivery_time
        }
        try:
            qs = urllib.parse.urlencode(payload)
            req = urllib.request.Request(f"{config.MACRO_URL}?{qs}", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req): pass
            
            # Reset
            st.session_state.form_customer = ""
            st.session_state.form_contact = ""
            st.session_state.form_notes = ""
            st.session_state.form_date = ""
            st.session_state.form_time_slot = ""
            
            for category, items_dict in products.CATALOG.items():
                if isinstance(items_dict, dict):
                    for p in items_dict: st.session_state[f"qty_{p}"] = 0
                
            st.session_state.success_msg = f"Order #{next_order_id} Saved!"
            st.rerun()
        except Exception as e:
            st.session_state.error_msg = f"Sync Failed: {e}"

# --- 4. CONFIRMATION DIALOG ---
@st.dialog("Confirm Order")
def show_confirmation_dialog(customerName, customerContact, cart_items, total_cost, delivery_date, delivery_time, mode):
    packaging_total, packaging_breakdown = calculate_order_packaging(cart_items)
    st.divider()
    order_details, delivery_details = st.columns(2)
    with order_details:
        order_details.markdown(
            f"""
            <div id="detailsDiv" style="display:grid;">
                <span><b>Name:</b> {customerName}</span>
                <span><b>Mobile:</b> {customerContact}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with delivery_details:
        raw_delivery_date = str(delivery_date)
        raw_delivery_date = raw_delivery_date[8:10] + "/" + raw_delivery_date[5:7] + "/" + raw_delivery_date[0:4]
        delivery_details.markdown(
            f"""
            <div id="deliveryDiv" style="display:grid;justify-content:end;">
                <span><b>Date:</b> {raw_delivery_date}</span>
                <span><b>Time:</b> {delivery_time}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    items, packaging = st.columns(2)
   
    with items:
        items.write("Items in Basket:")
        for item, qty in cart_items.items():
            items.write(f"- {qty}x {item}")
    with packaging:
        packaging.write("Packaging Details")
        formatted_markdown = ""
        # 2. Loop through every single item and add it as a new bullet point row
        for line in packaging_breakdown:
            # Optional: Clean up and capitalize item names for a better presentation
            title_line = line.replace("(", "(").title()  # Ensures brand names are capitalised
            packaging.write(f"- {title_line}\n")
    
        # 5. Render it seamlessly on your Streamlit App interface
        packaging.write(f"{formatted_markdown}")
    
    st.divider()
    
    st.write(f"Special Notes/Instructions:")
    
    special_notes = st.session_state.get("form_notes", "").strip()
    if not special_notes:
        st.write(f"Not Available")
    else:
        st.write(f"{special_notes}")

    st.divider()
    item_price, packaging_price = st.columns(2)
    with item_price:
        item_price.write(f"### Total: ₹{total_cost:,.2f}")

    with packaging_price:
        packaging_price.markdown(
            f"""
            <div id="packagingDiv" style="height: 60px;align-content: end;">
                <span><b>Total Packaging Fee:</b> ₹{packaging_total:,.2f}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", width='stretch'): st.rerun()
    with col2:
        btn_txt = "Update Order" if mode == "edit" else "Create Order"
        if st.button(btn_txt, type="primary", width='stretch'):
            process_sidebar_submission(packaging_breakdown, packaging_total, mode)
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
        if st.button("Cancel", width='stretch'): 
            st.rerun()
    with col2:
        # When they click "Confirm", we set a trigger flag and close the dialog
        if st.button("Confirm", type="primary", width='stretch'):
            st.session_state["execute_edit_load"] = True
            st.rerun()

@st.dialog("Return to Work Queue?")
def show_return_to_work_queue_dialog(order_id):
    st.warning(f"Change status of #{order_id} from Completed to Pending?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", width='stretch'): st.rerun()
    with col2:
        if st.button("Change", type="primary", width='stretch'):
            update_order_status(order_id, "Pending")
            st.toast(f"Order #{order_id} updated successfully to pending status!")
            st.rerun()

# validate delivery date 
def validate_selected_date():
    """Natively validates and rejects selection of Mondays, Tuesdays, or custom holidays."""
    selected = st.session_state.get("form_date")
    if not selected:
        return

    # Check day of the week (0 = Monday, 1 = Tuesday)
    is_weekday_blocked = selected.weekday() in [0, 1]
    
    # Check your custom configuration blacklist file strings
    selected_str = selected.strftime("%Y-%m-%d")
    is_custom_blocked = selected_str in dt_cfg.CUSTOM_BLOCKED_DATES

    if is_weekday_blocked or is_custom_blocked:
        # Raise an explicit visual alert on the user's workspace
        st.sidebar.error(f"❌ Closed on {selected.strftime('%A')} ({selected_str})!")
        
        # Automatically calculate and snap to the next valid open operational day
        fallback = datetime.date.today()
        while fallback.weekday() in [0, 1] or fallback.strftime("%Y-%m-%d") in dt_cfg.CUSTOM_BLOCKED_DATES:
            fallback += datetime.timedelta(days=1)
            
        # Repair the session state variable value smoothly
        st.session_state["form_date"] = fallback


# --- 5. SIDEBAR LAYOUT ---
# Initialize Session State Variables
if "editing_mode" not in st.session_state: st.session_state.editing_mode = False
if "form_customer" not in st.session_state: st.session_state["form_customer"] = ""
if "form_contact" not in st.session_state: st.session_state["form_contact"] = ""
if "form_notes" not in st.session_state: st.session_state["form_notes"] = ""
if "form_date" not in st.session_state: st.session_state["form_date"] = ""
if "form_time_slot" not in st.session_state: st.session_state["form_time_slot"] = ""
if "form_order" not in st.session_state: st.session_state["form_order"] = ""

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

    st.title("Type of Order")
    st.selectbox(
        label="Type of Order",
        options= ['Pre-Order','Walk-in'],
        key="form_type"
    )
    st.divider()
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
                        current_qty = st.session_state.get(widget_key, 0)
                        
                        st.number_input(
                            f"{item_name}\n(₹{price:.0f})", 
                            min_value=0, max_value=50, step=1, key=widget_key, value=int(current_qty)
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

    st.text_input("Special Notes/Instructions", key="form_notes")
    
    st.divider()

    def get_available_order_dates(days_to_show=21):
        """Generates a clean list of upcoming selectable operational dates, filtering closures."""
        available_dates = []
        today = datetime.date.today()
        
        for i in range(days_to_show):
            future_date = today + datetime.timedelta(days=i)
            
            # Filter out Mondays (0) and Tuesdays (1)
            if future_date.weekday() in [0,1]:
                continue
                
            # Filter out custom holidays listed in your config file
            if future_date.strftime("%Y-%m-%d") in dt_cfg.CUSTOM_BLOCKED_DATES:
                continue
                
            available_dates.append(future_date)
        return available_dates
    
    
    # --- GENERATE DATA INPUT POOLS (CRITICAL FIX FOR NAME-ERROR) ---
    open_days = get_available_order_dates(days_to_show=21)
    date_labels = {d: d.strftime("%A, %d %b") for d in open_days}


    # 1. INITIALIZE: Find the nearest open business day
    if "form_date" not in st.session_state:
        starting_day = datetime.date.today()
        # 0 = Monday, 1 = Tuesday
        while starting_day.weekday() in [0, 1] or starting_day.strftime("%Y-%m-%d") in dt_cfg.CUSTOM_BLOCKED_DATES:
            starting_day += datetime.timedelta(days=1)
        st.session_state["form_date"] = starting_day

    if "form_time_slot" not in st.session_state:
        st.session_state["form_time_slot"] = dt_cfg.TIME_SLOTS[0]
    
    
    # 2. THE CORRECTED GUARDIAN VALIDATION FUNCTION
    def handle_date_change():
        """Validates the input date and moves it forward if it hits a blocked day."""
        # Read what the user actually picked from the temporary widget state
        chosen_date = st.session_state.get("temp_date_picker")
        if not chosen_date:
            return
    
        # Keep advancing the date forward until it lands on an open operating day
        validated_date = chosen_date
        has_violation = False
        
        while validated_date.weekday() in [0, 1] or validated_date.strftime("%Y-%m-%d") in dt_cfg.CUSTOM_BLOCKED_DATES:
            has_violation = True
            validated_date += datetime.timedelta(days=1)
    
        if has_violation:
            # Show a friendly alert popup informing them of the adjustment
            #st.error(f"ℹ️ We are closed on that day! Advanced order date to: {validated_date.strftime('%A, %d %b')}")
            st.toast(f"ℹ️ We are closed on that day! Advanced order date to: {validated_date.strftime('%A, %d %b')}")
        
        # Save the clean, verified date into your permanent form state
        st.session_state["form_date"] = validated_date
    
    
    #3. RENDER THE WIDGET SAFELY
    date_col, time_col = st.columns(2)

    with date_col:
        # 1. Fetch your target date variable from memory state
        saved_form_date = st.session_state.get("form_date", datetime.date.today())
        
        # 2. CRITICAL TYPE GUARD: Force convert string dates into datetime.date objects
        if isinstance(saved_form_date, str):
            try:
                # Clean string and extract just the YYYY-MM-DD portion
                clean_date_str = saved_form_date.strip().split("T")[0]
                saved_form_date = datetime.datetime.strptime(clean_date_str, "%Y-%m-%d").date()
            except Exception as e:
                # Fallback if text format is heavily corrupted or unparseable
                saved_form_date = datetime.date.today()
                
        # Save the cleaned object back into state to keep types synchronized
        st.session_state["form_date"] = saved_form_date
    
        # 3. SAFE INJECTOR: Handle dates outside your standard active calendar timeline window
        if saved_form_date not in open_days:
            open_days.append(saved_form_date)
            # Both sides are now datetime.date objects, so sorting works flawlessly!
            open_days.sort() 
            date_labels[saved_form_date] = saved_form_date.strftime("%A, %d %b")
    
        # 4. Render your date dropdown menu safely
        st.session_state["form_date"] = st.selectbox(
            label="Select Order Date",
            options=open_days,
            index=open_days.index(saved_form_date),
            format_func=lambda x: date_labels.get(x, str(x))
        )
    
    with time_col:
        # 3. SMART FILTER: If order is for today, look to drop past hours slots dynamically
        current_time = datetime.datetime.now()
        active_slots = dt_cfg.TIME_SLOTS.copy()
        
        if st.session_state["form_date"] == datetime.date.today():
            filtered_slots = []
            for slot in dt_cfg.TIME_SLOTS:
                # Extract the starting hour from the string (e.g., "11:00 AM" -> 11, "03:00 PM" -> 15)
                start_time_str = slot.split(" - ")[0]
                parsed_hour = datetime.datetime.strptime(start_time_str, "%I:%M %p").hour
                
                # Only keep slots where the starting hour is in the future
                if current_time.hour < parsed_hour:
                    filtered_slots.append(slot)
            
            # Fallback if it is very late in the day
            active_slots = filtered_slots if filtered_slots else ["Slots Closed for Today"]
        
        # 4. Render the Time Slot Selectbox Dropdown
        # Checks if your previously saved value is still valid in the current active slots list
        default_time_idx = active_slots.index(st.session_state["form_time_slot"]) if st.session_state["form_time_slot"] in active_slots else 0
        
        st.session_state["form_time_slot"] = st.selectbox(
            label="Select Time Slot",
            options=active_slots,
            index=default_time_idx
        )
    
    st.divider()
    
    st.markdown(f"### Total: ₹{running_total:,.2f}")

    # FOOTER BUTTONS
    if st.session_state.editing_mode:
        # EDIT MODE BUTTONS
        c1, c2 = st.columns(2)
        with c1:
            st.button("Cancel", width='stretch',key="cancel_edit_sidebar_btn", on_click=cancel_edit_mode)
        with c2:
            if st.button("Save Changes", type="primary", width='stretch'):
                if st.session_state.form_customer.strip() == "": st.error("Name required!")
                elif not current_cart: st.error("Basket empty!")
                else: show_confirmation_dialog(st.session_state["form_customer"],st.session_state["form_contact"],current_cart, running_total, st.session_state.form_date, st.session_state.form_time_slot, "edit")
    else:
        # CREATE MODE BUTTON
        if st.button("Submit", width='stretch'):
            if st.session_state.form_customer.strip() == "": st.error("Name required!")
            elif not current_cart: st.error("Basket empty!")
            else: show_confirmation_dialog(st.session_state["form_customer"],st.session_state["form_contact"],current_cart, running_total, st.session_state.form_date, st.session_state.form_time_slot, "create")

# --- 6. MAIN DASHBOARD ---
st.title("Moon & Melody Dashboard")

if st.button("Update Inventory", type="primary", use_container_width=True):
    st.session_state.current_view = "entry_form"
    st.rerun()
    
if not df.empty:
    pending_count = len(df[(df["Status"] == "pending") & (df["Type of Order"] == "preorder")])
    #pending_count = len(df[df["Status"] == "pending"])
    walk_in_count = len(df[(df["Status"] == "pending") & (df["Type of Order"] == "walkin")])
    #walk_in_count = len(df[df["Status"] == "walkin"])
    completed_df = df[df["Status"] == "completed"]
    total_rev = completed_df["Cost"].sum() if not completed_df.empty else 0.0
else:
    pending_count = 0
    total_rev = 0.0
    walk_in_count = 0

m1, m2, m3 = st.columns(3)

m2.metric("Total Revenue", f"₹{total_rev:,.0f}")
completed_count = len(df[df['Status'].astype(str).str.strip().str.lower() == 'completed'])


st.markdown(
    f""",
    "<div id='allMetricDiv'> {m1.metric('Total Pending Orders', {pending_count + walk_in_count}, delta_color='inverse')}
    {m2.metric('Total Revenue', '₹{total_rev:,.0f}')}
    {m3.metric('Completed Orders', {completed_count})} </div>",
    """, unsafe_allow_html=True)

st.divider()

tab_queue, tab_walk_ins, tab_completed, tab_charts = st.tabs([f"Pre Orders :red[{pending_count}]", f"Walk-ins :red[{walk_in_count}]", f"Completed Orders :green[{completed_count}]", "Analytics & History"])

with tab_queue:
    if df.empty:
        st.success("No pending orders! You are all caught up.")
        styles.celebrate()

    elif "Status" in df.columns:
        pending_orders = df[(df["Status"] == "pending") & (df["Type of Order"] == "preorder")]
        
        if pending_orders.empty:
            st.success("No pre-orders available! You are all caught up.")
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
                                st.session_state["selected_row_to_edit"] = row
                                show_edit_dialog(row,row['Order ID'])
                                
                        with c3:
                            if st.button(icon=":material/delete:", label="", key=f"del_{row['Order ID']}", help="Delete Order", width='stretch'):
                                show_delete_dialog(row['Order ID'])

                        raw_date = str(row.get('Delivery Date'))
                        raw_date = raw_date[8:10] + "/" + raw_date[5:7] + "/" + raw_date[0:4]
                        st.caption(f"{raw_date}")
                        st.caption(f"{row.get('Delivery Time')}")
                        st.markdown(f"### {row.get('Customer Name', 'Unknown')}")
                        st.markdown(f"{row.get('Customer Contact', '-')}")
                        st.markdown("---")
                        
                        # 1. Cleanly pull the text, handling Pandas Series or missing objects safely
                        raw_items = row.get('Items', '')
                        
                        # Handle cases where Pandas accidentally packages it as a Series/Object array
                        if hasattr(raw_items, "to_string") or not isinstance(raw_items, (str, int, float)):
                            try:
                                # Convert a pandas Series or row subset back to pure scalar data
                                raw_items = str(raw_items.values[0]) if hasattr(raw_items, "values") else str(raw_items)
                            except:
                                raw_items = str(raw_items)
                        else:
                            raw_items = str(raw_items)

                        # 2. Clean out dirty data artifacts or empty spaces
                        raw_items_clean = raw_items.strip()
                        if pd.isna(raw_items) or raw_items_clean.lower() in ["nan", "none", ""]:
                            items_text = "No items selected"
                        else:
                            # 3. Format into structured markdown list items cleanly
                            # Standardize old formats using commas to clean newlines first
                            formatted_text = raw_items_clean.replace(",\n", "\n").replace(",", "\n")
                            
                            # Build structural markdown bullet strings row by row
                            lines = [f"- {line.strip().lstrip('- ')}" for line in formatted_text.split('\n') if line.strip()]
                            items_text = "\n".join(lines)
                            
                        # 4. Render clean on your layout card
                        st.markdown(f"**Items:**\n{items_text}")
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

with tab_walk_ins:
    #nothing here yet
    walkin_orders = df[(df["Status"] == "pending") & (df["Type of Order"] == "walkin")]
        
    if walkin_orders.empty:
        st.success("No walkin orders available! You are all caught up.")
        styles.celebrate()
    else:
        cols = st.columns(3)
        for idx, (_, row) in enumerate(walkin_orders.iterrows()):
            col_idx = idx % 3
            with cols[col_idx]:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.markdown(f"**#{row.get('Order ID')}**")
                    
                    with c2:
                        # ✏️ EDIT BUTTON - Triggers Sidebar Population
                        if st.button(icon=":material/edit:", label="" , key=f"edit_{row['Order ID']}", help="Edit in Sidebar", width='stretch'):
                            st.session_state["selected_row_to_edit"] = row
                            show_edit_dialog(row,row['Order ID'])
                            
                    with c3:
                        if st.button(icon=":material/delete:", label="", key=f"del_{row['Order ID']}", help="Delete Order", width='stretch'):
                            show_delete_dialog(row['Order ID'])

                    raw_date = str(row.get('Delivery Date'))
                    raw_date = raw_date[8:10] + "/" + raw_date[5:7] + "/" + raw_date[0:4]
                    st.caption(f"{raw_date}")
                    st.caption(f"{row.get('Delivery Time')}")
                    st.markdown(f"### {row.get('Customer Name', 'Unknown')}")
                    st.markdown(f"{row.get('Customer Contact', '-')}")
                    st.markdown("---")
                    
                    # 1. Cleanly pull the text, handling Pandas Series or missing objects safely
                    raw_items = row.get('Items', '')
                    
                    # Handle cases where Pandas accidentally packages it as a Series/Object array
                    if hasattr(raw_items, "to_string") or not isinstance(raw_items, (str, int, float)):
                        try:
                            # Convert a pandas Series or row subset back to pure scalar data
                            raw_items = str(raw_items.values[0]) if hasattr(raw_items, "values") else str(raw_items)
                        except:
                            raw_items = str(raw_items)
                    else:
                        raw_items = str(raw_items)

                    # 2. Clean out dirty data artifacts or empty spaces
                    raw_items_clean = raw_items.strip()
                    if pd.isna(raw_items) or raw_items_clean.lower() in ["nan", "none", ""]:
                        items_text = "No items selected"
                    else:
                        # 3. Format into structured markdown list items cleanly
                        # Standardize old formats using commas to clean newlines first
                        formatted_text = raw_items_clean.replace(",\n", "\n").replace(",", "\n")
                        
                        # Build structural markdown bullet strings row by row
                        lines = [f"- {line.strip().lstrip('- ')}" for line in formatted_text.split('\n') if line.strip()]
                        items_text = "\n".join(lines)
                        
                    # 4. Render clean on your layout card
                    st.markdown(f"**Items:**\n{items_text}")
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
        st.info("Complete orders to see them here!")

    elif "Status" in df.columns:
        completed_orders = df[df["Status"] == "completed"]
        
        if completed_orders.empty:
            st.info("Complete orders to see them here!")

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
                            if st.button(icon=":material/arrow_back:", label="" , key=f"back_{row['Order ID']}", help="Return to Work Queue", width='stretch'):
                                show_return_to_work_queue_dialog(row['Order ID']);

                        st.markdown(f"### {row.get('Customer Name', 'Unknown')}")
                        st.markdown(f"{row.get('Customer Contact', '-')}")
                        st.markdown("---")
                        
                        # 1. Cleanly pull the text, handling Pandas Series or missing objects safely
                        raw_items = row.get('Items', '')
                        # Handle cases where Pandas accidentally packages it as a Series/Object array
                        if hasattr(raw_items, "to_string") or not isinstance(raw_items, (str, int, float)):
                            try:
                                # Convert a pandas Series or row subset back to pure scalar data
                                raw_items = str(raw_items.values[0]) if hasattr(raw_items, "values") else str(raw_items)
                            except:
                                raw_items = str(raw_items)
                        else:
                            raw_items = str(raw_items)

                        # 2. Clean out dirty data artifacts or empty spaces
                        raw_items_clean = raw_items.strip()
                        if pd.isna(raw_items) or raw_items_clean.lower() in ["nan", "none", ""]:
                            items_text = "No items selected"
                        else:
                            # 3. Format into structured markdown list items cleanly
                            # Standardize old formats using commas to clean newlines first
                            formatted_text = raw_items_clean.replace(",\n", "\n").replace(",", "\n")
                            
                            # Build structural markdown bullet strings row by row
                            lines = [f"- {line.strip().lstrip('- ')}" for line in formatted_text.split('\n') if line.strip()]
                            items_text = "\n".join(lines)
                            
                        # 4. Render clean on your layout card
                        st.markdown(f"**Items:**\n{items_text}")
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
        # 1. Clean the DataFrame columns right before processing to remove duplicate references
        # This keeps the first occurrence of any column name and drops the extra invisible ones
        df_clean = df.loc[:, ~df.columns.duplicated()]
        
        # 2. Filter for completed orders using our clean reference
        completed = df_clean[df_clean["Status"] == "completed"]
        
        if not completed.empty:
            st.subheader("Daily Revenue Trend")
            
            # Make sure Date and Cost columns exist cleanly as text/numbers
            daily = completed.groupby("Date")["Cost"].sum().reset_index()
            st.bar_chart(daily, x="Date", y="Cost", color="#90EE90")
            
            st.subheader("Order History")
            
            # 3. Safely slice your target history view without crashing
            history_view = completed[["Date", "Order ID", "Customer Name", "Items", "Cost"]]
            
            st.dataframe(
                history_view,
                use_container_width=True, # Note: 'width=stretch' is updated to modern Streamlit syntax
                hide_index=True
            )
        else:
            st.info("Complete some orders to see your analytics!")
