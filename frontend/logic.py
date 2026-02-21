import pandas as pd
import requests
import json


def load_data(api_url):
    """
    Loads basic vehicle data to populate UI lists (Make, Model, etc.).
    Now fetches cleanly from the Backend API instead of a direct DB connection.
    """
    print("DEBUG (load_data): Requesting full vehicle database from Backend API...")

    if api_url:
        client = APIClient(api_url)
        df = client.get_all_cars()
        if not df.empty:
            print(f"✅ Successfully loaded {len(df)} cars via API.")
            return df
            
    print("⚠️ API returned empty or failed. Returning fallback data to prevent UI crash.")
    fallback_data = [
        {'make': 'Toyota', 'model': 'Prius', 'year': 2024, 'class': 'Sedan', 'price': 28000, 'city_mpg': 57, 'hwy_mpg': 56, 'fuel_type': 'Hybrid', 'reliability_score': 9.5, 'luxury_score': 5, 'features': 'Toyota Safety Sense 3.0', 'cargo_space': 20.3, 'rear_legroom': 34.8, 'acceleration': 7.2, 'driver_assist_score': 7, 'offroad_capability': 2, 'seats': 5},
        {'make': 'Honda', 'model': 'CR-V Hybrid', 'year': 2024, 'class': 'SUV', 'price': 34000, 'city_mpg': 43, 'hwy_mpg': 36, 'fuel_type': 'Hybrid', 'reliability_score': 9.0, 'luxury_score': 6, 'features': 'Honda Sensing', 'cargo_space': 39.3, 'rear_legroom': 41.0, 'acceleration': 7.6, 'driver_assist_score': 6, 'offroad_capability': 5, 'seats': 5},
        {'make': 'Ford', 'model': 'Maverick Hybrid', 'year': 2024, 'class': 'Pickup', 'price': 26000, 'city_mpg': 42, 'hwy_mpg': 33, 'fuel_type': 'Hybrid', 'reliability_score': 8.0, 'luxury_score': 4, 'features': 'FLEXBED', 'cargo_space': 33.3, 'rear_legroom': 36.9, 'acceleration': 7.7, 'driver_assist_score': 5, 'offroad_capability': 4, 'seats': 5},
        {'make': 'Tesla', 'model': 'Model 3', 'year': 2024, 'class': 'Sedan', 'price': 40000, 'city_mpg': 130, 'hwy_mpg': 138, 'fuel_type': 'Electric', 'reliability_score': 7.0, 'luxury_score': 7, 'features': 'Autopilot', 'cargo_space': 19.8, 'rear_legroom': 35.2, 'acceleration': 5.8, 'driver_assist_score': 9, 'offroad_capability': 3, 'seats': 5},
        {'make': 'Toyota', 'model': 'Camry', 'year': 2024, 'class': 'Sedan', 'price': 28000, 'city_mpg': 28, 'hwy_mpg': 39, 'fuel_type': 'Gas', 'reliability_score': 9.0, 'luxury_score': 5, 'features': 'TSS 2.5+', 'cargo_space': 15.1, 'rear_legroom': 38.0, 'acceleration': 7.6, 'driver_assist_score': 6, 'offroad_capability': 2, 'seats': 5},
        {'make': 'Rivian', 'model': 'R1S', 'year': 2024, 'class': 'SUV', 'price': 78000, 'city_mpg': 73, 'hwy_mpg': 65, 'fuel_type': 'Electric', 'reliability_score': 6.5, 'luxury_score': 9, 'features': 'Off-road Mode', 'cargo_space': 104.0, 'rear_legroom': 36.6, 'acceleration': 3.0, 'driver_assist_score': 8, 'offroad_capability': 10, 'seats': 7}
    ]
    return pd.DataFrame(fallback_data)


# api
class APIClient:
    """
    Handles all communication with the Backend Lambda.
    Removes the need for local ML libraries.
    """
    def __init__(self, api_url):
        self.api_url = api_url

    def refresh_database(self):
        """Call Lambda to force a refresh of its internal database cache"""
        if not self.api_url: return False
        
        try:
            payload = {"action": "refresh"}
            response = requests.post(self.api_url, json=payload, timeout=15)
            return response.status_code == 200
        except Exception as e:
            print(f"API Error (Refresh): {e}")
            return False

    def get_all_cars(self):
        """Call Lambda to get the full database of cars"""
        if not self.api_url: return pd.DataFrame()
        
        try:
            payload = {"action": "get_all_cars"}
            response = requests.post(self.api_url, json=payload, timeout=29)
            if response.status_code == 200:
                return pd.DataFrame(response.json())
            return pd.DataFrame()
        except Exception as e:
            print(f"API Error (Get All Cars): {e}")
            return pd.DataFrame()

    def get_recommendations(self, user_prefs):
        """Call Lambda to get ML Recommendations"""
        if not self.api_url: return pd.DataFrame()
        
        try:
            payload = {
                "action": "recommend",
                "inputs": user_prefs
            }
            response = requests.post(self.api_url, json=payload, timeout=29)
            if response.status_code == 200:
                return pd.DataFrame(response.json())
            return pd.DataFrame()
        except Exception as e:
            print(f"API Error (Recommend): {e}")
            return pd.DataFrame()

    def calculate_tco(self, car_row, inputs):
        """Call Lambda to calculate TCO and Resale Value"""
        if not self.api_url: 
            print("DEBUG: calculate_tco failed - api_url is empty")
            return {}
        
        try:
            car_data_clean = json.loads(car_row.to_json())
            
            payload = {
                "action": "calculate",
                "car_data": car_data_clean,
                "inputs": inputs
            }
            
            response = requests.post(self.api_url, json=payload, timeout=29)
            
            if response.status_code == 200:
                result = response.json()
                result['source'] = "⚡ AWS Lambda"
                return result
            else:
                print(f"DEBUG (calculate_tco): API Error Response Text = {response.text}")
            return {}
        except Exception as e:
            print(f"API Error (Calculate): {e}")
            return {}

    def get_ai_pitch(self, car_row, priority):
        """Call Lambda to get Bedrock AI Pitch"""
        if not self.api_url: return "API Not Configured"
        
        try:
            car_data_clean = json.loads(car_row.to_json())
            payload = {
                "action": "pitch",
                "car_data": car_data_clean,
                "inputs": {"priority": priority}
            }
            response = requests.post(self.api_url, json=payload, timeout=29)
            if response.status_code == 200:
                return response.json().get('pitch', "No pitch available.")
            return f"Error: {response.text}"
        except Exception as e:
            return f"Connection Error: {str(e)}"


# buisness logic
class AppLogic:
    """
    Handles data manipulation and formatting specifically for the Streamlit UI,
    keeping the main app.py file clean and readable.
    """
    
    @staticmethod
    def calculate_budget(budget_type, target_budget=0, monthly_cap=0, yearly_cap=0):
        if budget_type == "Vehicle Budget (Sticker)":
            return target_budget
        elif budget_type == "Monthly Total Budget (All-In)":
            est_ops = 250
            avail_pmt = max(0, monthly_cap - est_ops)
            return avail_pmt * 55 
        else: 
            monthly_equiv = yearly_cap / 12
            est_ops = 250
            avail_pmt = max(0, monthly_equiv - est_ops)
            return avail_pmt * 55

    @staticmethod
    def build_user_prefs(fuel_choices, pax_needs, perf_needs, assist_needs, calc_budget, priority, target_class, target_luxury, target_fun, target_offroad, seats_needs):
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
            
        return {
            'price': target_price_final, 'class': target_class, 
            'fuel_type': 'Any', 
            'city_mpg': target_mpg, 'reliability_score': 8.0, 
            'luxury_score': target_luxury, 'fun_score': target_fun,
            'rear_legroom': target_legroom, 'acceleration': target_accel,
            'cargo_space': target_cargo_final, 'driver_assist_score': target_assist,
            'offroad_capability': target_offroad,
            'seats': seats_needs
        }

    @staticmethod
    def filter_and_process_results(recs_df, fuel_choices, calc_budget, target_class, desired_features, api_client, tco_inputs, total_subs, priority):
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
            return pd.DataFrame()
            
        recs_df = recs_df.head(5)
        
        results = []
        for idx, row in recs_df.iterrows():
            costs = api_client.calculate_tco(row, tco_inputs)
            car_data = row.to_dict()
            
            if costs:
                car_data.update(costs)
                car_data['Monthly Cash Flow'] += total_subs
                car_data['Monthly True Cost'] += total_subs
            
            car_features = [f.strip() for f in car_data.get('features', '').split(',')]
            matches = [f for f in desired_features if any(f.lower() in feat.lower() for feat in car_features)]
            car_data['match_count'] = len(matches)
            car_data['matched_features'] = ", ".join(matches)
            
            car_data['price_diff'] = abs(car_data.get('price', 0) - calc_budget)
            
            results.append(car_data)
        
        sort_cols = ["match_count", "price_diff", "Monthly True Cost"]
        sort_asc = [False, True, True]
        
        if priority == "Lowest Total Cost":
            sort_cols = ["match_count", "Monthly True Cost"]
            sort_asc = [False, True] 
        elif priority == "Performance (Speed)":
            sort_cols = ["match_count", "acceleration", "price_diff"]
            sort_asc = [False, True, True] 
        elif priority == "Utility (Cargo)":
            sort_cols = ["match_count", "cargo_space", "price_diff"]
            sort_asc = [False, False, True] 
        elif priority == "Tech & Safety":
            sort_cols = ["match_count", "driver_assist_score", "price_diff"]
            sort_asc = [False, False, True] 
        
        return pd.DataFrame(results).sort_values(by=sort_cols, ascending=sort_asc)

    @staticmethod
    def format_comparison_dataframe(comp_df):
        base_cols = ['make', 'model', 'price', 'city_mpg', 'acceleration', 'seats', 'reliability_score']
        present_base_cols = [c for c in base_cols if c in comp_df.columns]
        final_cols = ['display_name'] + present_base_cols
        
        formatted_base_df = comp_df[final_cols].copy()
        if 'price' in formatted_base_df.columns:
            formatted_base_df['price'] = formatted_base_df['price'].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) and isinstance(x, (int, float)) else x)
        
        return formatted_base_df.set_index('display_name').transpose()

    @staticmethod
    def calculate_comparison_tcos(rows_to_display, global_tco_inputs, api_client, total_subs):
        tco_rows = []
        for sel_row in rows_to_display:
            row_copy = sel_row.copy()
            deal_inputs = row_copy.get('deal_inputs', global_tco_inputs)
            
            clean_row_dict = {k: v for k, v in row_copy.items() if k not in ['deal_inputs', 'is_deal']}
            car_series = pd.Series(clean_row_dict)
            
            base_costs = api_client.calculate_tco(car_series, deal_inputs)
            if base_costs:
                row_copy['Monthly Payment'] = base_costs.get('Monthly Payment', 0)
                row_copy['Monthly True Cost'] = base_costs.get('Monthly True Cost', 0) + total_subs
                row_copy['Resale Value'] = base_costs.get('Resale Value', 0)
                
            for y in [1, 3, 5]:
                temp_inputs = deal_inputs.copy()
                temp_inputs['years'] = y
                costs = api_client.calculate_tco(car_series, temp_inputs)
                if costs:
                    row_copy[f'Total Cost ({y} yr)'] = (costs.get('Monthly True Cost', 0) + total_subs) * 12 * y
                else:
                    row_copy[f'Total Cost ({y} yr)'] = 0
                    
            tco_rows.append(row_copy)
            
        return pd.DataFrame(tco_rows)

    @staticmethod
    def format_tco_dataframe(tco_df):
        tco_cols = ['Monthly Payment', 'Monthly True Cost', 'Resale Value', 'Total Cost (1 yr)', 'Total Cost (3 yr)', 'Total Cost (5 yr)']
        present_tco_cols = [c for c in tco_cols if c in tco_df.columns]
        final_tco_cols = ['display_name'] + present_tco_cols
        
        formatted_tco_df = tco_df[final_tco_cols].copy()
        for c in present_tco_cols:
            formatted_tco_df[c] = formatted_tco_df[c].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) and isinstance(x, (int, float)) else x)
        
        return formatted_tco_df.set_index('display_name').transpose()

    @staticmethod
    def build_deal_inputs(deal_method, analysis_years, gas_price, elec_price, elec_price_fast, custom_ins, driver_age_est, **kwargs):
        user_inputs = {
            'years': analysis_years, 'annual_miles': 12000, 
            'gas_price': gas_price, 'elec_price': elec_price, 'elec_price_road': elec_price_fast,
            'method': deal_method, 'custom_insurance': custom_ins, 'driver_age': driver_age_est
        }
        if deal_method == "Finance":
            user_inputs['apr'] = kwargs.get('apr', 6.0)
            user_inputs['term'] = kwargs.get('term', 60)
            user_inputs['down_payment'] = kwargs.get('down_payment', 2000)
        elif deal_method == "Lease":
            user_inputs['lease_monthly'] = kwargs.get('lease_monthly', 500)
            user_inputs['lease_due'] = kwargs.get('lease_due', 2000)
            user_inputs['lease_term'] = kwargs.get('lease_term', 36)
            user_inputs['years'] = user_inputs['lease_term'] / 12
        return user_inputs

    @staticmethod
    def get_breakdown_data(costs, view_mode, total_label, mult, total_subs):
        val_pay = costs.get('Monthly Payment', 0) * mult
        val_fuel = costs.get('Monthly Fuel', 0) * mult
        val_ins = costs.get('Monthly Ins', 0) * mult
        val_maint = costs.get('Monthly Maint', 0) * mult
        val_dep = costs.get('Monthly Dep', 0) * mult
        val_subs = total_subs * mult
        
        breakdown_data = {
            "Cost Component": ["Vehicle Payment", "Fuel / Charging", "Insurance", "Maintenance", "Subscriptions", "Depreciation (Hidden)"],
            f"Cost ({view_mode})": [val_pay, val_fuel, val_ins, val_maint, val_subs, val_dep]
        }
        if view_mode == total_label and costs.get('Upfront Cost', 0) > 0:
            breakdown_data["Cost Component"].append("Upfront Due")
            breakdown_data[f"Cost ({view_mode})"].append(costs.get('Upfront Cost', 0))

        return pd.DataFrame(breakdown_data)