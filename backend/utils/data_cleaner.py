"""
Data Cleaner — merges Kaggle + Agmarknet data, cleans and saves to processed/
Kaggle dataset: https://www.kaggle.com/datasets/kianwee/agricultural-raw-material-prices-1990-2020
or: https://www.kaggle.com/datasets/srinivas1/agricuture-crops-production-in-india
"""
import pandas as pd
import numpy as np
import os

RAW_DIR = os.path.join(os.path.dirname(__file__), "../../data/raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "../../data/processed")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


def generate_sample_data() -> pd.DataFrame:
    """
    Generate realistic sample data for TN vegetables (used when Kaggle/Agmarknet unavailable)
    This is for development/demo. Replace with real data in production.
    """
    np.random.seed(42)
    dates = pd.date_range(start="2020-01-01", end="2024-12-31", freq="D")

    products = {
        "Tomato":      {"base": 2500, "seasonal_amp": 1500, "peak_month": 2},
        "Onion":       {"base": 1800, "seasonal_amp": 1200, "peak_month": 11},
        "Potato":      {"base": 1500, "seasonal_amp": 800,  "peak_month": 3},
        "Brinjal":     {"base": 1200, "seasonal_amp": 600,  "peak_month": 7},
        "Carrot":      {"base": 2000, "seasonal_amp": 900,  "peak_month": 1},
        "Banana":      {"base": 3000, "seasonal_amp": 700,  "peak_month": 5},
        "Mango":       {"base": 4000, "seasonal_amp": 3000, "peak_month": 5},
        "Watermelon":  {"base": 800,  "seasonal_amp": 600,  "peak_month": 4},
    }

    markets = ["Koyambedu", "Erode", "Coimbatore", "Madurai", "Salem"]
    rows = []

    for product, params in products.items():
        for market in markets:
            market_factor = np.random.uniform(0.85, 1.15)
            for date in dates:
                # Seasonal pattern
                seasonal = params["seasonal_amp"] * np.sin(
                    2 * np.pi * (date.month - params["peak_month"]) / 12
                )
                # Trend + noise
                trend = params["base"] + (date.year - 2020) * 100
                noise = np.random.normal(0, params["base"] * 0.08)
                modal = max(200, (trend + seasonal + noise) * market_factor)

                rows.append({
                    "date": date,
                    "commodity": product,
                    "market": market,
                    "min_price": round(modal * 0.85, 2),
                    "max_price": round(modal * 1.15, 2),
                    "modal_price": round(modal, 2),
                    "source": "sample"
                })

    return pd.DataFrame(rows)


def load_kaggle_data(filepath: str) -> pd.DataFrame:
    """Load and standardize Kaggle CSV"""
    try:
        df = pd.read_csv(filepath)
        print(f"✅ Kaggle data loaded: {len(df)} rows")
        print(f"   Columns: {list(df.columns)}")

        # Standardize column names (adjust based on actual Kaggle dataset)
        rename_map = {
            "Date": "date", "Commodity": "commodity", "Market": "market",
            "Min Price": "min_price", "Max Price": "max_price", "Modal Price": "modal_price",
            "State": "state"
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

        df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
        df = df.dropna(subset=["date"])

        # Filter TN only if state column exists
        if "state" in df.columns:
            df = df[df["state"].str.contains("Tamil Nadu", case=False, na=False)]

        df["source"] = "kaggle"
        return df[["date", "commodity", "market", "min_price", "max_price", "modal_price", "source"]]

    except Exception as e:
        print(f"❌ Kaggle load error: {e}")
        return pd.DataFrame()


def merge_and_clean(kaggle_path: str = None, agmarknet_path: str = None) -> pd.DataFrame:
    """Merge both sources, clean, and save"""
    frames = []

    # Load Kaggle
    if kaggle_path and os.path.exists(kaggle_path):
        kaggle_df = load_kaggle_data(kaggle_path)
        if not kaggle_df.empty:
            frames.append(kaggle_df)

    # Load Agmarknet
    agmarknet_file = os.path.join(RAW_DIR, "agmarknet_prices.csv")
    if agmarknet_path and os.path.exists(agmarknet_path):
        agmarknet_file = agmarknet_path
    if os.path.exists(agmarknet_file):
        ag_df = pd.read_csv(agmarknet_file, parse_dates=["date"])
        frames.append(ag_df)
        print(f"✅ Agmarknet data loaded: {len(ag_df)} rows")

    # Fallback to sample data
    if not frames:
        print("⚠️ No real data found. Generating sample data for demo...")
        frames.append(generate_sample_data())

    df = pd.concat(frames, ignore_index=True)

    # Clean
    df = df.dropna(subset=["date", "modal_price"])
    df["modal_price"] = pd.to_numeric(df["modal_price"], errors="coerce")
    df["min_price"] = pd.to_numeric(df["min_price"], errors="coerce")
    df["max_price"] = pd.to_numeric(df["max_price"], errors="coerce")
    df = df[df["modal_price"] > 0]
    df = df.drop_duplicates(subset=["date", "commodity", "market"])
    df = df.sort_values("date")

    # Remove outliers (3 sigma)
    for commodity in df["commodity"].unique():
        mask = df["commodity"] == commodity
        mean = df.loc[mask, "modal_price"].mean()
        std = df.loc[mask, "modal_price"].std()
        df = df[~(mask & (abs(df["modal_price"] - mean) > 3 * std))]

    # Save
    output_path = os.path.join(PROCESSED_DIR, "cleaned_prices.csv")
    df.to_csv(output_path, index=False)
    print(f"✅ Cleaned data saved: {len(df)} rows → {output_path}")

    return df


if __name__ == "__main__":
    df = merge_and_clean()
    print(df.head())
    print(f"\nProducts: {df['commodity'].unique()}")
    print(f"Markets: {df['market'].unique()}")
    print(f"Date range: {df['date'].min()} → {df['date'].max()}")
