"""
Weather Integration — OpenWeatherMap API
Fetches current weather for TN districts and estimates price impact
"""
import requests
import os

WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "your_api_key_here")

TN_DISTRICT_COORDS = {
    "Chennai":        (13.0827, 80.2707),
    "Erode":          (11.3410, 77.7172),
    "Coimbatore":     (11.0168, 76.9558),
    "Madurai":        (9.9252, 78.1198),
    "Salem":          (11.6643, 78.1460),
    "Trichy":         (10.7905, 78.7047),
    "Tirunelveli":    (8.7139, 77.7567),
    "Vellore":        (12.9165, 79.1325),
}

def fetch_weather(district: str) -> dict:
    """Fetch current weather for a TN district"""
    coords = TN_DISTRICT_COORDS.get(district, (11.3410, 77.7172))
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": coords[0], "lon": coords[1],
            "appid": WEATHER_API_KEY, "units": "metric"
        }
        r = requests.get(url, params=params, timeout=5)
        data = r.json()
        if r.status_code == 200:
            return {
                "district": district,
                "temp_c": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "condition": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "wind_speed": data["wind"]["speed"],
            }
    except Exception as e:
        pass
    # Fallback sample data (when no API key)
    return {
        "district": district,
        "temp_c": 32.5,
        "humidity": 68,
        "condition": "Clouds",
        "description": "scattered clouds",
        "wind_speed": 3.2,
        "note": "Sample data — add OPENWEATHER_API_KEY in .env for live data"
    }

def get_price_impact(weather: dict, commodity: str) -> dict:
    """Estimate price impact based on weather conditions"""
    condition = weather.get("condition", "Clear")
    humidity = weather.get("humidity", 50)
    temp = weather.get("temp_c", 30)

    impact = "NEUTRAL"
    reason = "Normal weather conditions"
    pct = 0

    if condition in ["Rain", "Thunderstorm", "Drizzle"]:
        impact = "INCREASE"
        pct = 15
        reason = "Heavy rain disrupts transport & harvest — prices likely to rise"
    elif condition == "Clear" and temp > 38:
        impact = "INCREASE"
        pct = 10
        reason = "Extreme heat accelerates spoilage — demand for fresh produce rises"
    elif humidity > 85:
        impact = "INCREASE"
        pct = 8
        reason = "High humidity causes faster decay — supply reduces"
    elif condition in ["Clear", "Clouds"] and temp < 35:
        impact = "STABLE"
        pct = 0
        reason = "Favorable weather — normal supply expected"

    return {
        "impact": impact,
        "price_change_pct": pct,
        "reason": reason,
        "weather": weather
    }
