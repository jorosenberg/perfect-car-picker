import pandas as pd
import numpy as np
import os
import requests
import json
import sqlalchemy
import time

# --- 1. DATA LOADING (For UI Dropdowns) ---
def load_data():
    """
    Loads basic vehicle data to populate UI lists (Make, Model, etc.).
    This is lightweight and does not require ML libraries.
    """
    db_host = os.environ.get('DB_HOST')
    db_user = os.environ.get('DB_USER', 'adminuser')
    db_pass = os.environ.get('DB_PASS')
    db_name = os.environ.get('DB_NAME', 'cardb')

    print(f"DEBUG (load_data): DB_HOST='{db_host}', DB_USER='{db_user}', DB_NAME='{db_name}'")

    if db_host and db_pass:
        try:
            db_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:5432/{db_name}"
            # Short connect timeout so Streamlit doesn't hang endlessly on a bad ping
            engine = sqlalchemy.create_engine(
                db_url, 
                connect_args={'connect_timeout': 5}
            )
            
            # Ping up to 12 times (60 seconds total) to wait for RDS to wake up
            max_retries = 12
            for attempt in range(max_retries):
                try:
                    df = pd.read_sql("SELECT * FROM cars", engine)
                    print(f"✅ Successfully connected to RDS. Loaded {len(df)} cars.")
                    return df
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"⏳ RDS not ready. Retrying in 5 seconds... ({attempt + 1}/{max_retries})")
                        time.sleep(5)
                    else:
                        print(f"❌ RDS Connection Failed after 60 seconds: {e}")
        except Exception as e:
            print(f"❌ RDS Configuration Failed: {e}")
            
    print("⚠️ Returning fallback data to prevent 'No cars loaded' error in UI.")
    # Fallback data ensures that if Streamlit caches the result on a bad boot, Tabs 2 and 4 still work.
    fallback_data = [
        {'make': 'Toyota', 'model': 'Prius', 'year': 2024, 'class': 'Sedan', 'price': 28000, 'city_mpg': 57, 'hwy_mpg': 56, 'fuel_type': 'Hybrid', 'reliability_score': 9.5, 'luxury_score': 5, 'features': 'Toyota Safety Sense 3.0', 'cargo_space': 20.3, 'rear_legroom': 34.8, 'acceleration': 7.2, 'driver_assist_score': 7, 'offroad_capability': 2, 'seats': 5},
        {'make': 'Honda', 'model': 'CR-V Hybrid', 'year': 2024, 'class': 'SUV', 'price': 34000, 'city_mpg': 43, 'hwy_mpg': 36, 'fuel_type': 'Hybrid', 'reliability_score': 9.0, 'luxury_score': 6, 'features': 'Honda Sensing', 'cargo_space': 39.3, 'rear_legroom': 41.0, 'acceleration': 7.6, 'driver_assist_score': 6, 'offroad_capability': 5, 'seats': 5},
        {'make': 'Ford', 'model': 'Maverick Hybrid', 'year': 2024, 'class': 'Pickup', 'price': 26000, 'city_mpg': 42, 'hwy_mpg': 33, 'fuel_type': 'Hybrid', 'reliability_score': 8.0, 'luxury_score': 4, 'features': 'FLEXBED', 'cargo_space': 33.3, 'rear_legroom': 36.9, 'acceleration': 7.7, 'driver_assist_score': 5, 'offroad_capability': 4, 'seats': 5},
        {'make': 'Tesla', 'model': 'Model 3', 'year': 2024, 'class': 'Sedan', 'price': 40000, 'city_mpg': 130, 'hwy_mpg': 138, 'fuel_type': 'Electric', 'reliability_score': 7.0, 'luxury_score': 7, 'features': 'Autopilot', 'cargo_space': 19.8, 'rear_legroom': 35.2, 'acceleration': 5.8, 'driver_assist_score': 9, 'offroad_capability': 3, 'seats': 5},
        {'make': 'Toyota', 'model': 'Camry', 'year': 2024, 'class': 'Sedan', 'price': 28000, 'city_mpg': 28, 'hwy_mpg': 39, 'fuel_type': 'Gas', 'reliability_score': 9.0, 'luxury_score': 5, 'features': 'TSS 2.5+', 'cargo_space': 15.1, 'rear_legroom': 38.0, 'acceleration': 7.6, 'driver_assist_score': 6, 'offroad_capability': 2, 'seats': 5},
        {'make': 'Rivian', 'model': 'R1S', 'year': 2024, 'class': 'SUV', 'price': 78000, 'city_mpg': 73, 'hwy_mpg': 65, 'fuel_type': 'Electric', 'reliability_score': 6.5, 'luxury_score': 9, 'features': 'Off-road Mode', 'cargo_space': 104.0, 'rear_legroom': 36.6, 'acceleration': 3.0, 'driver_assist_score': 8, 'offroad_capability': 10, 'seats': 7}
    ]
    return pd.DataFrame(fallback_data)

# --- 2. API CLIENT (Thin Client Logic) ---
class APIClient:
    """
    Handles all communication with the Backend Lambda.
    Removes the need for local ML libraries.
    """
    def __init__(self, api_url):
        self.api_url = api_url

    def get_recommendations(self, user_prefs):
        """Call Lambda to get ML Recommendations"""
        if not self.api_url: return pd.DataFrame()
        
        try:
            payload = {
                "action": "recommend",
                "inputs": user_prefs
            }
            # Timeout set to 29s to match AWS API Gateway limits
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
            # FIX: Convert pandas Series to native Python types for JSON serialization.
            # Using .to_json() then json.loads() cleanly strips numpy data types (like int64).
            car_data_clean = json.loads(car_row.to_json())
            
            payload = {
                "action": "calculate",
                "car_data": car_data_clean,
                "inputs": inputs
            }
            
            print(f"DEBUG (calculate_tco): Sending request to API: {self.api_url}")
            print(f"DEBUG (calculate_tco): Car Data Make/Model = {car_data_clean.get('make')} {car_data_clean.get('model')}")
            
            response = requests.post(self.api_url, json=payload, timeout=29)
            
            print(f"DEBUG (calculate_tco): API Response Status = {response.status_code}")
            
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
            # FIX: Convert pandas Series to native Python types for JSON serialization.
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