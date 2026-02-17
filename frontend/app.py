import streamlit as st
import pandas as pd
import plotly.express as px
import os
from logic import load_data, APIClient

# Genereated Boilerplate from backend with AWS infra

# Page Config
st.set_page_config(page_title="Perfect Car Picker", layout="wide")

# --- CONFIGURATION ---
API_URL = os.getenv("API_URL") # Injected by Terraform
if not API_URL:
    st.error("⚠️ API_URL environment variable is missing. The app cannot connect to the backend.")
    st.stop()

# Initialize Client
api_client = APIClient(API_URL)

# --- INITIALIZE SESSION STATE ---
if 'deal_car' not in st.session_state:
    st.session_state.deal_car = None
if 'comparison_list' not in st.session_state:
    st.session_state.comparison_list = []

@st.cache_data
def get_cached_data():
    return load_data()

# --- LOAD DATA (For UI Lists Only) ---
df_full = get_cached_data()

# Title and Intro
st.title("🚗 Perfect Car Picker")
st.markdown("""
**AI-Powered Vehicle Analysis & Financial Modeling**
Answer a few questions about your lifestyle, and our AI will calculate the **True Cost of Ownership** (including depreciation, fuel, and maintenance) to find your perfect match.
""")

# --- SIDEBAR: GLOBAL SETTINGS ---
st.sidebar.header("🌍 Market & Finance")

with st.sidebar.expander("⛽ Energy Prices", expanded=True):
    gas_price = st.number_input("Gas Price ($/gal)", value=3.50, step=0.10)
    elec_price = st.number_input("Home Electricity ($/kWh)", value=0.16, step=0.01)
    elec_price_fast = st.number_input("Fast Charging ($/kWh)", value=0.36, step=0.01, help="Cost for DC Fast Charging on road trips")

# --- SUBSCRIPTIONS ---
with st.sidebar.expander("💳 Monthly Subscriptions", expanded=True):
    charge_sub = st.number_input("Charging Network ($/mo)", value=0, help="e.g., Electrify America Pass+, Tesla Supercharger Membership")
    feature_sub = st.number_input("Vehicle Features ($/mo)", value=0, help="e.g., Tesla Autopilot/FSD, Hyundai BlueLink, GM OnStar")
    total_subs = charge_sub + feature_sub

# --- DRIVER PROFILE ---
with st.sidebar.expander("👤 Driver Profile", expanded=False):
    years_licensed = st.number_input("Years since getting license", 0, 80, 14, help="We use this to estimate insurance risk scaling.")
    driver_age_est = 16 + years_licensed

with st.sidebar.expander("🏦 Buying Strategy (Global)", expanded=False):
    st.caption("These settings apply to the recommendations below.")
    global_method = st.selectbox("Preferred Method", ["Cash", "Finance", "Lease"])
    
    global_apr = 6.0
    global_term = 60
    global_down = 2000
    
    if global_method == "Finance":
        global_apr = st.number_input("APR %", 0.0, 25.0, 6.0)
        global_term = st.number_input("Loan Term (Months)", 12, 96, 60, step=12)
        global_down = st.number_input("Down Payment ($)", 0, 50000, 2000, step=500)
    elif global_method == "Lease":
        st.info("Lease estimates are generic (1.2% of MSRP) in the main list. Use the 'Deal Analyzer' tab for specific quotes.")

# --- TABBED INTERFACE ---
tab1, tab2, tab4 = st.tabs(["💡 Help Me Choose", "📊 Compare Cars", "💰 Deal Analyzer"])

# === TAB 1: QUESTIONNAIRE & AI RECOMMENDATION ===
with tab1:
    st.subheader("Let's find your ideal car")
    
    with st.form("preference_form"):
        col_q1, col_q2 = st.columns(2)
        
        with col_q1:
            st.markdown("### 1. Financials")
            budget_type = st.radio("Budget Mode", ["Vehicle Price (Sticker)", "Monthly Total Budget (All-In)", "Yearly Total Budget (All-In)"], horizontal=False)
            
            if budget_type == "Vehicle Price (Sticker)":
                target_budget = st.slider("Max Vehicle Price ($)", 15000, 150000, 40000, step=1000)
                calc_budget = target_budget
            elif budget_type == "Monthly Total Budget (All-In)":
                monthly_cap = st.slider("Max Monthly Cost ($)", 300, 5000, 800, step=50, help="Includes Pmt, Ins, Fuel, Maint")
                est_ops = 250
                avail_pmt = max(0, monthly_cap - est_ops)
                calc_budget = avail_pmt * 55 
                st.caption(f"👀 Estimating vehicles priced around **${calc_budget:,.0f}**")
            else: 
                yearly_cap = st.slider("Max Yearly Cost ($)", 4000, 36000, 10000, step=500)