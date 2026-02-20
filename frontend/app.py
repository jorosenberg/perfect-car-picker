import streamlit as st
import pandas as pd
import plotly.express as px
import os
from logic import load_data, APIClient

st.set_page_config(page_title="Perfect Car Picker", layout="wide")

API_URL = os.getenv("API_URL")
if not API_URL:
    st.error("⚠️ API_URL environment variable is missing. The app cannot connect to the backend.")

api_client = APIClient(API_URL)

if 'deal_car' not in st.session_state:
    st.session_state.deal_car = None
if 'comparison_list' not in st.session_state:
    st.session_state.comparison_list = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'pitch_map' not in st.session_state:
    st.session_state.pitch_map = {}

@st.cache_data(show_spinner="⏳ Loading vehicles from Backend API...")
def get_cached_data():
    return load_data(API_URL)

df_full = get_cached_data()

# Title and Intro
st.title("🚗 Perfect Car Picker")

if len(df_full) > 10:
    st.success(f"✅ **Live Database Connected!** Loaded {len(df_full)} vehicles from API.")
else:
    st.error(f"🔌 **Live Database Connection Failed!** Displaying {len(df_full)} offline fallback vehicles. Please reload database if first time app startup.")
    st.info("Click **'Force Data Refresh'** in the sidebar below to try reconnecting to the database.")

st.markdown("""
**AI-Powered Vehicle Analysis & Financial Modeling**
Answer a few questions about your lifestyle, and our AI will calculate the **True Cost of Ownership** (including depreciation, fuel, and maintenance) to find your perfect match.
""")

st.sidebar.header("🌍 Market & Finance")

with st.sidebar.expander("⛽ Energy Prices", expanded=True):
    gas_price = st.number_input("Gas Price ($/gal)", value=3.50, step=0.10)
    elec_price = st.number_input("Home Electricity ($/kWh)", value=0.16, step=0.01)
    elec_price_fast = st.number_input("Fast Charging ($/kWh)", value=0.36, step=0.01, help="Cost for DC Fast Charging on road trips")

with st.sidebar.expander("💳 Monthly Subscriptions", expanded=True):
    charge_sub = st.number_input("Charging Network ($/mo)", value=0, help="e.g., Electrify America Pass+, Tesla Supercharger Membership")
    feature_sub = st.number_input("Vehicle Features ($/mo)", value=0, help="e.g., Tesla Autopilot/FSD, Hyundai BlueLink, GM OnStar")
    total_subs = charge_sub + feature_sub

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

st.sidebar.divider()
st.sidebar.header("🛠️ System")
if st.sidebar.button("🔄 Force Data Refresh", help="Clears the cached fallback data and forces a fresh connection to the database."):
    st.cache_data.clear()
    st.rerun()

tab1, tab2, tab4 = st.tabs(["💡 Help Me Choose", "📊 Compare Cars", "💰 Deal Analyzer"])

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

            st.markdown("### 4. Luxury, Comfort & Fun")
            lux_choice = st.select_slider("Luxury Level", options=["Economy/Basic", "Standard/Mid", "Luxury/Premium"], value="Standard/Mid")
            lux_map = {"Economy/Basic": 3, "Standard/Mid": 6, "Luxury/Premium": 9}
            target_luxury = lux_map[lux_choice]
            
            fun_choice = st.select_slider("Fun Factor (Driving Dynamics)", options=["Practical", "Engaging", "Thrilling (Sports)"], value="Engaging")
            fun_map = {"Practical": 3, "Engaging": 6, "Thrilling (Sports)": 10}
            target_fun = fun_map[fun_choice]

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
                seats_needs = st.select_slider("Passenger Capacity", options=[2, 4, 5, 6, 7, 8], value=5)
                pax_needs = st.select_slider("Legroom", options=["Compact", "Standard", "Spacious"])
                
            with c2:
                terrain_choice = st.select_slider("Off-Road", options=["City/Paved", "Bumpy/Gravel", "Off-Road"], value="City/Paved")
                terrain_map = {"City/Paved": 2, "Bumpy/Gravel": 6, "Off-Road": 9}
                target_offroad = terrain_map[terrain_choice]
                perf_needs = st.select_slider("Speed", options=["Standard", "Peppy", "Fast"])

            assist_needs = st.radio("Assist Level?", ["Basic", "Mid (Lane Keep)", "Advanced (Hands-Free)"], index=1)
            feature_options = ["Apple CarPlay", "Android Auto", "Leather", "Sunroof", "AWD", "Heated Seats", "Autopilot", "3rd Row", "Tow Package"]
            desired_features = st.multiselect("Must-Haves:", feature_options)

            st.markdown("### 7. Top Priority")
            priority = st.selectbox("What matters most to you?", ["Balanced (Value)", "Lowest Total Cost", "Performance (Speed)", "Utility (Cargo)", "Tech & Safety"])

        submitted = st.form_submit_button("🔍 Analyze & Find Matches")

    if submitted:
        if not fuel_choices:
            st.error("Please select at least one Fuel Type.")
        else:
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
                'city_mpg': target_mpg, 'reliability_score': 8.0, 
                'luxury_score': target_luxury, 'fun_score': target_fun,
                'rear_legroom': target_legroom, 'acceleration': target_accel,
                'cargo_space': target_cargo_final, 'driver_assist_score': target_assist,
                'offroad_capability': target_offroad,
                'seats': seats_needs
            }
            
            with st.spinner("Finding matches via AWS Lambda..."):
                recs_df = api_client.get_recommendations(user_prefs)

            if recs_df.empty:
                st.warning("No matches found from API.")
                st.session_state.search_results = None
            else:
                recs_df = recs_df[recs_df['fuel_type'].isin(fuel_choices)]
                
                recs_df = recs_df[recs_df['price'] <= calc_budget]
                
                if target_class != "Any":
                    recs_df = recs_df[recs_df['class'] == target_class]
                
                if desired_features:
                    feature_aliases = {
                        "Apple CarPlay": ["carplay", "apple carplay", "apple"],
                        "Android Auto": ["android auto", "android"],
                        "Leather": ["leather", "nappa", "vernasca", "startex"],
                        "Sunroof": ["sunroof", "moonroof", "panoramic", "solar roof", "glass roof"],
                        "AWD": ["awd", "4wd", "all-wheel", "four-wheel", "quattro", "xdrive", "4motion"],
                        "Heated Seats": ["heated", "climate package"],
                        "Autopilot": ["autopilot", "bluecruise", "super cruise", "highway driving", "hands-free", "traffic jam", "driving assistant"],
                        "3rd Row": ["3rd row", "third row"],
                        "Tow Package": ["tow", "towing", "trailer", "hitch"]
                    }
                    
                    def car_has_all_features(row):
                        car_dump = str(row.to_dict()).lower()
                        
                        for req_feature in desired_features:
                            aliases = feature_aliases.get(req_feature, [req_feature.lower()])
                            
                            if req_feature == "3rd Row" and row.get('seats', 5) >= 7:
                                continue
                                
                            if not any(alias.lower() in car_dump for alias in aliases):
                                return False
                        return True
                        
                    recs_df = recs_df[recs_df.apply(car_has_all_features, axis=1)]
                
                if recs_df.empty:
                    st.warning("Matches found, but none met your strict Price, Fuel Type, Primary Use, and Must-Haves requirements. Try relaxing your filters or increasing your budget.")
                    st.session_state.search_results = None
                else:
                    recs_df = recs_df.head(5)
                    
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
                    for idx, row in recs_df.iterrows():
                        costs = api_client.calculate_tco(row, tco_inputs)
                        
                        car_data = row.to_dict()
                        if costs:
                            car_data.update(costs)
                            car_data['Monthly Cash Flow'] += total_subs
                            car_data['Monthly True Cost'] += total_subs
                        
                        results.append(car_data)
                    
                    sort_cols = ["Monthly True Cost"]
                    sort_asc = [True]
                    
                    if priority == "Performance (Speed)":
                        sort_cols = ["acceleration", "Monthly True Cost"]
                        sort_asc = [True, True] 
                    elif priority == "Utility (Cargo)":
                        sort_cols = ["cargo_space", "Monthly True Cost"]
                        sort_asc = [False, True] 
                    elif priority == "Tech & Safety":
                        sort_cols = ["driver_assist_score", "Monthly True Cost"]
                        sort_asc = [False, True] 
                    
                    results_df = pd.DataFrame(results).sort_values(by=sort_cols, ascending=sort_asc)
                    
                    st.session_state.search_results = results_df
                    st.session_state.pitch_map = {}
                    
                    if not results_df.empty:
                        top_car = results_df.iloc[0]
                        top_idx = results_df.index[0]
                        
                        with st.spinner(f"Auto-analyzing top match: {top_car['model']}..."):
                            ai_instruction = f"{priority}. Please also include a response based on the 'Pros' of the vehicle from its reviews, and explicitly list out the vehicle's notable features."
                            pitch = api_client.get_ai_pitch(top_car, ai_instruction)
                            st.session_state.pitch_map[top_idx] = pitch

    if st.session_state.search_results is not None:
        st.divider()
        st.subheader("Recommended for You")
        
        results_df = st.session_state.search_results
        
        st.download_button("📥 Download Results as CSV", results_df.to_csv(index=False).encode('utf-8'), 'recs.csv', 'text/csv')
        
        for idx, row in results_df.iterrows():
            cost_label = "Monthly Pmt" if global_method != 'Cash' else "Monthly TCO"
            cost_val = row.get('Monthly Payment', 0) if global_method != 'Cash' else row.get('Monthly True Cost', 0)
            
            expanded_state = True
            
            with st.expander(f"{row['year']} {row['make']} {row['model']} | {cost_label}: ${cost_val:.0f}", expanded=expanded_state):
                
                st.caption(f"✨ **Features:** {row.get('features', 'Standard')}")
                if 'review_summary' in row:
                    st.caption(f"📝 **Review:** {row['review_summary']}")
                    
                if idx in st.session_state.pitch_map:
                    st.info(f"🤖 **AI Analysis:** {st.session_state.pitch_map[idx]}")

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Price", f"${row.get('price',0):,.0f}")
                c2.metric("Monthly Flow", f"${row.get('Monthly Cash Flow',0):.0f}", help="Pmt + Fuel + Ins + Maint + Subs")
                c3.metric("MPG/MPGe", f"{row.get('Est MPG', row.get('city_mpg'))}", help="Weighted by driving habits & climate")
                c4.metric("Seats", f"{row.get('seats', 5)}") 
                
                if 'source' in row: st.caption(f"⚡ {row['source']}")

                if idx not in st.session_state.pitch_map:
                    if st.button(f"🤖 Why buy this?", key=f"ai_{idx}"):
                        with st.spinner("Asking AI..."):
                            ai_instruction = f"{priority}. Please also include a response based on the 'Pros' of the vehicle from its reviews, and explicitly list out the vehicle's notable features."
                            pitch = api_client.get_ai_pitch(row, ai_instruction)
                            st.session_state.pitch_map[idx] = pitch
                            st.rerun() 

                if st.button(f"💰 Deep Dive", key=f"btn_{idx}"):
                    st.session_state.deal_car = f"{row['make']} {row['model']} ({row['year']})"
                    st.success("Sent to Deal Analyzer!")

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
                deal_name = f"DEAL: {deal.get('make')} {deal.get('model')} - ${deal.get('price', 0):,.0f}"
                deal['display_name'] = deal_name
                custom_deals.append(deal)
        
        std_options = df_display['display_name'].tolist()
        deal_options = [d['display_name'] for d in custom_deals]
        all_options = deal_options + std_options 
        
        compare_selection = st.multiselect("Select Vehicles to Compare", all_options, max_selections=4)
        
        if compare_selection:
            rows_to_display = []
            
            for sel in compare_selection:
                if sel in deal_options:
                    found_deal = next(d for d in custom_deals if d['display_name'] == sel).copy()
                    rows_to_display.append(found_deal)
                else:
                    row = df_display[df_display['display_name'] == sel].iloc[0].to_dict()
                    rows_to_display.append(row)
            
            comp_df = pd.DataFrame(rows_to_display)
            
            st.markdown("### Specifications")
            base_cols = ['make', 'model', 'price', 'city_mpg', 'acceleration', 'seats', 'reliability_score']
            present_base_cols = [c for c in base_cols if c in comp_df.columns]
            final_cols = ['display_name'] + present_base_cols
            
            # Format price for base table
            formatted_base_df = comp_df[final_cols].copy()
            if 'price' in formatted_base_df.columns:
                formatted_base_df['price'] = formatted_base_df['price'].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) and isinstance(x, (int, float)) else x)
            
            comp_display = formatted_base_df.set_index('display_name').transpose()
            st.dataframe(comp_display.astype(str))
            
            st.divider()
            st.markdown("### 🧮 Total Cost of Ownership (TCO)")
            st.info("Calculate depreciation, fuel, insurance, and maintenance costs over 1, 3, and 5 years based on your global settings.")
            
            if st.button("Calculate TCO for Selected Cars", type="primary"):
                global_tco_inputs = {
                    'gas_price': gas_price, 
                    'elec_price': elec_price,
                    'elec_price_road': elec_price_fast,
                    'method': global_method, 'apr': global_apr, 'term': global_term, 'down_payment': global_down,
                    'commute_dist': commute_dist, 'days_week': days_week, 'commute_type': commute_type,
                    'road_trip_miles': road_trip_miles, 'other_miles': other_miles,
                    'climate': env_climate, 'terrain': env_terrain,
                    'driver_age': driver_age_est
                }
                
                with st.spinner("Calculating multi-year costs via API..."):
                    tco_rows = []
                    for sel_row in rows_to_display:
                        row_copy = sel_row.copy()
                        deal_inputs = row_copy.get('deal_inputs', global_tco_inputs)
                        
                        # Base calculations
                        base_costs = api_client.calculate_tco(row_copy, deal_inputs)
                        if base_costs:
                            row_copy['Monthly Payment'] = base_costs.get('Monthly Payment', 0)
                            row_copy['Monthly True Cost'] = base_costs.get('Monthly True Cost', 0) + total_subs
                            row_copy['Resale Value'] = base_costs.get('Resale Value', 0)
                            
                        # Calculate 1, 3, and 5 year projections
                        for y in [1, 3, 5]:
                            temp_inputs = deal_inputs.copy()
                            temp_inputs['years'] = y
                            costs = api_client.calculate_tco(row_copy, temp_inputs)
                            if costs:
                                row_copy[f'Total Cost ({y} yr)'] = (costs.get('Monthly True Cost', 0) + total_subs) * 12 * y
                            else:
                                row_copy[f'Total Cost ({y} yr)'] = 0
                                
                        tco_rows.append(row_copy)
                        
                    tco_df = pd.DataFrame(tco_rows)
                    
                    tco_cols = ['Monthly Payment', 'Monthly True Cost', 'Resale Value', 'Total Cost (1 yr)', 'Total Cost (3 yr)', 'Total Cost (5 yr)']
                    present_tco_cols = [c for c in tco_cols if c in tco_df.columns]
                    final_tco_cols = ['display_name'] + present_tco_cols
                    
                    formatted_tco_df = tco_df[final_tco_cols].copy()
                    for c in present_tco_cols:
                        formatted_tco_df[c] = formatted_tco_df[c].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) and isinstance(x, (int, float)) else x)
                    
                    tco_display = formatted_tco_df.set_index('display_name').transpose()
                
                # Render results outside of the spinner so it waits perfectly
                st.markdown("#### TCO Results")
                st.dataframe(tco_display.astype(str))

            st.divider()
            st.markdown("### Performance Chart")
            fig = px.scatter(comp_df, x='price', y='acceleration', color='make', size='city_mpg', hover_data=['model'])
            st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("💰 Deal Analyzer")
    
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
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("1. Deal Settings")
            deal_method = st.radio("Buying Method", ["Cash", "Finance", "Lease"])
            price_input = st.number_input("Negotiated Price ($)", value=int(car_row['price']), step=500)
            
            st.markdown("**Insurance Override**")
            custom_ins = st.number_input("Custom Quote ($/Month)", 0, 1000, 0, help="Leave 0 to use estimate")
            
            analysis_years = 5 
            if deal_method != "Lease":
                analysis_years = st.number_input("Analysis Duration (Years)", min_value=1, max_value=15, value=5, step=1)
            
            user_inputs = {
                'years': analysis_years, 'annual_miles': 12000, 
                'gas_price': gas_price, 'elec_price': elec_price, 'elec_price_road': elec_price_fast,
                'method': deal_method, 'custom_insurance': custom_ins, 'driver_age': driver_age_est
            }
            
            if deal_method == "Finance":
                user_inputs['apr'] = st.number_input("APR (%)", value=6.0, step=0.1)
                user_inputs['term'] = st.number_input("Loan Term (Months)", value=60, step=12)
                user_inputs['down_payment'] = st.number_input("Down Payment ($)", value=2000, step=500)
            elif deal_method == "Lease":
                user_inputs['lease_monthly'] = st.number_input("Monthly Payment ($)", value=500, step=10)
                user_inputs['lease_due'] = st.number_input("Due at Signing ($)", value=2000, step=100)
                user_inputs['lease_term'] = st.number_input("Lease Term (Months)", value=36, step=12)
                user_inputs['years'] = user_inputs['lease_term'] / 12

        car_row_calc = car_row.copy()
        car_row_calc['price'] = price_input
        costs = api_client.calculate_tco(car_row_calc, user_inputs)
        
        if costs:
            costs['Monthly Cash Flow'] += total_subs
            costs['Monthly True Cost'] += total_subs

        with col2:
            st.subheader("2. Cost Breakdown")
            if not costs:
                st.error("Calculation failed via API")
            else:
                total_label = "Total Period"
                if deal_method == "Lease":
                    term = int(user_inputs.get('lease_term', 36))
                    total_label = f"Total ({term} Mos)"
                else:
                    total_label = f"Total ({analysis_years} Yrs)"
                    
                view_mode = st.radio("Timeframe", ["Monthly", "Yearly", total_label], horizontal=True)
                show_dep = st.checkbox("Include Depreciation in Total?", value=False)
                
                if view_mode == "Yearly":
                    mult = 12
                elif view_mode == total_label:
                    if deal_method == "Lease":
                        mult = user_inputs.get('lease_term', 36)
                    else:
                        mult = analysis_years * 12
                else:
                    mult = 1
                
                display_cost = costs['Monthly True Cost'] * mult if show_dep else costs['Monthly Cash Flow'] * mult
                subtext = "Includes Dep/Equity Loss" if show_dep else "Running Cash Flow"
                if view_mode == total_label and not show_dep:
                    display_cost += costs['Upfront Cost']
                    subtext = "Cash Flow + Upfront"

                m1, m2 = st.columns(2)
                m1.metric(f"Cost ({view_mode})", f"${display_cost:,.2f}", delta=subtext)
                m2.metric("Payment Portion", f"${costs['Monthly Payment'] * mult:,.2f}")
                
                if st.button("➕ Add to Compare"):
                    snap = car_row_calc.to_dict()
                    snap.update(costs)
                    snap['deal_inputs'] = user_inputs.copy()
                    st.session_state.comparison_list.append(snap)
                    st.success("Added!")

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
                st.bar_chart(bd_df.set_index("Cost Component"))