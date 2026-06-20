from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.utils.data_cleaner import merge_and_clean
import pandas as pd
import shutil
import os

router = APIRouter()

RAW_DIR = os.path.join(os.path.dirname(__file__), "../../data/raw")


@router.post("/upload-kaggle")
async def upload_kaggle_csv(file: UploadFile = File(...)):
    """Upload Kaggle CSV dataset"""
    try:
        dest = os.path.join(RAW_DIR, "kaggle_prices.csv")
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
        df = merge_and_clean(kaggle_path=dest)
        return {"status": "success", "records": len(df), "message": "Data cleaned and saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch-agmarknet")
def fetch_agmarknet(days_back: int = 180):
    """Trigger Agmarknet scraper"""
    try:
        from backend.utils.agmarknet_scraper import fetch_all_tn_prices
        df = fetch_all_tn_prices(days_back=days_back)
        if not df.empty:
            df.to_csv(os.path.join(RAW_DIR, "agmarknet_prices.csv"), index=False)
            merge_and_clean()
            return {"status": "success", "records": len(df)}
        return {"status": "warning", "message": "No data fetched from Agmarknet"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-sample")
def generate_sample():
    """Generate sample data for demo/testing"""
    try:
        df = merge_and_clean()
        return {"status": "success", "records": len(df), "message": "Sample data generated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
def data_status():
    """Check data availability"""
    processed = os.path.join(os.path.dirname(__file__), "../../data/processed/cleaned_prices.csv")
    if os.path.exists(processed):
        df = pd.read_csv(processed)
        return {
            "status": "ready",
            "records": len(df),
            "commodities": list(df["commodity"].unique()),
            "markets": list(df["market"].unique())
        }
    return {"status": "empty", "message": "No data. Use /generate-sample or /upload-kaggle"}
