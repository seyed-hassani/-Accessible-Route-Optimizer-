# src/preprocess.py

import pandas as pd

def load_and_clean(filepath):
    """
    Loads CSV and performs basic cleaning and feature creation.
    """
    print(f"📂 Loading data from {filepath}...")
    df = pd.read_csv(filepath)

    # Drop rows with missing values (you can adjust this logic)
    df.dropna(inplace=True)

    # Convert timestamp column to datetime, if it exists
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour

    # Example: map weather conditions to numeric code
    if 'weather' in df.columns:
        weather_map = {'Clear': 0, 'Rain': 1, 'Snow': 2, 'Fog': 3}
        df['weather_code'] = df['weather'].map(weather_map).fillna(0).astype(int)

    print(f"✅ Cleaned dataset with {len(df)} rows.")
    return df
