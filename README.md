# 🌾 AgriDemand Pro
### Seasonal Produce Demand Forecaster for Tamil Nadu Supermarkets

> ML + Prophet-powered platform that forecasts vegetable/fruit demand using real TN mandi prices — reducing wastage and optimizing procurement.

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| ML Models | Prophet, XGBoost, scikit-learn |
| Backend | FastAPI, SQLAlchemy |
| Frontend | Streamlit, Plotly |
| Database | MySQL 8.0 |
| Data | Agmarknet scraper + Kaggle CSV |
| Deploy | Docker + docker-compose |

---

## 🚀 Quick Start

### Option 1 — Docker (Recommended)
```bash
docker-compose up --build
```
- Frontend → http://localhost:8501
- API Docs → http://localhost:8000/docs

### Option 2 — Manual Setup

**Step 1: Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 2: Setup MySQL**
```bash
mysql -u root -p < backend/database/schema.sql
```

**Step 3: Configure .env**
```bash
cp .env.example .env
# Edit DATABASE_URL with your MySQL credentials
```

**Step 4: Generate sample data + train models**
```bash
python notebooks/eda_and_train.py
```

**Step 5: Start backend**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Step 6: Start frontend (new terminal)**
```bash
streamlit run frontend/app.py
```

---

## 📁 Project Structure

```
agridemand-pro/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── models/
│   │   ├── prophet_model.py       # Time series forecasting
│   │   └── xgboost_model.py       # Wastage risk classifier
│   ├── routes/
│   │   ├── forecast.py            # /api/forecast/* endpoints
│   │   ├── products.py            # /api/products/* endpoints
│   │   └── data_ingest.py         # /api/data/* endpoints
│   ├── database/
│   │   ├── db.py                  # SQLAlchemy connection
│   │   └── schema.sql             # MySQL tables + seed data
│   └── utils/
│       ├── agmarknet_scraper.py   # Real TN mandi price fetcher
│       └── data_cleaner.py        # Data pipeline + sample generator
├── frontend/
│   └── app.py                     # Streamlit dashboard
├── notebooks/
│   └── eda_and_train.py           # EDA + model training script
├── data/
│   ├── raw/                       # Kaggle CSV / Agmarknet data
│   └── processed/                 # Cleaned data + trained models
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/forecast/price-forecast` | Get N-day price forecast |
| GET | `/api/forecast/summary` | 7-day summary + procurement tip |
| GET | `/api/forecast/wastage-risk` | Predict wastage risk |
| POST | `/api/forecast/train` | Train model for one commodity |
| POST | `/api/forecast/train-all` | Train all models |
| GET | `/api/products/list` | List products & markets |
| GET | `/api/products/price-history` | Historical prices |
| GET | `/api/products/stats` | Price statistics |
| POST | `/api/data/upload-kaggle` | Upload Kaggle CSV |
| POST | `/api/data/fetch-agmarknet` | Scrape live TN prices |
| POST | `/api/data/generate-sample` | Generate demo data |
| GET | `/api/data/status` | Check data availability |

---

## 📊 Features

- ✅ 7 / 14 / 30 / 90-day price forecasting using Facebook Prophet
- ✅ Seasonal pattern analysis (yearly + weekly + festival)
- ✅ Wastage risk prediction using XGBoost classifier (HIGH / MEDIUM / LOW)
- ✅ Real TN mandi price fetching via Agmarknet scraper
- ✅ Kaggle dataset integration
- ✅ Multi-market price comparison dashboard
- ✅ Procurement suggestion engine
- ✅ CSV export of forecasts
- ✅ Interactive Plotly charts
- ✅ Docker deployment ready

---

## 🥦 Supported Products

Tomato, Onion, Potato, Brinjal, Carrot, Cabbage, Cauliflower, Beans, Banana, Mango, Grapes, Watermelon

## 🏪 Supported Markets (Tamil Nadu)

Koyambedu (Chennai), Erode, Coimbatore, Madurai, Salem, Trichy, Tirunelveli, Vellore

---

## 🎓 Academic Details

- **Project Type:** Final Year B.Tech Project + Internship Submission
- **Domain:** AI & Data Science / AgriTech
- **College:** Shree Venkateshwara Hi-Tech Engineering College, Erode
- **Tech Focus:** Machine Learning, Time Series Forecasting, Full Stack Development

---

## 📦 Dataset Sources

1. **Kaggle:** [Agriculture Prices India](https://www.kaggle.com/datasets/srinivas1/agricuture-crops-production-in-india)
2. **Agmarknet:** https://agmarknet.gov.in (real-time mandi prices)
3. **Sample Data:** Auto-generated realistic TN seasonal data (built-in)

---

## 👨‍💻 Author

**Ramkumar** | AI & Data Science | GitHub: [@RAMKUMARSUDHA](https://github.com/RAMKUMARSUDHA)
