from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import tickers, signals, watchlist, trades, reports

app = FastAPI(title="Trading Bot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Try to create database tables, but don't fail if database is not available
try:
    from app.database import engine
    from app.models import Base
    Base.metadata.create_all(bind=engine)
    print("SUCCESS: Database tables created successfully")
    database_connected = True
except Exception as e:
    print(f"WARNING: Database connection failed: {e}")
    print("INFO: API will run without database functionality")
    database_connected = False

app.include_router(tickers.router, prefix="/api/tickers", tags=["tickers"])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])

@app.get("/")
def read_root():
    return {
        "message": "Trading Bot API is running",
        "database_connected": database_connected,
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "tickers": "/api/tickers",
            "signals": "/api/signals",
            "watchlist": "/api/watchlist",
            "trades": "/api/trades",
            "reports": "/api/reports"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected" if database_connected else "disconnected",
        "services": {
            "api": "running",
            "database": "connected" if database_connected else "error"
        }
    }