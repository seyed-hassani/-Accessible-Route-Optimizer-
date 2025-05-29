# src/lambda_handler.py

import json
import joblib
import os
import pandas as pd

from config import MODEL_PATH, FEATURES

# Load model (only once)
model = joblib.load(MODEL_PATH)

def lambda_handler(event, context):
    """
    AWS Lambda entry point for transit delay prediction.
    Expects a JSON input with feature values.
    Example input:
    {
        "gps_speed": 42.5,
        "route_id": 3,
        "weather_code": 1,
        "hour": 17
    }
    """
    try:
        # Extract input features
        input_data = {k: event[k] for k in FEATURES}
        df = pd.DataFrame([input_data])

        # Predict
        prediction = model.predict(df)[0]
        return {
            "statusCode": 200,
            "body": json.dumps({
                "delayed": int(prediction)
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }
