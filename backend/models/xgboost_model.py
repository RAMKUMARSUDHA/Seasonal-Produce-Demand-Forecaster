"""
XGBoost Wastage Risk Predictor
Predicts if a product batch will face HIGH/MEDIUM/LOW wastage risk
based on price trends, season, supply-demand gap
"""
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import joblib
import os

MODEL_DIR = os.path.join(os.path.dirname(__file__), "../../data/processed/models")
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "xgboost_wastage.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create ML features from price history"""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["commodity", "market", "date"])

    # Time features
    df["month"] = df["date"].dt.month
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["day_of_year"] = df["date"].dt.dayofyear
    df["quarter"] = df["date"].dt.quarter

    # Price features
    df["price_7d_avg"] = df.groupby(["commodity", "market"])["modal_price"].transform(
        lambda x: x.rolling(7, min_periods=1).mean()
    )
    df["price_30d_avg"] = df.groupby(["commodity", "market"])["modal_price"].transform(
        lambda x: x.rolling(30, min_periods=1).mean()
    )
    df["price_change_7d"] = df.groupby(["commodity", "market"])["modal_price"].transform(
        lambda x: x.pct_change(7)
    )
    df["price_volatility"] = df.groupby(["commodity", "market"])["modal_price"].transform(
        lambda x: x.rolling(14, min_periods=1).std()
    )
    df["price_spread"] = df["max_price"] - df["min_price"]

    # Wastage risk label (derived heuristically for training)
    # High wastage = price dropping fast + high volatility
    df["wastage_risk"] = "MEDIUM"
    df.loc[
        (df["price_change_7d"] < -0.15) & (df["price_volatility"] > df["price_volatility"].quantile(0.75)),
        "wastage_risk"
    ] = "HIGH"
    df.loc[
        (df["price_change_7d"] > 0.10) & (df["price_volatility"] < df["price_volatility"].quantile(0.25)),
        "wastage_risk"
    ] = "LOW"

    return df.dropna()


def train_xgboost(df: pd.DataFrame) -> XGBClassifier:
    """Train wastage risk classifier"""
    featured_df = engineer_features(df)

    feature_cols = [
        "month", "week", "day_of_year", "quarter",
        "modal_price", "price_7d_avg", "price_30d_avg",
        "price_change_7d", "price_volatility", "price_spread"
    ]

    X = featured_df[feature_cols].fillna(0)
    y = featured_df["wastage_risk"]

    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric="mlogloss",
        random_state=42
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("\n📊 Wastage Model Performance:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    joblib.dump(model, MODEL_PATH)
    joblib.dump(le, ENCODER_PATH)
    print(f"✅ XGBoost model saved: {MODEL_PATH}")

    return model, le


def predict_wastage(commodity: str, market: str, modal_price: float,
                    price_7d_avg: float, price_30d_avg: float,
                    month: int, week: int) -> dict:
    """Predict wastage risk for given inputs"""
    try:
        model = joblib.load(MODEL_PATH)
        le = joblib.load(ENCODER_PATH)
    except FileNotFoundError:
        return {"risk_level": "UNKNOWN", "reason": "Model not trained yet. Run training first."}

    price_change_7d = (modal_price - price_7d_avg) / (price_7d_avg + 1e-6)
    price_volatility = abs(modal_price - price_30d_avg)
    price_spread = modal_price * 0.3  # estimate

    features = pd.DataFrame([{
        "month": month,
        "week": week,
        "day_of_year": week * 7,
        "quarter": (month - 1) // 3 + 1,
        "modal_price": modal_price,
        "price_7d_avg": price_7d_avg,
        "price_30d_avg": price_30d_avg,
        "price_change_7d": price_change_7d,
        "price_volatility": price_volatility,
        "price_spread": price_spread
    }])

    pred = model.predict(features)[0]
    proba = model.predict_proba(features)[0]
    risk_level = le.inverse_transform([pred])[0]

    reasons = {
        "HIGH": "Price dropping rapidly with high market volatility — overstocking risk!",
        "MEDIUM": "Moderate price fluctuation — monitor stock levels.",
        "LOW": "Stable prices with upward trend — safe to stock."
    }

    return {
        "risk_level": risk_level,
        "confidence": round(float(max(proba)) * 100, 1),
        "reason": reasons[risk_level],
        "price_change_7d_pct": round(price_change_7d * 100, 2)
    }


if __name__ == "__main__":
    from backend.utils.data_cleaner import merge_and_clean
    df = merge_and_clean()
    train_xgboost(df)

    result = predict_wastage("Tomato", "Koyambedu", 2000, 2500, 2300, 6, 24)
    print("\n🔍 Wastage Prediction:", result)
