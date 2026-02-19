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

    if db_host and db_pass:
        try:
            db_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:5432/{db_name}"
            engine = sqlalchemy.create_engine(
                db_url, 
                connect_args={'connect_timeout': 5}
            )

            max_retries = 6
            for attempt in range(max_retries):
                try:
                    df = pd.read_sql("SELECT * FROM cars", engine)
                    print("Successfully connected to RDS and loaded data.")
                    return df
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"RDS not ready. Retrying in 5 seconds... ({attempt + 1}/{max_retries})")
                        time.sleep(5)
                    else:
                        print(f"RDS Connection Failed after 30 seconds: {e}")
                        return pd.DataFrame() 
                    
        except Exception as e:
            print(f"Database Configuration Error: {e}")
            return pd.DataFrame()

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
            response = requests.post(self.api_url, json=payload, timeout=29)
            if response.status_code == 200:
                return pd.DataFrame(response.json())
            return pd.DataFrame()
        except Exception as e:
            print(f"API Error (Recommend): {e}")
            return pd.DataFrame()

    def calculate_tco(self, car_row, inputs):
        """Call Lambda to calculate TCO and Resale Value"""
        if not self.api_url: return {}
        
        try:
            payload = {
                "action": "calculate",
                "car_data": car_row.to_dict(),
                "inputs": inputs
            }
            response = requests.post(self.api_url, json=payload, timeout=29)
            if response.status_code == 200:
                result = response.json()
                result['source'] = "⚡ AWS Lambda"
                return result
            return {}
        except Exception as e:
            print(f"API Error (Calculate): {e}")
            return {}

    def get_ai_pitch(self, car_row, priority):
        """Call Lambda to get Bedrock AI Pitch"""
        if not self.api_url: return "API Not Configured"
        
        try:
            payload = {
                "action": "pitch",
                "car_data": car_row.to_dict(),
                "inputs": {"priority": priority}
            }
            response = requests.post(self.api_url, json=payload, timeout=29)
            if response.status_code == 200:
                return response.json().get('pitch', "No pitch available.")
            return f"Error: {response.text}"
        except Exception as e:
            return f"Connection Error: {str(e)}"