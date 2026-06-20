from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import pandas as pd
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from backend.models.prophet_model import forecast as prophet_forecast, train_all_models
from backend.models.xgboost_model import predict_wastage
from backend.utils.data_cleaner import merge_and_clean

router = APIRouter()

PROCESSED_CSV = os.path.join(os.path.dirname(__file__), "../../data/processed/cleaned_prices.csv")


def load_data() -> pd.DataFrame:
    if os.path.exists(PROCESSED_CSV):
        return pd.read_csv(PROCESSED_CSV, parse_dates=["date"])
    return merge_and_clean()


class TrainRequest(BaseModel):
    commodity: str = "Tomato"
    market: str = "Koyambedu"


@router.get("/price-forecast")
def get_price_forecast(
    commodity: str = Query("Tomato", description="Vegetable or fruit name"),
    market: str = Query("Koyambedu", description="Market/mandi name"),
    days: int = Query(30, ge=7, le=90, description="Forecast horizon in days")
):
    """Get price forecast for a commodity in a market"""
    try:
        df = load_data()
        result = prophet_forecast(df, commodity, market, days)
        return {
            "commodity": commodity,
            "market": market,
            "forecast_days": days,
            "data": result.to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wastage-risk")
def get_wastage_risk(
    commodity: str = Query("Tomato"),
    market: str = Query("Koyambedu"),
    current_price: float = Query(..., description="Today's modal price (₹/Quintal)")
):
    """Predict wastage risk for a commodity"""
    try:
        df = load_data()
        commodity_df = df[
            (df["commodity"].str.lower() == commodity.lower()) &
            (df["market"].str.lower() == market.lower())
        ].sort_values("date")

        if commodity_df.empty:
            commodity_df = df[df["commodity"].str.lower() == commodity.lower()].sort_values("date")

        if len(commodity_df) < 7:
            raise HTTPException(status_code=400, detail="Not enough historical data")

        price_7d_avg = commodity_df["modal_price"].tail(7).mean()
        price_30d_avg = commodity_df["modal_price"].tail(30).mean()
        today = pd.Timestamp.today()

        result = predict_wastage(
            commodity=commodity,
            market=market,
            modal_price=current_price,
            price_7d_avg=price_7d_avg,
            price_30d_avg=price_30d_avg,
            month=today.month,
            week=today.isocalendar().week
        )

        return {
            "commodity": commodity,
            "market": market,
            "current_price": current_price,
            "price_7d_avg": round(price_7d_avg, 2),
            "price_30d_avg": round(price_30d_avg, 2),
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
def get_forecast_summary(
    commodity: str = Query("Tomato"),
    market: str = Query("Koyambedu")
):
    """Get 7-day summary with procurement suggestion"""
    try:
        df = load_data()
        forecast_df = prophet_forecast(df, commodity, market, days=7)

        avg_price = forecast_df["predicted_price"].mean()
        price_trend = forecast_df["predicted_price"].iloc[-1] - forecast_df["predicted_price"].iloc[0]
        dominant_demand = forecast_df["demand_level"].mode()[0]

        if price_trend > 0 and dominant_demand == "HIGH":
            suggestion = "📈 Buy NOW — prices rising, high demand expected"
        elif price_trend < 0 and dominant_demand == "LOW":
            suggestion = "📉 HOLD — prices dropping, wait for stable period"
        else:
            suggestion = "⚖️ MODERATE stock — stable market conditions"

        return {
            "commodity": commodity,
            "market": market,
            "7_day_avg_price": round(avg_price, 2),
            "price_trend": "RISING" if price_trend > 0 else "FALLING",
            "dominant_demand": dominant_demand,
            "procurement_suggestion": suggestion,
            "forecast": forecast_df.to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train")
def train_model(req: TrainRequest):
    """Train/retrain forecast model for a specific commodity-market pair"""
    try:
        df = load_data()
        from backend.models.prophet_model import train_prophet
        train_prophet(df, req.commodity, req.market)
        return {"status": "success", "message": f"Model trained for {req.commodity} - {req.market}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train-all")
def train_all():
    """Train models for all commodity-market combinations"""
    try:
        df = load_data()
        train_all_models(df)
        return {"status": "success", "message": "All models trained"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
