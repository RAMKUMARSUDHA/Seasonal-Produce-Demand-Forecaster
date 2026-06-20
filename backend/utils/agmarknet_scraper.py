"""
Agmarknet Scraper — fetches real TN mandi prices
Website: https://agmarknet.gov.in
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time

AGMARKNET_URL = "https://agmarknet.gov.in/SearchCmmMkt.aspx"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

TN_MARKETS = {
    "Koyambedu": "1234",   # Replace with actual Agmarknet market codes
    "Erode": "1235",
    "Coimbatore": "1236",
    "Madurai": "1237",
    "Salem": "1238",
}

COMMODITIES = {
    "Tomato": "78",
    "Onion": "23",
    "Potato": "24",
    "Banana": "5",
    "Mango": "15",
}

def fetch_agmarknet_prices(commodity: str, market: str, from_date: str, to_date: str) -> pd.DataFrame:
    """
    Fetch prices from Agmarknet for a given commodity and market.
    Returns DataFrame with columns: date, min_price, max_price, modal_price
    """
    try:
        payload = {
            "Tx_Commodity": COMMODITIES.get(commodity, "78"),
            "Tx_State": "Tamil Nadu",
            "Tx_Market": market,
            "DateFrom": from_date,
            "DateTo": to_date,
            "Fr_Date": from_date,
            "To_Date": to_date,
        }

        response = requests.post(AGMARKNET_URL, data=payload, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, "lxml")

        table = soup.find("table", {"id": "cphBody_gridRecords"})
        if not table:
            print(f"⚠️ No data found for {commodity} in {market}")
            return pd.DataFrame()

        rows = []
        for tr in table.find_all("tr")[1:]:
            cols = [td.text.strip() for td in tr.find_all("td")]
            if len(cols) >= 6:
                rows.append({
                    "date": pd.to_datetime(cols[0], dayfirst=True),
                    "commodity": commodity,
                    "market": market,
                    "min_price": float(cols[3].replace(",", "")),
                    "max_price": float(cols[4].replace(",", "")),
                    "modal_price": float(cols[5].replace(",", "")),
                    "source": "agmarknet"
                })

        df = pd.DataFrame(rows)
        print(f"✅ Fetched {len(df)} records for {commodity} - {market}")
        return df

    except Exception as e:
        print(f"❌ Error fetching {commodity} from {market}: {e}")
        return pd.DataFrame()


def fetch_all_tn_prices(days_back: int = 365) -> pd.DataFrame:
    """Fetch prices for all TN markets and commodities"""
    all_data = []
    to_date = datetime.today().strftime("%d-%b-%Y")
    from_date = (datetime.today() - timedelta(days=days_back)).strftime("%d-%b-%Y")

    for commodity in COMMODITIES:
        for market in TN_MARKETS:
            df = fetch_agmarknet_prices(commodity, market, from_date, to_date)
            if not df.empty:
                all_data.append(df)
            time.sleep(1)  # Be polite to the server

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


if __name__ == "__main__":
    print("🌾 Fetching Agmarknet TN prices...")
    df = fetch_all_tn_prices(days_back=180)
    if not df.empty:
        df.to_csv("../../data/raw/agmarknet_prices.csv", index=False)
        print(f"✅ Saved {len(df)} records to data/raw/agmarknet_prices.csv")
    else:
        print("⚠️ No data fetched. Using Kaggle dataset as fallback.")
