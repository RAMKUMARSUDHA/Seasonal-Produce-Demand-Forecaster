"""
WhatsApp Alert — Twilio API
Sends wastage risk alerts to supermarket managers
"""
import os
import requests

TWILIO_SID   = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM  = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
ALERT_TO     = os.getenv("ALERT_WHATSAPP_TO", "whatsapp:+91XXXXXXXXXX")

def send_wastage_alert(commodity: str, market: str, risk_level: str, reason: str, price: float) -> dict:
    """Send WhatsApp alert for HIGH wastage risk"""
    if risk_level != "HIGH":
        return {"status": "skipped", "reason": "Only HIGH risk triggers alerts"}

    emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(risk_level, "⚪")
    message = f"""
🌾 *AgriDemand Pro Alert*

{emoji} *{risk_level} WASTAGE RISK DETECTED*

📦 Commodity: {commodity}
🏪 Market: {market}
💰 Current Price: ₹{price:,.0f}/Quintal

⚠️ {reason}

👉 Action: Reduce procurement for next 3 days.

— AgriDemand Pro Auto Alert
    """.strip()

    if not TWILIO_SID or not TWILIO_TOKEN:
        print(f"⚠️ Twilio not configured. Alert message:\n{message}")
        return {
            "status": "demo",
            "message": message,
            "note": "Add TWILIO_* keys in .env for real WhatsApp alerts"
        }

    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
        data = {"From": TWILIO_FROM, "To": ALERT_TO, "Body": message}
        r = requests.post(url, data=data, auth=(TWILIO_SID, TWILIO_TOKEN), timeout=10)
        if r.status_code == 201:
            return {"status": "sent", "sid": r.json().get("sid")}
        return {"status": "failed", "error": r.text}
    except Exception as e:
        return {"status": "error", "error": str(e)}
