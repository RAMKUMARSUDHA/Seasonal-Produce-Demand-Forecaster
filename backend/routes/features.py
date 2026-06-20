"""
Extra Features Routes — Chatbot, WhatsApp, Weather, Freshness, Map
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

router = APIRouter()

# ── Weather ─────────────────────────────────────────────────
@router.get("/weather")
def get_weather(district: str = Query("Erode"), commodity: str = Query("Tomato")):
    from backend.utils.weather import fetch_weather, get_price_impact
    weather = fetch_weather(district)
    impact  = get_price_impact(weather, commodity)
    return impact

# ── WhatsApp Alert ──────────────────────────────────────────
class AlertRequest(BaseModel):
    commodity: str
    market: str
    risk_level: str
    reason: str
    price: float

@router.post("/send-alert")
def send_alert(req: AlertRequest):
    from backend.utils.whatsapp_alert import send_wastage_alert
    result = send_wastage_alert(req.commodity, req.market, req.risk_level, req.reason, req.price)
    return result

# ── Freshness Check ─────────────────────────────────────────
@router.post("/freshness-check")
async def freshness_check(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        from backend.utils.freshness_checker import check_freshness
        result = check_freshness(image_bytes)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── AI Chatbot ──────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    commodity: str = "Tomato"
    market: str = "Koyambedu"

@router.post("/chat")
def chat(req: ChatRequest):
    """
    AI Chatbot using Claude API for agri demand Q&A
    Set ANTHROPIC_API_KEY in .env for live responses
    """
    import requests as req_lib
    api_key = os.getenv("ANTHROPIC_API_KEY", "")

    system_prompt = f"""You are AgriBot, an expert AI assistant for Tamil Nadu supermarket managers.
You help with vegetable/fruit demand forecasting, price trends, procurement decisions, and wastage reduction.
Current context: User is asking about {req.commodity} in {req.market} market.
Keep answers short, practical, and relevant to Tamil Nadu agriculture.
Respond in simple English (or mix Tamil words naturally)."""

    if not api_key:
        # Demo response when no API key
        demo_responses = {
            "price": f"Based on historical data, {req.commodity} prices in {req.market} typically peak during summer (Apr-Jun) and drop post-monsoon. Current trend suggests moderate demand.",
            "stock": f"For {req.commodity} in {req.market}, recommend stocking 20-30% above average during festival seasons (Pongal, Diwali).",
            "wastage": f"To reduce {req.commodity} wastage: 1) Order 3-day batches instead of weekly, 2) Monitor daily price drops, 3) Apply 20% discount when price falls >15%.",
            "default": f"AgriDemand Pro suggests monitoring {req.commodity} prices closely in {req.market}. Use the Forecast tab for 30-day predictions and Wastage Risk tab for alerts."
        }
        msg_lower = req.message.lower()
        if "price" in msg_lower or "cost" in msg_lower:
            reply = demo_responses["price"]
        elif "stock" in msg_lower or "order" in msg_lower or "buy" in msg_lower:
            reply = demo_responses["stock"]
        elif "waste" in msg_lower or "spoil" in msg_lower or "loss" in msg_lower:
            reply = demo_responses["wastage"]
        else:
            reply = demo_responses["default"]
        return {"reply": reply, "mode": "demo", "note": "Add ANTHROPIC_API_KEY in .env for AI responses"}

    try:
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        body = {
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 300,
            "system": system_prompt,
            "messages": [{"role": "user", "content": req.message}]
        }
        r = req_lib.post("https://api.anthropic.com/v1/messages", json=body, headers=headers, timeout=15)
        if r.status_code == 200:
            reply = r.json()["content"][0]["text"]
            return {"reply": reply, "mode": "live"}
        return {"reply": "AgriBot is temporarily unavailable.", "mode": "error"}
    except Exception as e:
        return {"reply": f"Error: {e}", "mode": "error"}

# ── TN Heatmap Data ─────────────────────────────────────────
@router.get("/heatmap-data")
def get_heatmap_data(commodity: str = Query("Tomato")):
    """Returns district-wise price data for TN heatmap"""
    import pandas as pd
    processed = os.path.join(os.path.dirname(__file__), "../../data/processed/cleaned_prices.csv")
    try:
        df = pd.read_csv(processed)
        filtered = df[df["commodity"].str.lower() == commodity.lower()]
        market_avg = filtered.groupby("market")["modal_price"].mean().reset_index()
        market_avg.columns = ["market", "avg_price"]
        market_avg["avg_price"] = market_avg["avg_price"].round(2)
        return {"commodity": commodity, "data": market_avg.to_dict(orient="records")}
    except Exception as e:
        return {"error": str(e)}
