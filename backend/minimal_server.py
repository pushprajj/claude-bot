#!/usr/bin/env python3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Minimal Test Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "running", "message": "Minimal server is working"}

@app.get("/api/tickers/")
def get_tickers():
    return [{"id": 1, "symbol": "TEST", "market_type": "stock", "exchange": "TEST", "is_active": True}]

@app.post("/api/signals/generate-confirmed-buy")
def generate_confirmed_buy(request: dict = None):
    return {
        "message": "Test confirmed buy generation", 
        "status": "processing", 
        "ticker_count": 5,
        "estimated_time": "1 minute"
    }

if __name__ == "__main__":
    print("Starting minimal server on http://localhost:8001...")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info",
        access_log=True
    )