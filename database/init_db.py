import os
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text

def init_db():
    db_host = os.environ.get('DB_HOST')
    db_user = os.environ.get('DB_USER')
    db_pass = os.environ.get('DB_PASS')
    db_name = os.environ.get('DB_NAME')
    
    if db_host and db_pass:
        print(f"🚀 Detected AWS Environment. Target DB: {db_host}/{db_name}")
        
        root_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:5432/postgres"
        
        try:
            root_engine = create_engine(root_url, isolation_level="AUTOCOMMIT")
            with root_engine.connect() as conn:
                check_query = text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'")
                exists = conn.execute(check_query).fetchone()
                
                if not exists:
                    print(f"⚠️ Database '{db_name}' not found. Creating...")
                    conn.execute(text(f"CREATE DATABASE {db_name}"))
                    print(f"✅ Created database '{db_name}' successfully.")
                else:
                    print(f"ℹ️ Database '{db_name}' already exists.")
                    
        except Exception as e:
            print(f"⚠️ Warning: Could not check/create database. It might already exist or permissions are restricted.\nError: {e}")

        db_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:5432/{db_name}"
    else:
        db_path = os.path.join(os.path.dirname(__file__), 'cars.db')
        print(f"⚠️ No DB_HOST found. Using local SQLite '{db_path}'...")
        db_url = f"sqlite:///{db_path}"

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            print(f"✅ Connection to '{db_name}' successful.")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    cars_data = [
        # --- HYBRIDS ---
        ('Toyota', 'Prius', 2024, 'Sedan', 28000, 57, 56, 'Hybrid', 9.5, 5, 'Toyota Safety Sense 3.0, Wireless CarPlay, Solar Roof, Heated Seats', 20.3, 34.8, 7.2, "Pros: Incredible MPG, sleek new design. Cons: Rear headroom is tight.", 7, "Toyota Safety Sense™ 3.0", "https://www.toyota.com/safety-sense/", 2, 5),
        ('Honda', 'CR-V Hybrid', 2024, 'SUV', 34000, 43, 36, 'Hybrid', 9.0, 6, 'Honda Sensing, Bose Audio, Leather Seats, Moonroof', 39.3, 41.0, 7.6, "Pros: Spacious interior, smooth hybrid system. Cons: No spare tire.", 6, "Honda Sensing®", "https://automobiles.honda.com/sensing", 5, 5),
        ('Ford', 'Maverick Hybrid', 2024, 'Pickup', 26000, 42, 33, 'Hybrid', 8.0, 4, 'FLEXBED System, Apple CarPlay, Ford Co-Pilot360, Crew Cab', 33.3, 36.9, 7.7, "Pros: Unbeatable price and MPG for a truck. Cons: Cheap interior plastics.", 5, "Ford Co-Pilot360™", "https://www.ford.com/technology/driver-assist-technology/", 4, 5),
        ('Lexus', 'ES 300h', 2024, 'Sedan', 44000, 43, 44, 'Hybrid', 9.5, 8, 'Lexus Safety System+ 2.5, Mark Levinson Audio, Ultra Luxury Package', 13.9, 39.2, 8.1, "Pros: Extremely quiet, plush ride, excellent fuel economy. Cons: Not sporty.", 7, "Lexus Safety System+ 2.5", "https://www.lexus.com/safety", 2, 5),

        # --- GAS ---
        ('Toyota', 'Camry', 2024, 'Sedan', 28000, 28, 39, 'Gas', 9.0, 5, 'Apple CarPlay, Toyota Safety Sense 2.5+, 9-inch Touchscreen, Dual-Zone Climate', 15.1, 38.0, 7.6, "Pros: Comfortable ride, user-friendly controls. Cons: Noisier cabin than some rivals.", 6, "Toyota Safety Sense™ 2.5+", "https://www.toyota.com/safety-sense/", 2, 5),
        ('Honda', 'Civic', 2024, 'Sedan', 26000, 31, 40, 'Gas', 9.0, 4, 'Honda Sensing, Bose Audio, 9-inch Screen, Wireless CarPlay', 14.8, 37.4, 7.5, "Pros: Agile handling, spacious cabin for a compact. Cons: Road noise.", 6, "Honda Sensing®", "https://automobiles.honda.com/sensing", 2, 5),
        ('BMW', '3 Series', 2024, 'Sedan', 48000, 25, 34, 'Gas', 6.5, 8, 'iDrive 8 Curved Display, Vernasca Leather, Head-up Display, M Sport Package', 17.0, 35.2, 5.6, "Pros: Powerful engines, excellent handling balance. Cons: Steering lacks feedback.", 8, "Driving Assistant Professional", "https://www.bmwusa.com/technology/driver-assistance.html", 3, 5),
        ('Mercedes-Benz', 'C-Class', 2024, 'Sedan', 49000, 23, 33, 'Gas', 6.0, 9, 'MBUX AI, Burmester 3D Audio, 64-Color Ambient Lighting, Augmented Video Nav', 12.6, 36.0, 6.0, "Pros: Stunning interior design, tech-forward. Cons: Touch-sensitive controls can be finicky.", 8, "Driver Assistance Package", "https://www.mbusa.com/en/technology/safety", 3, 5),
        ('Nissan', 'Versa', 2024, 'Sedan', 18000, 32, 40, 'Gas', 7.5, 2, 'Zero Gravity Seats, Safety Shield 360, Wireless Charging', 14.7, 31.0, 10.0, "Pros: Lots of safety tech for the price. Cons: Slow acceleration, tight back seat.", 5, "Nissan Safety Shield® 360", "https://www.nissanusa.com/experience-nissan/intelligent-mobility/safety-shield.html", 1, 5),
        ('Kia', 'Telluride', 2024, 'SUV', 38000, 20, 26, 'Gas', 8.5, 7, 'Dual Panoramic Screens, Nappa Leather, Driver Talk Intercom, Quiet Mode', 21.0, 42.4, 7.0, "Pros: Upscale feel, adult-friendly 3rd row. Cons: Fuel economy is average.", 7, "Highway Driving Assist 2", "https://www.kia.com/us/en/drive-wise", 5, 7),
        ('Toyota', 'RAV4 Hybrid', 2024, 'SUV', 32000, 41, 38, 'Gas', 9.5, 5, 'Digital Rearview Mirror, JBL Audio, Panoramic Glass Roof', 37.5, 37.8, 7.4, "Pros: High MPG, practical cargo shape. Cons: Engine can drone on highway.", 6, "Toyota Safety Sense™ 2.5", "https://www.toyota.com/safety-sense/", 6, 5),
        ('Lexus', 'RX', 2024, 'SUV', 52000, 22, 29, 'Gas', 9.5, 9, 'Mark Levinson PurePlay, Traffic Jam Assist, E-Latch Door Handles', 29.6, 37.4, 7.2, "Pros: Ultra-quiet cabin, plush ride. Cons: Fussy infotainment in older models.", 7, "Lexus Safety System+ 3.0", "https://www.lexus.com/safety", 4, 5),
        ('Subaru', 'Outback', 2024, 'SUV', 30000, 26, 32, 'Gas', 8.5, 5, 'EyeSight Driver Assist, StarTex Water-Repellent Upholstery, Roof Rails', 32.5, 39.5, 8.5, "Pros: Standard AWD, rugged utility. Cons: CVT transmission feels rubbery.", 6, "Subaru EyeSight®", "https://www.subaru.com/engineering/eyesight.html", 8, 5),
        ('Ford', 'F-150', 2024, 'Pickup', 45000, 20, 26, 'Gas', 7.5, 6, 'Pro Power Onboard (Generator), BlueCruise Hands-Free, Max Recline Seats', 52.8, 43.6, 6.0, "Pros: Class-leading towing, generator feature. Cons: Gets expensive quickly.", 9, "Ford BlueCruise Hands-Free", "https://www.ford.com/technology/bluecruise/", 8, 5),
        ('Ram', '1500', 2024, 'Pickup', 48000, 19, 24, 'Gas', 7.0, 7, 'Multi-Function Tailgate, RamBox Cargo Management, 12-inch Uconnect', 53.9, 45.2, 6.5, "Pros: Best ride quality in class (coil springs), luxury interior. Cons: Lower towing than Ford.", 5, "Advanced Safety Group", "https://www.ramtrucks.com/safety-security.html", 7, 5),
        ('Porsche', '911', 2024, 'Sports', 115000, 18, 24, 'Gas', 7.5, 9, 'PDK Transmission, Sport Chrono Package, Wet Mode', 4.6, 27.0, 3.5, "Pros: Telepathic steering, timeless design. Cons: Expensive options list, tiny back seat.", 7, "Porsche InnoDrive", "https://www.porsche.com/international/technology/innodrive/", 2, 4),
        ('Mazda', 'MX-5 Miata', 2024, 'Sports', 29000, 26, 35, 'Gas', 8.5, 5, 'Kinematic Posture Control, Bilstein Dampers, Brembo Brakes', 4.6, 0.0, 6.0, "Pros: Pure driving joy, easy manual top. Cons: Tight cabin, noisy at highway speeds.", 4, "i-Activsense®", "https://www.mazdausa.com/why-mazda/safety", 2, 2),

        # --- ELECTRIC ---
        ('Tesla', 'Model 3', 2024, 'Sedan', 40000, 130, 138, 'Electric', 7.0, 7, 'Autopilot, 15-inch Center Screen, Glass Roof, Dog Mode, Phone Key', 19.8, 35.2, 5.8, "Pros: Supercharger network, instant torque. Cons: Distracting screen-only controls.", 9, "Autopilot / FSD Capability", "https://www.tesla.com/autopilot", 3, 5),
        ('Lucid', 'Air', 2024, 'Sedan', 78000, 135, 140, 'Electric', 6.0, 9, '34-inch Glass Cockpit, DreamDrive Pro, Massage Seats, Frunk', 32.0, 41.0, 3.0, "Pros: Incredible range and power, spacious. Cons: Software bugs, low roofline entry.", 8, "DreamDrive™ Pro", "https://www.lucidmotors.com/dreamdrive", 3, 5),
        ('Hyundai', 'Ioniq 5', 2024, 'SUV', 42000, 132, 110, 'Electric', 8.0, 7, 'Vehicle-to-Load (V2L), Relaxion Reclining Seats, Sliding Center Console', 27.2, 39.4, 5.0, "Pros: Fast charging capability, retro design. Cons: No rear wiper, small frunk.", 7, "Highway Driving Assist 2", "https://www.hyundaiusa.com/us/en/safety", 4, 5),
        ('Rivian', 'R1S', 2024, 'SUV', 78000, 73, 65, 'Electric', 6.5, 9, 'Camp Mode, Pet Mode, Portable Speaker, Air Suspension', 104.0, 36.6, 3.0, "Pros: Legit off-road chops, sports car speed. Cons: Firm ride on pavement.", 8, "Rivian Driver+", "https://rivian.com/experience/technology", 10, 7),
        ('Rivian', 'R1T', 2024, 'Pickup', 75000, 70, 65, 'Electric', 6.0, 9, 'Gear Tunnel, Built-in Air Compressor, Hydraulic Roll Control', 62.0, 36.6, 3.0, "Pros: Clever storage (Gear Tunnel), incredible performance. Cons: Service center availability.", 8, "Rivian Driver+", "https://rivian.com/experience/technology", 10, 5),
        ('Chevrolet', 'Bolt EV', 2023, 'Hatchback', 27000, 120, 110, 'Electric', 7.0, 3, 'Super Cruise, Sport Mode, Regen on Demand Paddle', 16.6, 36.0, 6.5, "Pros: Great value EV, punchy acceleration. Cons: Slow DC fast charging speeds.", 8, "Super Cruise™", "https://www.chevrolet.com/electric/super-cruise", 2, 5)
    ]
    
    columns = [
        'make', 'model', 'year', 'class', 'price', 
        'city_mpg', 'hwy_mpg', 'fuel_type', 
        'reliability_score', 'luxury_score', 'features', 
        'cargo_space', 'rear_legroom', 'acceleration', 
        'review_summary', 'driver_assist_score', 'driver_assist_name', 
        'driver_assist_link', 'offroad_capability', 'seats'
    ]

    df = pd.DataFrame(cars_data, columns=columns)

    print("📥 Inserting into database...")
    try:
        df.to_sql('cars', engine, if_exists='replace', index=False, method='multi')
        print(f"✅ Database initialized successfully with {len(df)} records!")
    except Exception as e:
        print(f"❌ Error inserting data: {e}")

if __name__ == "__main__":
    init_db()