import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

def train_recommender_model(df):
    """
    Trains a NearestNeighbors model and returns it along with the preprocessor.
    """
    numeric_features = [
        'price', 
        'city_mpg', 
        'reliability_score', 
        'luxury_score',
        'fun_score',
        'acceleration',   
        'rear_legroom',   
        'cargo_space',
        'driver_assist_score',
        'offroad_capability',
        'seats'
    ]
    categorical_features = ['class', 'fuel_type']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])

    X = preprocessor.fit_transform(df)

    model = NearestNeighbors(n_neighbors=len(df), algorithm='auto')
    model.fit(X)
    
    return model, preprocessor

def get_recommendations(user_preferences, df, model, preprocessor):
    """
    Returns car rows matching user preferences.
    """
    if df.empty or model is None:
        return pd.DataFrame()

    user_df = pd.DataFrame([user_preferences])
    
    required_cols = [
        'price', 'city_mpg', 'reliability_score', 'luxury_score', 'fun_score',
        'acceleration', 'rear_legroom', 'cargo_space', 
        'driver_assist_score', 'offroad_capability', 'seats', 'class', 'fuel_type'
    ]
    
    for col in required_cols:
        if col not in user_df.columns:
            if col == 'class': user_df[col] = 'Any'
            elif col == 'fuel_type': user_df[col] = 'Any'
            else: user_df[col] = 0

    user_vector = preprocessor.transform(user_df)
    
    distances, indices = model.kneighbors(user_vector)

    return df.iloc[indices[0]].copy()