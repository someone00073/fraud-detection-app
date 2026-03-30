import pandas as pd
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

MODEL_PATH = "model.pkl"
COLUMNS_PATH = "columns.pkl"
DATASET_PATH = "dataset/data.csv"


def train_model():
    print("🔄 Training model using CSV...")

    df = pd.read_csv(DATASET_PATH)

    # Encode categorical columns
    le_cat = LabelEncoder()
    le_city = LabelEncoder()
    le_dev = LabelEncoder()

    df['category_enc'] = le_cat.fit_transform(df['category'])
    df['city_enc'] = le_city.fit_transform(df['city'])
    df['device_enc'] = le_dev.fit_transform(df['device_type'])

    feature_cols = [
        'amount',
        'transaction_frequency',
        'hour',
        'new_device',
        'new_city',
        'category_enc',
        'city_enc',
        'device_enc'
    ]

    X = df[feature_cols]
    y = df['fraud']

    model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    class_weight='balanced',
    random_state=42
)
    model.fit(X, y)

    # Save model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    encoders = {
        "category": le_cat,
        "city": le_city,
        "device_type": le_dev
    }

    with open(COLUMNS_PATH, "wb") as f:
        pickle.dump(encoders, f)

    print("✅ Model trained & saved!")

    return model, encoders


def load_model():
    if not os.path.exists(MODEL_PATH):
        return train_model()

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    with open(COLUMNS_PATH, "rb") as f:
        encoders = pickle.load(f)

    return model, encoders


def encode_input(data, encoders):
    le_cat = encoders['category']
    le_city = encoders['city']
    le_dev = encoders['device_type']

    def safe(le, val):
        return le.transform([val])[0] if val in le.classes_ else 0

    return [[
        float(data['amount']),
        float(data['transaction_frequency']),
        float(data['hour']),
        float(data['new_device']),
        float(data['new_city']),
        safe(le_cat, data['category']),
        safe(le_city, data['city']),
        safe(le_dev, data['device_type'])
    ]]

if __name__ == "__main__":
    train_model()