# src/config.py

# File paths
DATA_PATH = "data/transit_data.csv"
MODEL_PATH = "models/model.pkl"

# Feature columns
FEATURES = ['gps_speed', 'route_id', 'weather_code', 'hour']

# Target column
TARGET = 'delayed'

# Model settings (expandable later)
RANDOM_STATE = 42
TEST_SIZE = 0.2
