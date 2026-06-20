"""
Prophet Model — Time series demand forecasting
"""
import pandas as pd
import numpy as np
from prophet import Prophet
import joblib
import os
from datetime import datetime

MODEL_DIR = os.path.join(os.path.dirname(__file__), "../../data/processed/models")
os.makedirs(MODEL_DIR, exist_ok=True)


def prepare_prophet_data(df: pd.DataFrame, commodity: str, market: str) -> pd.DataFrame:
    """Filter and format data for Prophet (needs 'ds' and 'y' columns)"""
    filtered = df[
        (df["commodity"].str.lower() == commodity.lower()) &
        (df["market"].str.lower() == market.lower())
    ].copy()

    if filtered.empty:
        # Fallback: use all markets average
        filtered = df[df["commodity"].str.lower() == commodity.lower()].copy()
        filtered = filtered.groupby("date")["modal_price"].mean().reset_index()
        filtered.columns = ["ds", "y"]
    else:
        filtered = filtered[["date", "modal_price"]].copy()
        filtered.columns = ["ds", "y"]

    filtered["ds"] = pd.to_datetime(filtered["ds"])
    filtered = filtered.dropna().sort_values("ds")
    return filtered


def train_prophet(df: pd.DataFrame, commodity: str, market: str) -> Prophet:
    """Train Prophet model for given commodity + market"""
    prophet_df = prepare_prophet_data(df, commodity, market)

    if len(prophet_df) < 30:
        raise ValueError(f"Not enough data for {commodity} in {market}. Need at least 30 records.")

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode="multiplicative",
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10,
        interval_width=0.95
    )

    # Add Indian festival seasonality
    model.add_seasonality(name="festival", period=365.25 / 4, fourier_order=5)

    model.fit(prophet_df)

    # Save model
    model_path = os.path.join(MODEL_DIR, f"prophet_{commodity}_{market}.pkl".replace(" ", "_"))
    joblib.dump(model, model_path)
    print(f"✅ Prophet model saved: {model_path}")

    return model


def load_prophet(commodity: str, market: str) -> Prophet:
    """Load saved Prophet model"""
    model_path = os.path.join(MODEL_DIR, f"prophet_{commodity}_{market}.pkl".replace(" ", "_"))
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}. Train first.")
    return joblib.load(model_path)


def forecast(df: pd.DataFrame, commodity: str, market: str, days: int = 30) -> pd.DataFrame:
    """
    Generate price + demand forecast.
    Returns DataFrame with: ds, yhat, yhat_lower, yhat_upper, demand_level
    """
    try:
        model = load_prophet(commodity, market)
    except FileNotFoundError:
        print(f"⚠️ Model not found. Training now for {commodity} - {market}...")
        model = train_prophet(df, commodity, market)

    future = model.make_future_dataframe(periods=days, freq="D")
    forecast_df = model.predict(future)

    # Keep only last N rows (future dates)
    future_forecast = forecast_df.tail(days).copy()

    # Add demand level based on predicted price vs historical average
    historical_avg = df[df["commodity"].str.lower() == commodity.lower()]["modal_price"].mean()
    future_forecast["demand_level"] = future_forecast["yhat"].apply(
        lambda x: "HIGH" if x > historical_avg * 1.15
        else ("LOW" if x < historical_avg * 0.85 else "MEDIUM")
    )

    result = future_forecast[["ds", "yhat", "yhat_lower", "yhat_upper", "demand_level"]].copy()
    result.columns = ["date", "predicted_price", "lower_bound", "upper_bound", "demand_level"]
    result["predicted_price"] = result["predicted_price"].round(2)
    result["lower_bound"] = result["lower_bound"].round(2)
    result["upper_bound"] = result["upper_bound"].round(2)

    return result.head(days)


def train_all_models(df: pd.DataFrame):
    """Train Prophet models for all commodity-market combos"""
    commodities = df["commodity"].unique()
    markets = df["market"].unique()
    success, failed = 0, 0

    for commodity in commodities:
        for market in markets:
            try:
                train_prophet(df, commodity, market)
                success += 1
            except Exception as e:
                print(f"⚠️ Skipped {commodity}-{market}: {e}")
                failed += 1

    print(f"\n✅ Training complete: {success} models trained, {failed} skipped")


if __name__ == "__main__":
    from backend.utils.data_cleaner import merge_and_clean
    df = merge_and_clean()
    result = forecast(df, "Tomato", "Koyambedu", days=30)
    print(result)
