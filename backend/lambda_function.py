import json
import os
import pandas as pd
import sqlalchemy
import boto3
from cost_calculator import calculate_tco
from car_recommender import train_recommender_model, get_recommendations
from ai_advisor import get_car_pitch

def load_data():
    print("--- 🔍 DB LOAD INITIATED ---")
    db_user = os.environ.get('DB_USER', 'adminuser')
    db_pass = os.environ.get('DB_PASS')
    db_name = os.environ.get('DB_NAME', 'cardb')
    
    # FIX: Actually read the environment variable, don't overwrite with ""
    db_host = os.environ.get('DB_HOST', '') 
    
    print(f"ENV CHECK -> DB_USER: {db_user}, DB_NAME: {db_name}")
    print(f"ENV CHECK -> DB_HOST (from env vars): '{db_host}'")

    if not db_host:
        try:
            print(f"DB_HOST missing from Env Vars. Attempting to find RDS endpoint for DBName '{db_name}' via boto3...")
            rds_client = boto3.client('rds', region_name='us-east-1')
            response = rds_client.describe_db_instances()
            for instance in response.get('DBInstances', []):
                if instance.get('DBName') == db_name:
                    db_host = instance.get('Endpoint', {}).get('Address')
                    print(f"Found RDS endpoint dynamically: {db_host}")
                    break
            if not db_host:
                print("Could not find a matching RDS instance via boto3.")
        except Exception as e:
            print(f"Failed to fetch RDS endpoint via boto3: {e}")

    if db_host and db_pass:
        try:
            print(f"Attempting connection to PostgreSQL at {db_host}...")
            db_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:5432/{db_name}"
            # Short timeout so Lambda doesn't hang forever if networking fails
            engine = sqlalchemy.create_engine(db_url, connect_args={'connect_timeout': 5})
            df = pd.read_sql("SELECT * FROM cars", engine)
            print(f"SUCCESS: Loaded {len(df)} vehicles from RDS.")
            return df
        except Exception as e:
            print(f"RDS Connection Failed: {e}")
            print("Falling back to static static data.")

    # fallback
    print("Returning fallback data...")
    data = [
        {'make': 'Toyota', 'model': 'Prius', 'year': 2024, 'class': 'Sedan', 'price': 28000, 'city_mpg': 57, 'hwy_mpg': 56, 'fuel_type': 'Hybrid', 'reliability_score': 9.5, 'luxury_score': 5, 'features': 'Toyota Safety Sense 3.0', 'cargo_space': 20.3, 'rear_legroom': 34.8, 'acceleration': 7.2, 'driver_assist_score': 7, 'offroad_capability': 2, 'seats': 5},
        {'make': 'Honda', 'model': 'CR-V Hybrid', 'year': 2024, 'class': 'SUV', 'price': 34000, 'city_mpg': 43, 'hwy_mpg': 36, 'fuel_type': 'Hybrid', 'reliability_score': 9.0, 'luxury_score': 6, 'features': 'Honda Sensing', 'cargo_space': 39.3, 'rear_legroom': 41.0, 'acceleration': 7.6, 'driver_assist_score': 6, 'offroad_capability': 5, 'seats': 5},
        {'make': 'Ford', 'model': 'Maverick Hybrid', 'year': 2024, 'class': 'Pickup', 'price': 26000, 'city_mpg': 42, 'hwy_mpg': 33, 'fuel_type': 'Hybrid', 'reliability_score': 8.0, 'luxury_score': 4, 'features': 'FLEXBED', 'cargo_space': 33.3, 'rear_legroom': 36.9, 'acceleration': 7.7, 'driver_assist_score': 5, 'offroad_capability': 4, 'seats': 5},
        {'make': 'Tesla', 'model': 'Model 3', 'year': 2024, 'class': 'Sedan', 'price': 40000, 'city_mpg': 130, 'hwy_mpg': 138, 'fuel_type': 'Electric', 'reliability_score': 7.0, 'luxury_score': 7, 'features': 'Autopilot', 'cargo_space': 19.8, 'rear_legroom': 35.2, 'acceleration': 5.8, 'driver_assist_score': 9, 'offroad_capability': 3, 'seats': 5},
        {'make': 'Toyota', 'model': 'Camry', 'year': 2024, 'class': 'Sedan', 'price': 28000, 'city_mpg': 28, 'hwy_mpg': 39, 'fuel_type': 'Gas', 'reliability_score': 9.0, 'luxury_score': 5, 'features': 'TSS 2.5+', 'cargo_space': 15.1, 'rear_legroom': 38.0, 'acceleration': 7.6, 'driver_assist_score': 6, 'offroad_capability': 2, 'seats': 5},
        {'make': 'Rivian', 'model': 'R1S', 'year': 2024, 'class': 'SUV', 'price': 78000, 'city_mpg': 73, 'hwy_mpg': 65, 'fuel_type': 'Electric', 'reliability_score': 6.5, 'luxury_score': 9, 'features': 'Off-road Mode', 'cargo_space': 104.0, 'rear_legroom': 36.6, 'acceleration': 3.0, 'driver_assist_score': 8, 'offroad_capability': 10, 'seats': 7}
    ]
    return pd.DataFrame(data)

# model cache
_model = None
_preprocessor = None
_df = None

def get_model_assets():
    global _model, _preprocessor, _df
    if _model is None:
        _df = load_data()
        _model, _preprocessor = train_recommender_model(_df)
    return _df, _model, _preprocessor

def lambda_handler(event, context):
    try:
        if 'body' in event:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        else:
            body = event

        action = body.get('action', 'calculate')
        inputs = body.get('inputs', {})
        car_data = body.get('car_data', {})
        
        print(f"Action triggered: '{action}'")
        
        result = {}

        if action == 'recommend':
            print("Processing Recommendation Request...")
            df, model, preprocessor = get_model_assets()
            recommendations_df = get_recommendations(inputs, df, model, preprocessor)
            result = recommendations_df.to_dict(orient='records')
            
        elif action == 'calculate':
            print("Processing Calculation Request...")
            if not car_data:
                return {'statusCode': 400, 'body': json.dumps({'error': 'Missing car_data'})}
            result = calculate_tco(car_data, inputs, resale_model=None)

        elif action == 'pitch':
            print("Processing Pitch Request...")
            if not car_data:
                return {'statusCode': 400, 'body': json.dumps({'error': 'Missing car_data'})}
            priority = inputs.get('priority', 'Balanced')
            pitch_text = get_car_pitch(car_data, priority)
            result = {'pitch': pitch_text}

        else:
            return {'statusCode': 400, 'body': json.dumps({'error': f'Unknown action: {action}'})}

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"Fatal Lambda Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }