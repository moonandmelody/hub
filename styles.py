import streamlit as st
import random

# --- 🎨 BRAND ASSETS ---
# Replace this link with your actual logo if you have one hosted online
LOGO_URL = "https://cdn-icons-png.flaticon.com/512/3222/3222642.png"

# --- 🎨 COLOR PALETTE ---
# You can change these hex codes to match your brand!
PRIMARY_COLOR = "#F6F0EA"       # (Ivory) 
SECONDARY_COLOR = "#AC7E44"     # (Gold) 
BACKGROUND_COLOR = "#061627"    # (Navy)
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
                background-color: {PRIMARY_COLOR};
            }}
            #moon-and-melody-dashboard {{
                display: flex;
                justify-content: center;
                font-family: 'Cinzel', serif;
                padding: 30px 20px !important;
            }}

            /* 2. SIDEBAR STYLING */
            [data-testid="stSidebar"] {{
                background-color: {SIDEBAR_COLOR};
                border-right: 1px solid {SIDEBAR_COLOR};
                width:460px !important;
            }}

            [data-testid="stNumberInputField"] {{
                height: 40px;
            }}

            h3 {{
                font-size: 35px !important;
            }}
            
            h5 {{
                font-size: 30px !important;
            }}

            .st-emotion-cache-1bf0olv > p {{
                font-family: 'Montserrat',serif;
                color: white;
            }}
            .st-emotion-cache-6v4t1a {{
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.7);
            }}

            [data-testid="stNumberInputContainer"] {{
                width: 200px;
                border: none !important;
            }}

            [data-testid="stTextInputRootElement"] {{
                width: 350px;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.7);
                border: none !important;
            }}

            h1 {{
                padding: 12px 0px !important;
                font-size: 30px !important;
            }}
            
            [data-testid="stBaseButton-secondary"] {{
                background-color: transparent;
                border: 1px solid {BACKGROUND_COLOR};
            }}

            .st-emotion-cache-194zssa > div {{
                justify-content: end;
            }}

            /* 3. BUTTON STYLING */
            
            .stButton > button {{
                background-color: {BACKGROUND_COLOR} !important;
                color: white;
                border-radius: 8px;
                border: none;
                padding: 10px 20px;
                font-weight: 600;
                transition: all 0.3s ease;
            }}
            
            .stButton > button:hover {{
                background-color: {BACKGROUND_COLOR};
                transform: scale(1.02);
                color: white;
            }}

            .st-emotion-cache-1cl4umz{{
                background-color: {BACKGROUND_COLOR};
                border: none;
            }}

            .st-emotion-cache-1cl4umz:hover{{
                background-color: {BACKGROUND_COLOR};
                border: none;
            }}

            .st-emotion-cache-1cl4umz:focus-visible{{
                background-color: {BACKGROUND_COLOR};
                border: none;
                box-shadow: none;
            }}

            /* 4. METRIC CARDS (Top Numbers) */
            div [class="st-emotion-cache-0"] {{
                height:100%;
            }}
            [data-testid="stMetric"] {{
                background-color: {BACKGROUND_COLOR};
                padding: 15px;
                border-radius: 10px;
                box-shadow: 0px 4px 10px rgba(0,0,0,1);
                text-align: center;
                border: 1px solid {BACKGROUND_COLOR};
                width: 210px;
                height: 150px;
            }}
            [data-testid="stMetricLabel"] {{
                color: white;
                font-size: 14px;
                width:100%;
                display: flex;
                justify-content: center;
            }}
            [data-testid="stMarkdownContainer"]{{
                font-family: 'Cinzel', serif;
            }}
            [data-testid="stMetricValue"] {{
                color: {SECONDARY_COLOR};
                font-size: 25px !important;
                font-weight: 700;
                padding: 40px 10px 40px 10px;
                display: flex;
                justify-content: center;
            }}
            .st-emotion-cache-1ml8qm {{
                font-size: 15px;
            }}

            .st-emotion-cache-wt0xm9:nth-of-type(1) {{
                width: calc(33.3333% - 1rem) !important;
            }}

            .st-emotion-cache-wt0xm9:nth-of-type(2) {{
                width: calc(33.3333% - 1rem) !important;
            }}

            .st-emotion-cache-wt0xm9:nth-of-type(3) {{
                width: calc(33.3333% - 1rem) !important;
            }}

            .st-emotion-cache-wt0xm9:nth-of-type(1) > div {{
                width: auto !important;
            }}

            .st-emotion-cache-wt0xm9:nth-of-type(2) > div {{
                width: auto !important;
            }}

            .st-emotion-cache-wt0xm9:nth-of-type(3) > div {{
                width: auto !important;
            }}

            .st-key-allMetricDiv > div > div > div > div > div{{
                display: flex;
                justify-content: center;
            }}

            /* Filter Date */
            .stSelectbox:nth-of-type(3) {{
                    display: grid;
                    justify-content: end;
            }}

            /* 5. POST-IT NOTE CARDS (Containers) */
            [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {{
                /* This targets the cards in your grid */
            }}

            .st-emotion-cache-wt0xm9 {{
                width: 300px !important;
            }}

            .st-emotion-cache-wt0xm9 > div {{
                width: 300px !important;
            }}

            [data-testid="stCaptionContainer"] > p {{
                margin: 0px;
                font-size: 15px;
                color: {BACKGROUND_COLOR};
                font-family: 'Montserrat',serif;
                opacity: 1;
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
                color: {BACKGROUND_COLOR};
                font-weight: 600;
                width: 50%;
            }}
            .stTabs [aria-selected="true"] {{
                background-color: {PRIMARY_COLOR} !important;
                color: {BACKGROUND_COLOR} !important;
                width: 50%;
            }}

            .st-d7 {{
                background-color: transparent;
            }}

            /* Dialog box */
            [data-testid="stAlertContainer"]{{
                background-color: transparent;
            }}

            .st-emotion-cache-yhc2tm {{
                font-family: 'Montserrat',serif;
            }}

            /* Button hover or focus */
            .st-emotion-cache-5qfegl:focus-visible{{
                box-shadow: none;
            }}

            /* Confirmation Dialog Box */
            [data-testid="stDialog"] > div > div {{
                width: 1100px;
            }}

            [data-testid="stDialog"] > div > div > div {{
                justify-content: center;
            }}

            /* 8. BALLOON ANIMATION KEYFRAMES */
            @keyframes floatUp {{
                0% {{ transform: translateY(100vh) rotate(0deg); opacity: 1; }}
                50% {{ transform: translateY(100vh) rotate(20deg); opacity: 1; }}
                40% {{ transform: translateY(80vh) rotate(-40deg); opacity: 1; }}
                100% {{ transform: translateY(-120vh) rotate(0deg); opacity: 0.7; }}
            }}

        </style>
    """, unsafe_allow_html=True)

# --- 🎈 CUSTOM CELEBRATION FUNCTION ---
def celebrate():
    """Generates custom balloons in Brand Colors"""
    
    # HTML for a single balloon
    # We use a randomized left position and animation duration for natural movement
    balloon_html = ""
    colors = [PRIMARY_COLOR, SECONDARY_COLOR, BACKGROUND_COLOR] 
    
    for i in range(36): # Create 36 balloons
        left_pos = random.randint(5, 95)
        duration = random.uniform(3, 4)
        delay = random.uniform(0, 1)
        color = random.choice(colors)
        
        balloon_html += f"""
        <div style="
            position: fixed;
            bottom: -100px;
            left: {left_pos}%;
            width: 50px;
            height: 70px;
            background-color: {color};
            border-radius: 50%;
            opacity: 1;
            box-shadow: inset -5px -5px 10px rgba(0,0,0,0.8);
            animation: floatUp {duration}s ease-in forwards;
            animation-delay: {delay}s;
            z-index: 9999;
        ">
            <div style="
                position: absolute;
                bottom: -10px;
                left: 24px;
                width: 2px;
                height: 30px;
                background-color: rgba(0,0,0,1);
            "></div>
        </div>
        """
    
    # Inject the HTML into the app
    st.markdown(balloon_html, unsafe_allow_html=True)
