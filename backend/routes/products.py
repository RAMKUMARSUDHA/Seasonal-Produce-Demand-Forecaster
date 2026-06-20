from fastapi import APIRouter
import pandas as pd
import os

router = APIRouter()

PROCESSED_CSV = os.path.join(os.path.dirname(__file__), "../../data/processed/cleaned_prices.csv")

PRODUCTS = ["Tomato", "Onion", "Potato", "Brinjal", "Carrot", "Banana", "Mango", "Watermelon"]
MARKETS = ["Koyambedu", "Erode", "Coimbatore", "Madurai", "Salem"]


@router.get("/list")
def get_products():
    return {"products": PRODUCTS, "markets": MARKETS}


@router.get("/price-history")
def get_price_history(commodity: str = "Tomato", market: str = "Koyambedu", days: int = 90):
    try:
        df = pd.read_csv(PROCESSED_CSV, parse_dates=["date"])
        filtered = df[
            (df["commodity"].str.lower() == commodity.lower()) &
            (df["market"].str.lower() == market.lower())
        ].sort_values("date").tail(days)

        return {
            "commodity": commodity,
            "market": market,
            "data": filtered[["date", "min_price", "max_price", "modal_price"]].to_dict(orient="records")
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/stats")
def get_stats(commodity: str = "Tomato", market: str = "Koyambedu"):
    try:
        df = pd.read_csv(PROCESSED_CSV, parse_dates=["date"])
        filtered = df[
            (df["commodity"].str.lower() == commodity.lower()) &
            (df["market"].str.lower() == market.lower())
        ]

        if filtered.empty:
            return {"error": "No data found"}

        return {
            "commodity": commodity,
            "market": market,
            "total_records": len(filtered),
            "avg_price": round(filtered["modal_price"].mean(), 2),
            "min_price": round(filtered["modal_price"].min(), 2),
            "max_price": round(filtered["modal_price"].max(), 2),
            "latest_price": round(filtered.sort_values("date").iloc[-1]["modal_price"], 2),
            "date_range": {
                "from": str(filtered["date"].min().date()),
                "to": str(filtered["date"].max().date())
            }
        }
    except Exception as e:
        return {"error": str(e)}
