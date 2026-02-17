import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

def train_recommender_model(df):
    # car features 
    # to add:
    numeric_features = [
        'price', 
        'city_mpg', 
        'reliability_score', 
        'luxury_score',
        'acceleration',   
        'rear_legroom',   
        'cargo_space',
        'driver_assist_score',
        'offroad_capability',
        'seats'
    ]
    categorical_features = ['class', 'fuel_type']

    # preprocessing = normalize values
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])

    # .fit_transform = computes the params and apply transformation to same dataset in one step, efficiently calculate the necessary transformation parameters from the training data and simultaneously apply that transformation, fit() + transform()
    X = preprocessor.fit_transform(df)

    # can change neighbors on review
    model = NearestNeighbors(n_neighbors=5, algorithm='auto')
    # .fit = compute parameters needed for data transformation
    model.fit(X)
    
    return model, preprocessor

def get_recommendations(user_preferences, df, model, preprocessor):
    """
    car rows
    """
    if df.empty or model is None:
        return pd.DataFrame()

    user_df = pd.DataFrame([user_preferences])
    
    required_cols = [
        'price', 'city_mpg', 'reliability_score', 'luxury_score', 
        'acceleration', 'rear_legroom', 'cargo_space', 
        'driver_assist_score', 'offroad_capability', 'seats', 'class', 'fuel_type'
    ]
    
    # default fallback
    for col in required_cols:
        if col not in user_df.columns:
            if col == 'class': user_df[col] = 'Any'
            elif col == 'fuel_type': user_df[col] = 'Any'
            else: user_df[col] = 0

    user_vector = preprocessor.transform(user_df)
    
    # Find nearest neighbors (Get top 5)
    distances, indices = model.kneighbors(user_vector)
    
    # Return the actual car rows
    return df.iloc[indices[0]].copy()