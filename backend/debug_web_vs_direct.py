#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
import asyncio
from datetime import datetime
import json

def test_direct_script():
    print("=== Direct Script Test ===")
    test_symbols = ['WES.AX', 'WOW.AX', 'CBA.AX']
    
    for symbol in test_symbols:
        try:
            data = yf.download(symbol, period='60d', interval='1d', progress=False, auto_adjust=False)
            print(f"{symbol}: SUCCESS - {data.shape if not data.empty else 'EMPTY'}")
        except Exception as e:
            print(f"{symbol}: ERROR - {str(e)}")

async def test_async_context():
    print("\n=== Async Context Test ===") 
    test_symbols = ['WES.AX', 'WOW.AX', 'CBA.AX']
    
    for symbol in test_symbols:
        try:
            # Simulate how web interface calls it
            data = yf.download(symbol, period='60d', interval='1d', progress=False, auto_adjust=False)
            print(f"{symbol}: SUCCESS - {data.shape if not data.empty else 'EMPTY'}")
        except Exception as e:
            print(f"{symbol}: ERROR - {str(e)}")

def test_session_reuse():
    print("\n=== Session Reuse Test ===")
    import requests
    
    # Test if creating a session affects subsequent yfinance calls
    session = requests.Session()
    
    # Make some requests to Yahoo Finance to potentially trigger rate limiting
    for i in range(5):
        try:
            response = session.get('https://finance.yahoo.com', timeout=5)
            print(f"Pre-request {i+1}: {response.status_code}")
        except Exception as e:
            print(f"Pre-request {i+1}: ERROR - {str(e)}")
    
    # Now test yfinance after session activity
    try:
        data = yf.download('WES.AX', period='60d', interval='1d', progress=False, auto_adjust=False)
        print(f"After session activity - WES.AX: SUCCESS - {data.shape if not data.empty else 'EMPTY'}")
    except Exception as e:
        print(f"After session activity - WES.AX: ERROR - {str(e)}")

def test_import_context():
    print("\n=== Import Context Test ===")
    
    # Test if importing in different ways affects behavior
    print("Testing different import methods...")
    
    # Method 1: Fresh import
    import importlib
    importlib.reload(yf)
    
    try:
        data = yf.download('WES.AX', period='60d', interval='1d', progress=False, auto_adjust=False)
        print(f"Fresh import - WES.AX: SUCCESS - {data.shape if not data.empty else 'EMPTY'}")
    except Exception as e:
        print(f"Fresh import - WES.AX: ERROR - {str(e)}")

def test_environment_variables():
    print("\n=== Environment Variables Test ===")
    
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path[:3]}...")  # First 3 entries
    print(f"Environment variables of interest:")
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'USER_AGENT']:
        print(f"  {key}: {os.environ.get(key, 'Not set')}")

async def simulate_web_interface_call():
    print("\n=== Simulating Web Interface Call ===")
    
    # Import exactly as the web interface does
    from app.database import get_db
    from app.models import Ticker, MarketType
    from app.services.data_fetcher import DataFetcher
    
    # Get a database session like the web interface
    db_session = next(get_db())
    
    try:
        # Get tickers exactly like the web interface
        asx_tickers = db_session.query(Ticker).filter(
            Ticker.market_type == MarketType.STOCK,
            Ticker.exchange == 'ASX',
            Ticker.symbol.in_(['WES', 'WOW', 'CBA']),
            Ticker.is_active == True
        ).limit(3).all()
        
        print(f"Found {len(asx_tickers)} tickers via database")
        
        # Use DataFetcher exactly like web interface
        data_fetcher = DataFetcher()
        
        for ticker in asx_tickers:
            try:
                # Call the exact same method that web interface calls
                data = await data_fetcher.fetch_stock_data(f"{ticker.symbol}.AX", period="60d", interval="1d")
                print(f"{ticker.symbol}.AX via DataFetcher: {'SUCCESS' if data is not None else 'EMPTY'}")
            except Exception as e:
                print(f"{ticker.symbol}.AX via DataFetcher: ERROR - {str(e)}")
                
    finally:
        db_session.close()

if __name__ == "__main__":
    test_direct_script()
    asyncio.run(test_async_context())
    test_session_reuse()
    test_import_context()
    test_environment_variables()
    asyncio.run(simulate_web_interface_call())