#!/usr/bin/env python3
"""
Add test tickers for Bybit and additional stocks for comprehensive testing
"""
from app.database import SessionLocal
from app.models import Ticker, MarketType
from datetime import datetime

def add_test_tickers():
    """Add test tickers for multi-exchange signal generation"""
    db = SessionLocal()
    
    try:
        # Bybit crypto tickers (popular pairs available on Bybit)
        bybit_tickers = [
            {"symbol": "BTC", "name": "Bitcoin", "exchange": "Bybit"},
            {"symbol": "ETH", "name": "Ethereum", "exchange": "Bybit"},
            {"symbol": "ADA", "name": "Cardano", "exchange": "Bybit"},
            {"symbol": "SOL", "name": "Solana", "exchange": "Bybit"},
            {"symbol": "DOGE", "name": "Dogecoin", "exchange": "Bybit"},
        ]
        
        # Additional popular stocks for yfinance testing
        stock_tickers = [
            {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ"},
            {"symbol": "TSLA", "name": "Tesla Inc.", "exchange": "NASDAQ"},
            {"symbol": "AMZN", "name": "Amazon.com Inc.", "exchange": "NASDAQ"},
        ]
        
        added_count = 0
        
        # Add Bybit tickers
        for ticker_data in bybit_tickers:
            # Check if ticker already exists
            existing = db.query(Ticker).filter(
                Ticker.symbol == ticker_data["symbol"],
                Ticker.exchange == ticker_data["exchange"]
            ).first()
            
            if not existing:
                ticker = Ticker(
                    symbol=ticker_data["symbol"],
                    market_type=MarketType.CRYPTO,
                    exchange=ticker_data["exchange"],
                    name=ticker_data["name"],
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(ticker)
                added_count += 1
                print(f"Added Bybit ticker: {ticker_data['symbol']}")
            else:
                print(f"Bybit ticker already exists: {ticker_data['symbol']}")
        
        # Add stock tickers
        for ticker_data in stock_tickers:
            # Check if ticker already exists
            existing = db.query(Ticker).filter(
                Ticker.symbol == ticker_data["symbol"],
                Ticker.exchange == ticker_data["exchange"]
            ).first()
            
            if not existing:
                ticker = Ticker(
                    symbol=ticker_data["symbol"],
                    market_type=MarketType.STOCK,
                    exchange=ticker_data["exchange"],
                    name=ticker_data["name"],
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(ticker)
                added_count += 1
                print(f"Added stock ticker: {ticker_data['symbol']}")
            else:
                print(f"Stock ticker already exists: {ticker_data['symbol']}")
        
        db.commit()
        print(f"\nSuccessfully added {added_count} new tickers")
        
        # Summary of all tickers by exchange
        print("\nTicker summary by exchange:")
        exchanges = db.query(Ticker.exchange, db.func.count(Ticker.id)).group_by(Ticker.exchange).all()
        for exchange, count in exchanges:
            print(f"  {exchange}: {count} tickers")
        
    except Exception as e:
        print(f"Error adding tickers: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_test_tickers()