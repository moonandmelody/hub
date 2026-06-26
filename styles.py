import streamlit as st

# --- 🎨 BRAND ASSETS ---
# Replace this link with your actual logo if you have one hosted online
LOGO_URL = "https://cdn-icons-png.flaticon.com/512/3222/3222642.png"

# --- 🎨 COLOR PALETTE ---
# You can change these hex codes to match your brand!
PRIMARY_COLOR = "#F6F0EA"       # (Navy) 
SECONDARY_COLOR = "#AC7E44"     # (Gold) 
BACKGROUND_COLOR = "#061627"    # (Ivory)
SIDEBAR_COLOR = "#AC7E44"       # (Gold) 
TEXT_COLOR = "#F6F0EA"          # (Navy)
#SIDEBAR_COLOR = "#C9A3A3"       # (Rose) 
#TEXT_COLOR = "#6B4F4F"          # (Brown)

# --- 🎨 CSS INJECTOR FUNCTION ---
def apply_custom_css():
    st.markdown(f"""
        <style>
            /* 1. IMPORT GOOGLE FONT (Cinzel) */
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@100;200;300;400;600&display=swap');
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@100;200;300;400;600&display=swap');

            html, body, [class*="css"] {{
                font-family: 'Cinzel', serif;
                color: {TEXT_COLOR};
            }}

            /* 2. SIDEBAR STYLING */
            [data-testid="stSidebar"] {{
                background-color: {SIDEBAR_COLOR};
                border-right: 1px solid {SIDEBAR_COLOR};
            }}

            /* 3. BUTTON STYLING */
            .stButton > button {{
                background-color: {PRIMARY_COLOR};
                color: white;
                border-radius: 8px;
                border: none;
                padding: 10px 20px;
                font-weight: 600;
                transition: all 0.3s ease;
            }}
            .stButton > button:hover {{
                background-color: {PRIMARY_COLOR};
                transform: scale(1.02);
                color: white;
            }}

            /* 4. METRIC CARDS (Top Numbers) */
            [data-testid="stMetric"] {{
                background-color: white;
                padding: 15px;
                border-radius: 10px;
                box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
                text-align: center;
                border: 1px solid {PRIMARY_COLOR};
            }}
            [data-testid="stMetricLabel"] {{
                color: #888;
                font-size: 14px;
            }}
            [data-testid="stMetricValue"] {{
                color: {PRIMARY_COLOR};
                font-size: 28px;
                font-weight: 700;
            }}

            /* 5. POST-IT NOTE CARDS (Containers) */
            [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {{
                /* This targets the cards in your grid */
            }}
            
            /* Make the containers look like nice cards */
            div[data-testid="stContainer"] {{
                background-color: white;
                border-radius: 12px;
                padding: 20px;
                border: 1px solid #E8E8E8;
                box-shadow: 0 2px 5px rgba(0,0,0,0.02);
            }}

            /* 6. TAB STYLING */
            .stTabs [data-baseweb="tab-list"] {{
                gap: 20px;
            }}
            .stTabs [data-baseweb="tab"] {{
                height: 50px;
                white-space: pre-wrap;
                background-color: white;
                border-radius: 5px;
                color: #555;
                font-weight: 600;
            }}
            .stTabs [aria-selected="true"] {{
                background-color: {PRIMARY_COLOR} !important;
                color: white !important;
            }}

        </style>
    """, unsafe_allow_html=True)
