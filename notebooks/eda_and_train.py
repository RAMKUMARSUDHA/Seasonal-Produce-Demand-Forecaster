# ============================================================
# AgriDemand Pro — EDA & Model Training Script
# Run: python notebooks/eda_and_train.py
# ============================================================
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import matplotlib.pyplot as plt
from backend.utils.data_cleaner import merge_and_clean
from backend.models.prophet_model import train_prophet, forecast
from backend.models.xgboost_model import train_xgboost

# 1. Load & Clean
print("=" * 60)
print("STEP 1: Loading and cleaning data...")
df = merge_and_clean()
print(f"Shape: {df.shape}")
print(f"Date range: {df['date'].min().date()} -> {df['date'].max().date()}")
print(f"Products: {sorted(df['commodity'].unique())}")
print(f"Markets:  {sorted(df['market'].unique())}")

# 2. EDA Plots
print("\nSTEP 2: Generating EDA plots...")
os.makedirs("notebooks/plots", exist_ok=True)

fig, ax = plt.subplots(figsize=(14, 6))
df.boxplot(column="modal_price", by="commodity", ax=ax)
plt.title("Price Distribution by Commodity")
plt.suptitle("")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("notebooks/plots/01_price_distribution.png", dpi=150)
plt.close()

fig, ax = plt.subplots(figsize=(14, 6))
for product in ["Tomato", "Onion", "Potato"]:
    prod_df = df[df["commodity"] == product].groupby("date")["modal_price"].mean()
    ax.plot(prod_df.index, prod_df.values, label=product, linewidth=1.5)
ax.set_title("Price Trends Over Time")
ax.legend()
plt.tight_layout()
plt.savefig("notebooks/plots/02_price_trends.png", dpi=150)
plt.close()
print("Plots saved to notebooks/plots/")

# 3. Train Prophet
print("\nSTEP 3: Training Prophet models...")
for commodity in ["Tomato", "Onion", "Banana"]:
    for market in ["Koyambedu", "Erode"]:
        try:
            train_prophet(df, commodity, market)
        except Exception as e:
            print(f"Skipped {commodity}-{market}: {e}")

# 4. Train XGBoost
print("\nSTEP 4: Training XGBoost wastage model...")
train_xgboost(df)

# 5. Sample Forecast
print("\nSTEP 5: Sample 7-day forecast (Tomato, Koyambedu):")
result = forecast(df, "Tomato", "Koyambedu", days=7)
print(result.to_string(index=False))

print("\n" + "="*60)
print("All training complete!")
print("Models: data/processed/models/")
print("Plots:  notebooks/plots/")
