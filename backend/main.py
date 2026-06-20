from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import forecast, products, data_ingest, features
from backend.database.db import test_connection

app = FastAPI(
    title="AgriDemand Pro API",
    description="Seasonal Produce Demand Forecaster for Tamil Nadu Supermarkets",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(forecast.router,    prefix="/api/forecast",  tags=["Forecast"])
app.include_router(products.router,    prefix="/api/products",  tags=["Products"])
app.include_router(data_ingest.router, prefix="/api/data",      tags=["Data"])
app.include_router(features.router,    prefix="/api/features",  tags=["Features"])

@app.on_event("startup")
async def startup():
    print("🚀 AgriDemand Pro v2.0 API starting...")
    test_connection()

@app.get("/")
def root():
    return {"app": "AgriDemand Pro", "version": "2.0.0", "status": "running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
