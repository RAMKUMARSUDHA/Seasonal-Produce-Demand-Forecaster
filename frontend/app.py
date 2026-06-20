"""
AgriDemand Pro v2.0 — Streamlit Frontend
All 5 new features: Chatbot, WhatsApp Alert, Weather, Freshness, Heatmap
"""
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

API_BASE = "http://localhost:8000/api"

st.set_page_config(page_title="AgriDemand Pro", page_icon="🌾", layout="wide")

st.markdown("""
<style>
.main-header {
    font-size:2.5rem; font-weight:800;
    background:linear-gradient(90deg,#2E7D32,#66BB6A);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.chat-user { background:#e3f2fd; padding:0.7rem 1rem; border-radius:12px 12px 2px 12px; margin:0.3rem 0; }
.chat-bot  { background:#f1f8e9; padding:0.7rem 1rem; border-radius:12px 12px 12px 2px; margin:0.3rem 0; border-left:3px solid #2E7D32; }
</style>""", unsafe_allow_html=True)

def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def api_post(path, params=None, json=None, files=None):
    try:
        r = requests.post(f"{API_BASE}{path}", params=params, json=json, files=files, timeout=60)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=300)
def fetch_products():
    try:
        r = requests.get(f"{API_BASE}/products/list", timeout=5)
        return r.json()
    except:
        return {
            "products": ["Tomato","Onion","Potato","Brinjal","Carrot","Banana","Mango","Watermelon"],
            "markets":  ["Koyambedu","Erode","Coimbatore","Madurai","Salem"]
        }

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌾 AgriDemand Pro")
    st.markdown("*v2.0 — Tamil Nadu Supermarket AI*")
    st.divider()
    meta = fetch_products()
    products = meta["products"]
    markets  = meta["markets"]
    selected_commodity = st.selectbox("🥦 Commodity", products)
    selected_market    = st.selectbox("🏪 Market", markets)
    forecast_days      = st.slider("📅 Forecast Days", 7, 90, 30)
    current_price      = st.number_input("💰 Today's Price (₹/Quintal)", min_value=100.0, value=2500.0, step=50.0)
    st.divider()
    if st.button("🔄 Generate Sample Data"):
        with st.spinner("Generating..."):
            result = api_post("/data/generate-sample")
            if "records" in result:
                st.success(f"✅ {result['records']} records!")
                st.cache_data.clear()
            else:
                st.error(str(result))
    uploaded = st.file_uploader("📂 Upload Kaggle CSV", type=["csv"])
    if uploaded:
        files = {"file": (uploaded.name, uploaded.getvalue(), "text/csv")}
        r = api_post("/data/upload-kaggle", files=files)
        st.success("✅ Uploaded!" if "records" in r else "❌ Failed")

# ── Header ───────────────────────────────────────────────────
st.markdown('<p class="main-header">🌾 AgriDemand Pro v2.0</p>', unsafe_allow_html=True)
st.markdown(f"**{selected_commodity}** · **{selected_market}** · {forecast_days}-day forecast")
st.divider()

# 7 tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📈 Forecast", "📊 History", "⚠️ Wastage Risk",
    "🌦️ Weather Impact", "📸 Freshness Check",
    "🤖 AI Chatbot", "🗺️ TN Heatmap"
])

# ── TAB 1: Forecast ──────────────────────────────────────────
with tab1:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("### 📋 7-Day Summary")
        summary = api_get("/forecast/summary", {"commodity": selected_commodity, "market": selected_market})
        if "7_day_avg_price" in summary:
            trend_icon = "📈" if summary["price_trend"] == "RISING" else "📉"
            demand_icons = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
            st.metric("Avg Price (7d)", f"₹{summary['7_day_avg_price']:,.0f}")
            st.metric("Trend", f"{trend_icon} {summary['price_trend']}")
            st.metric("Demand", f"{demand_icons.get(summary['dominant_demand'],'⚪')} {summary['dominant_demand']}")
            st.info(summary.get("procurement_suggestion", ""))
        else:
            st.warning("Generate sample data from sidebar →")
    with col2:
        st.markdown(f"### 📈 {forecast_days}-Day Price Forecast")
        with st.spinner("Generating forecast..."):
            result = api_get("/forecast/price-forecast", {"commodity": selected_commodity, "market": selected_market, "days": forecast_days})
        if "data" in result and result["data"]:
            df = pd.DataFrame(result["data"])
            df["date"] = pd.to_datetime(df["date"])
            color_map = {"HIGH":"#d32f2f","MEDIUM":"#f57c00","LOW":"#388e3c"}
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["date"], y=df["upper_bound"], fill=None, mode="lines", line=dict(color="rgba(46,125,50,0.2)"), name="Upper"))
            fig.add_trace(go.Scatter(x=df["date"], y=df["lower_bound"], fill="tonexty", mode="lines", line=dict(color="rgba(46,125,50,0.2)"), fillcolor="rgba(46,125,50,0.1)", name="Lower"))
            fig.add_trace(go.Scatter(x=df["date"], y=df["predicted_price"], mode="lines+markers", name="Forecast",
                line=dict(color="#2E7D32", width=2.5),
                marker=dict(color=[color_map.get(d,"#2E7D32") for d in df["demand_level"]], size=8)))
            fig.update_layout(xaxis_title="Date", yaxis_title="₹/Quintal", hovermode="x unified", height=380)
            st.plotly_chart(fig, use_container_width=True)
            st.download_button("⬇️ Download CSV", df.to_csv(index=False),
                f"forecast_{selected_commodity}_{selected_market}.csv", "text/csv")
        else:
            st.warning("No data. Generate sample data from sidebar.")

# ── TAB 2: History ───────────────────────────────────────────
with tab2:
    st.markdown(f"### 📊 Price History — {selected_commodity} · {selected_market}")
    hist_days = st.slider("Show last N days", 30, 365, 90)
    history = api_get("/products/price-history", {"commodity": selected_commodity, "market": selected_market, "days": hist_days})
    if "data" in history and history["data"]:
        hdf = pd.DataFrame(history["data"])
        hdf["date"] = pd.to_datetime(hdf["date"])
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=hdf["date"], y=hdf["max_price"], mode="lines", name="Max", line=dict(color="#ef5350", dash="dot")))
        fig3.add_trace(go.Scatter(x=hdf["date"], y=hdf["modal_price"], mode="lines", name="Modal", line=dict(color="#2E7D32", width=2)))
        fig3.add_trace(go.Scatter(x=hdf["date"], y=hdf["min_price"], mode="lines", name="Min", line=dict(color="#42a5f5", dash="dot")))
        fig3.update_layout(xaxis_title="Date", yaxis_title="₹/Quintal", hovermode="x unified", height=400)
        st.plotly_chart(fig3, use_container_width=True)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Average", f"₹{hdf['modal_price'].mean():,.0f}")
        c2.metric("Highest", f"₹{hdf['max_price'].max():,.0f}")
        c3.metric("Lowest",  f"₹{hdf['min_price'].min():,.0f}")
        c4.metric("Latest",  f"₹{hdf['modal_price'].iloc[-1]:,.0f}")
    else:
        st.warning("No history data. Generate sample data first.")

# ── TAB 3: Wastage Risk ──────────────────────────────────────
with tab3:
    st.markdown("### ⚠️ Wastage Risk Analyzer")
    if st.button("🔍 Analyze Wastage Risk"):
        with st.spinner("Analyzing..."):
            risk = api_get("/forecast/wastage-risk", {"commodity": selected_commodity, "market": selected_market, "current_price": current_price})
        if "risk_level" in risk:
            rl = risk["risk_level"]
            color = {"HIGH":"#d32f2f","MEDIUM":"#f57c00","LOW":"#388e3c"}.get(rl,"#666")
            icon  = {"HIGH":"🔴","MEDIUM":"🟡","LOW":"🟢"}.get(rl,"⚪")
            st.markdown(f"""
            <div style="background:{color}15;border-left:5px solid {color};padding:1.5rem;border-radius:8px;">
                <h2 style="color:{color}">{icon} {rl} WASTAGE RISK</h2>
                <p style="font-size:1.1rem">{risk.get('reason','')}</p>
                <p><b>Confidence:</b> {risk.get('confidence',0)}% | <b>7d Change:</b> {risk.get('price_change_7d_pct',0):+.1f}%</p>
            </div>""", unsafe_allow_html=True)

            # Auto send WhatsApp alert if HIGH
            if rl == "HIGH":
                st.warning("🔴 HIGH risk detected! Sending WhatsApp alert...")
                alert = api_post("/features/send-alert", json={
                    "commodity": selected_commodity, "market": selected_market,
                    "risk_level": rl, "reason": risk.get("reason",""), "price": current_price
                })
                if alert.get("status") == "sent":
                    st.success("✅ WhatsApp alert sent to manager!")
                elif alert.get("status") == "demo":
                    st.info(f"📱 Demo mode alert:\n{alert.get('message','')}")
        else:
            st.info("Train model first: run eda_and_train.py")

# ── TAB 4: Weather Impact ────────────────────────────────────
with tab4:
    st.markdown("### 🌦️ Weather Impact on Prices")
    district = st.selectbox("Select District", ["Erode","Chennai","Coimbatore","Madurai","Salem","Trichy"])
    if st.button("🌤️ Check Weather Impact"):
        with st.spinner("Fetching weather..."):
            weather_data = api_get("/features/weather", {"district": district, "commodity": selected_commodity})
        if "impact" in weather_data:
            w = weather_data["weather"]
            impact = weather_data["impact"]
            pct = weather_data["price_change_pct"]
            impact_color = {"INCREASE":"#d32f2f","STABLE":"#388e3c","NEUTRAL":"#666"}.get(impact,"#666")
            impact_icon  = {"INCREASE":"📈","STABLE":"➡️","NEUTRAL":"➡️"}.get(impact,"➡️")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 🌡️ Current Weather")
                st.metric("Temperature", f"{w.get('temp_c',0):.1f}°C")
                st.metric("Humidity", f"{w.get('humidity',0)}%")
                st.metric("Condition", w.get('condition','N/A'))
                st.metric("Wind Speed", f"{w.get('wind_speed',0)} m/s")
                if "note" in w:
                    st.caption(w["note"])
            with c2:
                st.markdown("#### 💰 Price Impact")
                st.markdown(f"""
                <div style="background:{impact_color}15;border-left:5px solid {impact_color};padding:1.5rem;border-radius:8px;">
                    <h3 style="color:{impact_color}">{impact_icon} {impact}</h3>
                    <h2 style="color:{impact_color}">+{pct}% Expected</h2>
                    <p>{weather_data.get('reason','')}</p>
                </div>""", unsafe_allow_html=True)
                if pct > 0:
                    new_price = current_price * (1 + pct/100)
                    st.metric("Projected Price", f"₹{new_price:,.0f}", delta=f"+{pct}%")
        else:
            st.error("Weather fetch failed. Check API connection.")

# ── TAB 5: Freshness Check ───────────────────────────────────
with tab5:
    st.markdown("### 📸 Vegetable Freshness Checker")
    st.markdown("Upload a photo of the vegetable/fruit to check freshness grade")
    uploaded_img = st.file_uploader("📷 Upload Image", type=["jpg","jpeg","png","webp"])
    if uploaded_img:
        col1, col2 = st.columns(2)
        with col1:
            st.image(uploaded_img, caption="Uploaded Image", use_container_width=True)
        with col2:
            with st.spinner("Analyzing freshness..."):
                files = {"file": (uploaded_img.name, uploaded_img.getvalue(), uploaded_img.type)}
                result = api_post("/features/freshness-check", files=files)
            if "grade" in result and result["grade"] != "UNKNOWN":
                color = result.get("color","#666")
                grade = result["grade"]
                score = result.get("score", 0)
                st.markdown(f"""
                <div style="background:{color}15;border-left:5px solid {color};padding:1.5rem;border-radius:8px;margin-top:1rem;">
                    <h2 style="color:{color}">{'🟢' if grade=='FRESH' else '🟡' if grade=='MODERATE' else '🔴'} {grade}</h2>
                    <h3>Score: {score}/100</h3>
                    <p><b>Shelf Life:</b> {result.get('shelf_life','')}</p>
                    <p>{result.get('suggestion','')}</p>
                </div>""", unsafe_allow_html=True)

                st.markdown("#### 🔬 Analysis Details")
                analysis = result.get("analysis", {})
                a1,a2,a3 = st.columns(3)
                a1.metric("Green Ratio", f"{analysis.get('green_ratio',0):.3f}")
                a2.metric("Brightness", f"{analysis.get('brightness',0):.1f}")
                a3.metric("Texture Variance", f"{analysis.get('texture_variance',0):.1f}")
            else:
                st.error(f"Analysis failed: {result.get('error','Unknown error')}")

# ── TAB 6: AI Chatbot ────────────────────────────────────────
with tab6:
    st.markdown("### 🤖 AgriBot — AI Assistant")
    st.markdown("Ask anything about demand, prices, procurement, or wastage!")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "bot", "text": f"👋 Vanakkam! I'm AgriBot. Ask me anything about {selected_commodity} prices, demand forecasts, or procurement tips for {selected_market} market!"}
        ]

    # Display chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">👤 {msg["text"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bot">🌾 {msg["text"]}</div>', unsafe_allow_html=True)

    # Input
    user_input = st.chat_input("Ask AgriBot...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "text": user_input})
        with st.spinner("AgriBot thinking..."):
            resp = api_post("/features/chat", json={
                "message": user_input,
                "commodity": selected_commodity,
                "market": selected_market
            })
        reply = resp.get("reply", "Sorry, I couldn't process that.")
        mode  = resp.get("mode", "demo")
        if mode == "demo":
            reply += "\n\n*(Demo mode — add ANTHROPIC_API_KEY in .env for live AI)*"
        st.session_state.chat_history.append({"role": "bot", "text": reply})
        st.rerun()

    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = [{"role": "bot", "text": "Chat cleared! How can I help you?"}]
        st.rerun()

    st.markdown("**Quick Questions:**")
    qcols = st.columns(3)
    quick_qs = [
        f"What's the demand trend for {selected_commodity}?",
        f"How to reduce wastage in {selected_market}?",
        f"Best time to stock {selected_commodity}?"
    ]
    for i, q in enumerate(quick_qs):
        if qcols[i].button(q, key=f"quick_{i}"):
            st.session_state.chat_history.append({"role": "user", "text": q})
            resp = api_post("/features/chat", json={"message": q, "commodity": selected_commodity, "market": selected_market})
            st.session_state.chat_history.append({"role": "bot", "text": resp.get("reply","...")})
            st.rerun()

# ── TAB 7: TN Heatmap ────────────────────────────────────────
with tab7:
    st.markdown(f"### 🗺️ Tamil Nadu Price Heatmap — {selected_commodity}")

    heatmap_data = api_get("/features/heatmap-data", {"commodity": selected_commodity})
    if "data" in heatmap_data and heatmap_data["data"]:
        hdf = pd.DataFrame(heatmap_data["data"])

        # Bar chart (map alternative since TN geojson needs external file)
        fig_bar = px.bar(hdf.sort_values("avg_price", ascending=True),
            x="avg_price", y="market", orientation="h",
            color="avg_price", color_continuous_scale="RdYlGn_r",
            title=f"{selected_commodity} — Average Price by Market (₹/Quintal)",
            labels={"avg_price": "Avg Price (₹/Quintal)", "market": "Market"})
        fig_bar.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

        # Bubble chart — size = price
        fig_bubble = px.scatter(hdf, x="market", y="avg_price",
            size="avg_price", color="avg_price",
            color_continuous_scale="RdYlGn_r",
            title="Market Price Bubble Chart",
            labels={"avg_price": "₹/Quintal", "market": "Market"})
        fig_bubble.update_layout(height=350)
        st.plotly_chart(fig_bubble, use_container_width=True)

        # Table
        st.dataframe(hdf.sort_values("avg_price").reset_index(drop=True), use_container_width=True, hide_index=True)
        cheapest  = hdf.loc[hdf["avg_price"].idxmin(), "market"]
        costliest = hdf.loc[hdf["avg_price"].idxmax(), "market"]
        st.success(f"💡 Best buy: **{cheapest}** | Most expensive: **{costliest}**")
    else:
        st.warning("Generate sample data from sidebar first.")

# ── Footer ───────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center;color:#666;font-size:0.85rem'>
🌾 AgriDemand Pro v2.0 · Tamil Nadu Supermarkets · Prophet + XGBoost + FastAPI + Claude AI
</div>""", unsafe_allow_html=True)
