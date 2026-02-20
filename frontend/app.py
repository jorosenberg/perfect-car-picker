import streamlit as st
import pandas as pd
import plotly.express as px
import os
import requests
import json
from logic import load_data, CarRecommender, CostCalculator, ResaleModel, AIAdvisor

# Page Config
st.set_page_config(page_title="Perfect Car Picker", layout="wide")

# --- CLOUD INTEGRATION CHECK ---
API_URL = os.getenv("API_URL") # Injected by Terraform User Data

# --- INITIALIZE SESSION STATE ---
if 'deal_car' not in st.session_state:
    st.session_state.deal_car = None
if 'comparison_list' not in st.session_state:
    st.session_state.comparison_list = []

@st.cache_data
def get_cached_data():
    return load_data()

# --- REMOTE CALCULATION HELPER ---
def get_tco_result(car_row, inputs, resale_model_local=None):
    """
    Decides whether to calculate locally or use AWS Lambda API.
    """
    if API_URL:
        # Cloud Mode
        try:
            payload = {
                "car_data": car_row.to_dict(),
                "inputs": inputs
            }
            response = requests.post(API_URL, json=payload, timeout=5)
            if response.status_code == 200:
                result = response.json()
                result['source'] = "⚡ AWS Lambda" 
                return result
            else:
                return CostCalculator.calculate_tco(car_row, inputs, resale_model_local)
        except Exception:
            return CostCalculator.calculate_tco(car_row, inputs, resale_model_local)
    else:
        # Local Mode
        return CostCalculator.calculate_tco(car_row, inputs, resale_model_local)

# --- LOAD DATA & MODELS ---
df_full = get_cached_data()

if df_full.empty:
    st.warning("⚠️ Database not found. Please run `init_db.py`.")
    st.stop()

# Initialize ML Models
recommender_global = CarRecommender(df_full)
resale_model_global = ResaleModel(df_full) 

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

# --- SIDEBAR: SYSTEM SETTINGS ---
st.sidebar.divider()
st.sidebar.header("🛠️ System")
if st.sidebar.button("🔄 Refresh Database Cache", help="Clears local cache and forces the backend to fetch fresh database records."):
    if API_URL:
        with st.spinner("Refreshing backend database..."):
            try:
                requests.post(API_URL, json={"action": "refresh"}, timeout=15)
                st.sidebar.success("Backend refreshed!")
            except Exception as e:
                st.sidebar.error("Failed to reach backend API.")
    
    st.cache_data.clear()
    st.rerun()

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
                monthly_equiv = yearly_cap / 12
                est_ops = 250
                avail_pmt = max(0, monthly_equiv - est_ops)
                calc_budget = avail_pmt * 55
                st.caption(f"👀 Estimating vehicles priced around **${calc_budget:,.0f}**")
            
            st.markdown("### 2. Primary Use")
            usage_options = {"Daily Commute (Sedan/Hatch)": "Sedan", "Family Hauling (SUV)": "SUV", "Towing / Work (Pickup)": "Pickup", "Weekend Fun (Sports)": "Sports", "I don't know / Best Value": "Any"}
            usage_choice = st.selectbox("Usage?", options=list(usage_options.keys()))
            target_class = usage_options[usage_choice]

            st.markdown("### 3. Ownership")
            years_ownership = st.slider("Keep car for (Years)", 1, 15, 5)

            st.markdown("### 4. Luxury & Comfort")
            lux_choice = st.select_slider("Luxury Level", options=["Economy/Basic", "Standard/Mid", "Luxury/Premium"], value="Standard/Mid")
            lux_map = {"Economy/Basic": 3, "Standard/Mid": 6, "Luxury/Premium": 9}
            target_luxury = lux_map[lux_choice]

        with col_q2:
            st.markdown("### 5. Fuel & Driving")
            fuel_choices = st.multiselect("Fuel Type (Select all that apply)", ["Gas", "Hybrid", "Electric"], default=["Gas", "Hybrid", "Electric"])
            
            with st.expander("📏 Detailed Driving Habits", expanded=False):
                commute_dist = st.number_input("Daily Commute (Round Trip)", 0, 200, 20)
                days_week = st.slider("Commute Days/Week", 0, 7, 5)
                commute_type = st.select_slider("Commute Type", options=["Mostly City", "Mixed", "Mostly Highway"], value="Mixed")
                road_trip_miles = st.number_input("Annual Road Trip Miles", 0, 10000, 1000)
                other_miles = st.number_input("Weekly Errand Miles", 0, 500, 50)
                st.markdown("**Environment**")
                env_climate = st.select_slider("Climate", options=["Moderate", "Cold (Winter)", "Hot (Summer)"], value="Moderate")
                env_terrain = st.select_slider("Terrain", options=["Flat", "Hilly", "Mountainous"], value="Flat")

            st.markdown("### 6. Capability & Tech")
            c1, c2 = st.columns(2)
            with c1:
                # NEW SEAT COUNT SLIDER
                seats_needs = st.select_slider("Passenger Capacity", options=[2, 4, 5, 6, 7, 8], value=5)
            with c2:
                terrain_choice = st.select_slider("Off-Road", options=["City/Paved", "Bumpy/Gravel", "Off-Road"], value="City/Paved")
                terrain_map = {"City/Paved": 2, "Bumpy/Gravel": 6, "Off-Road": 9}
                target_offroad = terrain_map[terrain_choice]
            
            pax_needs = st.select_slider("Legroom", options=["Compact", "Standard", "Spacious"])
            perf_needs = st.select_slider("Speed", options=["Standard", "Peppy", "Fast"])
            assist_needs = st.radio("Assist Level?", ["Basic", "Mid (Lane Keep)", "Advanced (Hands-Free)"], index=1)
            feature_options = ["Apple CarPlay", "Android Auto", "Leather", "Sunroof", "AWD", "Heated Seats", "Autopilot", "3rd Row", "Tow Package"]
            desired_features = st.multiselect("Must-Haves:", feature_options)

            st.markdown("### 7. Top Priority")
            priority = st.selectbox("What matters most to you?", ["Balanced (Value)", "Lowest Total Cost", "Performance (Speed)", "Utility (Cargo)", "Tech & Safety"])

        submitted = st.form_submit_button("🔍 Analyze & Find Matches")

    if submitted:
        st.divider()
        st.subheader("Recommended for You")
        
        if not fuel_choices:
            st.error("Please select at least one Fuel Type.")
        else:
            df_filtered = df_full[df_full['fuel_type'].isin(fuel_choices)].copy()
            
            if df_filtered.empty:
                st.warning(f"No cars found matching fuel types: {', '.join(fuel_choices)}")
            else:
                recommender_local = CarRecommender(df_filtered)
                
                if "Electric" in fuel_choices: target_mpg = 110
                elif "Hybrid" in fuel_choices: target_mpg = 50
                else: target_mpg = 25

                target_legroom = 40.0 if pax_needs == "Spacious" else 36.0
                target_accel = 4.5 if perf_needs == "Fast" else 7.5
                target_assist = 9.0 if "Advanced" in assist_needs else 6.0
                
                target_price_final = calc_budget
                target_cargo_final = 30.0
                
                if priority == "Lowest Total Cost": target_price_final = calc_budget * 0.9 
                elif priority == "Performance (Speed)": target_accel = max(3.0, target_accel - 1.5)
                elif priority == "Utility (Cargo)": target_cargo_final = 50.0 
                elif priority == "Tech & Safety": target_assist = 9.5
                    
                user_prefs = {
                    'price': target_price_final, 'class': target_class, 
                    'fuel_type': 'Any', 
                    'city_mpg': target_mpg, 'reliability_score': 8.0, 'luxury_score': target_luxury,
                    'rear_legroom': target_legroom, 'acceleration': target_accel,
                    'cargo_space': target_cargo_final, 'driver_assist_score': target_assist,
                    'offroad_capability': target_offroad,
                    'seats': seats_needs # Added to prefs
                }
                
                try:
                    recs = recommender_local.recommend(user_prefs)
                    
                    tco_inputs = {
                        'years': years_ownership, 
                        'gas_price': gas_price, 
                        'elec_price': elec_price,
                        'elec_price_road': elec_price_fast,
                        'method': global_method, 'apr': global_apr, 'term': global_term, 'down_payment': global_down,
                        'commute_dist': commute_dist, 'days_week': days_week, 'commute_type': commute_type,
                        'road_trip_miles': road_trip_miles, 'other_miles': other_miles,
                        'climate': env_climate, 'terrain': env_terrain,
                        'driver_age': driver_age_est
                    }
                    
                    results = []
                    for idx, row in recs.iterrows():
                        costs = get_tco_result(row, tco_inputs, resale_model_local=resale_model_global)
                        car_data = row.to_dict()
                        car_data.update(costs)
                        car_data['Monthly Cash Flow'] += total_subs
                        car_data['Monthly True Cost'] += total_subs
                        
                        car_features = [f.strip() for f in car_data['features'].split(',')]
                        matches = [f for f in desired_features if any(f.lower() in feat.lower() for feat in car_features)]
                        car_data['match_count'] = len(matches)
                        car_data['matched_features'] = ", ".join(matches)
                        results.append(car_data)
                    
                    sort_cols = ["match_count", "Monthly True Cost"]
                    sort_asc = [False, True]
                    
                    if priority == "Performance (Speed)":
                        sort_cols = ["match_count", "acceleration", "Monthly True Cost"]
                        sort_asc = [False, True, True] 
                    elif priority == "Utility (Cargo)":
                        sort_cols = ["match_count", "cargo_space", "Monthly True Cost"]
                        sort_asc = [False, False, True]
                    elif priority == "Tech & Safety":
                        sort_cols = ["match_count", "driver_assist_score", "Monthly True Cost"]
                        sort_asc = [False, False, True] 
                    
                    results_df = pd.DataFrame(results).sort_values(by=sort_cols, ascending=sort_asc)
                    
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=results_df.to_csv(index=False).encode('utf-8'),
                        file_name='autoinvest_recommendations.csv',
                        mime='text/csv',
                    )
                    
                    for idx, row in results_df.iterrows():
                        cost_label = "Monthly Pmt" if global_method != 'Cash' else "Monthly TCO"
                        cost_val = row['Monthly Payment'] if global_method != 'Cash' else row['Monthly True Cost']
                        
                        with st.expander(f"{row['year']} {row['make']} {row['model']} | {cost_label}: ${cost_val:.0f}", expanded=True):
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("Price", f"${row['price']:,.0f}")
                            c2.metric("Monthly Flow", f"${row['Monthly Cash Flow']:.0f}", help="Pmt + Fuel + Ins + Maint + Subs")
                            c3.metric("Real-World MPG", f"{row['Est MPG']}", help="Weighted by driving habits & climate")
                            c4.metric("Seats", f"{row['seats']}") # Display Seats
                            
                            if 'source' in row and 'AWS' in row['source']:
                                st.caption(f"⚡ Calculated via {row['source']}")

                            # AI PITCH BUTTON
                            if st.button(f"🤖 Why buy this {row['model']}?", key=f"ai_{idx}"):
                                with st.spinner("Consulting AI Advisor (Bedrock)..."):
                                    pitch = AIAdvisor.get_car_pitch(row, priority)
                                    st.info(pitch)

                            if st.button(f"💰 Deep Dive Analysis", key=f"btn_{idx}"):
                                st.session_state.deal_car = f"{row['make']} {row['model']} ({row['year']})"
                                st.success(f"Car selected! Go to the 'Deal Analyzer' tab.")

                except Exception as e:
                    st.error(f"Error: {str(e)}")

# === TAB 2: COMPARE ===
with tab2:
    st.subheader("Head-to-Head Spec Comparison")
    
    if df_full.empty:
        st.error("No data available.")
    else:
        df_display = df_full.copy()
        df_display['display_name'] = df_display['make'] + " " + df_display['model'] + " (" + df_display['year'].astype(str) + ")"
        
        custom_deals = []
        if 'comparison_list' in st.session_state:
            for i, deal in enumerate(st.session_state.comparison_list):
                deal_name = f"DEAL: {deal['make']} {deal['model']} - ${deal.get('price', 0):,.0f}"
                deal['display_name'] = deal_name
                custom_deals.append(deal)
        
        std_options = df_display['display_name'].tolist()
        deal_options = [d['display_name'] for d in custom_deals]
        all_options = deal_options + std_options 
        
        compare_selection = st.multiselect("Select Vehicles to Compare (Max 4)", all_options, max_selections=4)
        
        if compare_selection:
            rows_to_display = []
            
            for sel in compare_selection:
                if sel in deal_options:
                    found_deal = next(d for d in custom_deals if d['display_name'] == sel)
                    rows_to_display.append(found_deal)
                else:
                    row = df_display[df_display['display_name'] == sel].iloc[0].to_dict()
                    rows_to_display.append(row)
            
            comp_df = pd.DataFrame(rows_to_display)
            
            st.markdown("### Vehicle Specifications")
            base_cols = ['make', 'model', 'price', 'city_mpg', 'hwy_mpg', 'acceleration', 'cargo_space', 'rear_legroom', 'seats', 'reliability_score']
            tco_cols = ['Monthly Payment', 'Monthly True Cost', 'Resale Value']
            present_cols = [c for c in tco_cols if c in comp_df.columns]
            final_cols = ['display_name'] + base_cols + present_cols
            
            comp_display = comp_df[final_cols].set_index('display_name').transpose()
            st.dataframe(comp_display.astype(str))
            
            st.markdown("### Interactive Performance Chart")
            fig = px.scatter(comp_df, x='price', y='acceleration', color='make', size='city_mpg', hover_data=['model'], title="Price vs Speed (Size = MPG)")
            st.plotly_chart(fig, use_container_width=True)
                
        else:
            st.info("Select vehicles above to see a side-by-side comparison.")
    
# === TAB 4: DEAL ANALYZER (NEW) ===
with tab4:
    st.header("💰 Detailed Cost & Deal Analyzer")
    
    if df_full.empty:
        st.error("No cars loaded.")
    else:
        car_options = list(df_full['make'] + " " + df_full['model'] + " (" + df_full['year'].astype(str) + ")")
        
        default_ix = 0
        if st.session_state.deal_car and st.session_state.deal_car in car_options:
            default_ix = car_options.index(st.session_state.deal_car)
        
        selected_car_str = st.selectbox("Select Vehicle", car_options, index=default_ix)
        
        make, model_raw = selected_car_str.split(" ", 1)
        model = model_raw.split(" (")[0]
        car_row = df_full[(df_full['make'] == make) & (df_full['model'] == model)].iloc[0]
        
        st.divider()
        
        col_fin1, col_fin2 = st.columns([1, 2])
        
        with col_fin1:
            st.subheader("1. Deal Settings")
            deal_method = st.radio("Buying Method", ["Cash", "Finance", "Lease"])
            
            price_input = st.number_input("Negotiated Price ($)", value=int(car_row['price']), step=500)
            
            st.markdown("**Insurance Override**")
            custom_ins = st.number_input("Custom Quote ($/Month)", 0, 1000, 0, help="Leave 0 to use estimate")
            
            analysis_years = 5 
            if deal_method != "Lease":
                analysis_years = st.number_input("Analysis Duration (Years)", min_value=1, max_value=15, value=5, step=1)
            
            user_fin_inputs = {
                'years': analysis_years, 'annual_miles': 12000, 
                'gas_price': gas_price, 
                'elec_price': elec_price,
                'elec_price_road': elec_price_fast, 
                'method': deal_method,
                'custom_insurance': custom_ins,
                'driver_age': driver_age_est
            }
            
            car_row_calc = car_row.copy()
            car_row_calc['price'] = price_input
            
            if deal_method == "Finance":
                user_apr = st.number_input("APR (%)", value=6.0, step=0.1)
                user_term = st.number_input("Loan Term (Months)", value=60, step=12)
                user_down = st.number_input("Down Payment ($)", value=2000, step=500)
                user_fin_inputs.update({'apr': user_apr, 'term': user_term, 'down_payment': user_down})
                
            elif deal_method == "Lease":
                st.markdown("[Open Leasehackr Calculator ↗](https://leasehackr.com/calculator)")
                lease_mode = st.radio("Input Type", ["Effective Monthly Cost", "Detailed Components"])
                
                if lease_mode == "Detailed Components":
                    l_monthly = st.number_input("Monthly Payment ($)", value=500, step=10)
                    l_due = st.number_input("Due at Signing ($)", value=2000, step=100)
                    l_term = st.number_input("Lease Term (Months)", value=36, step=12)
                    user_fin_inputs.update({'lease_monthly': l_monthly, 'lease_due': l_due, 'lease_term': l_term})
                else:
                    l_eff = st.number_input("Effective Monthly Cost ($)", value=600, step=10)
                    l_term = st.number_input("Lease Term (Months)", value=36, step=12)
                    user_fin_inputs.update({'lease_monthly': l_eff, 'lease_due': 0, 'lease_term': l_term})
                
                user_fin_inputs['years'] = l_term / 12

        costs = get_tco_result(car_row_calc, user_fin_inputs, resale_model_local=resale_model_global)
        
        costs['Monthly Cash Flow'] += total_subs
        costs['Monthly True Cost'] += total_subs
        
        with col_fin2:
            st.subheader("2. Cost Breakdown")
            
            total_label = "Total Period"
            if deal_method == "Lease":
                term = int(user_fin_inputs.get('lease_term', 36))
                total_label = f"Total ({term} Mos)"
            else:
                total_label = f"Total ({analysis_years} Yrs)"
                
            view_mode = st.radio("Timeframe", ["Monthly", "Yearly", total_label], horizontal=True)
            show_dep = st.checkbox("Include Depreciation in Total?", value=False)
            
            if view_mode == "Yearly":
                mult = 12
            elif view_mode == total_label:
                if deal_method == "Lease":
                    mult = user_fin_inputs.get('lease_term', 36)
                else:
                    mult = analysis_years * 12
            else:
                mult = 1
                
            m1, m2, m3 = st.columns(3)
            
            if show_dep:
                display_cost = costs['Monthly True Cost'] * mult
                subtext = "Includes Dep/Equity Loss"
            else:
                base_flow = costs['Monthly Cash Flow'] * mult
                if view_mode == total_label:
                    display_cost = base_flow + costs['Upfront Cost']
                    subtext = "Cash Flow + Upfront"
                else:
                    display_cost = base_flow
                    subtext = "Running Cash Flow"
            
            m1.metric(f"Cost ({view_mode})", f"${display_cost:,.2f}", delta=subtext)
            m2.metric("Payment Portion", f"${costs['Monthly Payment'] * mult:,.2f}")
            m3.metric("Running Costs", f"${(costs['Monthly Fuel'] + costs['Monthly Ins'] + costs['Monthly Maint']) * mult:,.2f}")
            
            st.divider()
            
            if st.button("➕ Add this Configured Deal to Comparison", type="primary"):
                deal_snapshot = car_row_calc.to_dict()
                deal_snapshot.update(costs)
                deal_snapshot['is_deal'] = True
                st.session_state.comparison_list.append(deal_snapshot)
                st.success(f"Added {deal_snapshot['make']} {deal_snapshot['model']} deal to Compare tab!")
            
            st.divider()
            m4, m5, m6 = st.columns(3)
            
            if deal_method != "Lease":
                m4.metric(f"Value after {analysis_years} yrs", f"${costs['Resale Value']:,.0f}", delta="Est. Resale Price")
            else:
                m4.metric("Residual Value", "N/A (Lease)", delta="Return to Dealer")
                
            avg_yearly = costs['Monthly True Cost'] * 12
            m5.metric("Avg Cost / Year", f"${avg_yearly:,.0f}", help="Total True Cost / Years")
            
            st.divider()
            
            val_pay = costs['Monthly Payment'] * mult
            val_fuel = costs['Monthly Fuel'] * mult
            val_ins = costs['Monthly Ins'] * mult
            val_maint = costs['Monthly Maint'] * mult
            val_dep = costs['Monthly Dep'] * mult
            val_subs = total_subs * mult
            
            breakdown_data = {
                "Cost Component": ["Vehicle Payment", "Fuel / Charging", "Insurance", "Maintenance", "Subscriptions", "Depreciation (Hidden)"],
                f"Cost ({view_mode})": [val_pay, val_fuel, val_ins, val_maint, val_subs, val_dep]
            }
            
            if view_mode == total_label and costs['Upfront Cost'] > 0:
                breakdown_data["Cost Component"].append("Upfront Due")
                breakdown_data[f"Cost ({view_mode})"].append(costs['Upfront Cost'])

            bd_df = pd.DataFrame(breakdown_data)
            
            st.dataframe(bd_df.style.format({f"Cost ({view_mode})": "${:,.2f}"}))
            st.bar_chart(bd_df.set_index("Cost Component"))