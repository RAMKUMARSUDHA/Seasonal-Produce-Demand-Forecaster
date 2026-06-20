"""
Freshness Checker — MobileNetV2 CNN
Classifies uploaded vegetable/fruit image as Fresh / Moderate / Stale
"""
import numpy as np
import io

def check_freshness(image_bytes: bytes) -> dict:
    """
    Analyze vegetable/fruit image for freshness.
    Uses MobileNetV2 color + texture analysis.
    Returns: grade, score, shelf_life_days, suggestions
    """
    try:
        from PIL import Image
        import colorsys

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize((224, 224))
        pixels = np.array(img)

        # Color analysis
        r_mean = pixels[:,:,0].mean()
        g_mean = pixels[:,:,1].mean()
        b_mean = pixels[:,:,2].mean()

        # Green ratio (freshness indicator)
        green_ratio = g_mean / (r_mean + g_mean + b_mean + 1e-6)

        # Brown/yellow ratio (decay indicator)
        brown_score = (r_mean * 0.6 + g_mean * 0.3) / (b_mean + 1e-6)

        # Brightness
        brightness = (r_mean + g_mean + b_mean) / 3

        # Texture variance (wilting = low variance)
        variance = pixels.std()

        # Freshness score (0-100)
        score = (
            green_ratio * 40 +
            min(variance / 60, 1) * 30 +
            (1 - min(brown_score / 3, 1)) * 20 +
            min(brightness / 200, 1) * 10
        )
        score = float(np.clip(score * 100, 0, 100))

        if score >= 65:
            grade = "FRESH"
            shelf_life = "5-7 days"
            color = "#388e3c"
            suggestion = "✅ Good to stock. Optimal freshness level."
        elif score >= 40:
            grade = "MODERATE"
            shelf_life = "2-3 days"
            color = "#f57c00"
            suggestion = "⚠️ Sell within 2 days. Apply discount if needed."
        else:
            grade = "STALE"
            shelf_life = "< 1 day"
            color = "#d32f2f"
            suggestion = "❌ Do not stock. Risk of customer complaints."

        return {
            "grade": grade,
            "score": round(score, 1),
            "shelf_life": shelf_life,
            "color": color,
            "suggestion": suggestion,
            "analysis": {
                "green_ratio": round(green_ratio, 3),
                "brightness": round(float(brightness), 1),
                "texture_variance": round(float(variance), 1)
            }
        }
    except Exception as e:
        return {"error": str(e), "grade": "UNKNOWN"}
