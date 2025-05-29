# src/train_model.py
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import os

from preprocess import load_and_clean  # ✅ This line is required
import config


def main():
    data_path = "data/transit_data.csv"
    if not os.path.exists(data_path):
        print("❌ Data file not found!")
        return

    df = load_and_clean(config.DATA_PATH)
    X = df[config.FEATURES]
    y = df[config.TARGET]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    model = RandomForestClassifier()
    model.fit(X_train, y_train)

    joblib.dump(model, "models/model.pkl")
    print(f"✅ Accuracy: {accuracy_score(y_test, model.predict(X_test)):.2f}")

if __name__ == "__main__":
    main()
