#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import Signal, Ticker, MarketType
from sqlalchemy.orm import Session
from datetime import datetime
import json

def check_signals():
    db_session = next(get_db())
    
    try:
        print("=== Current Signals in Database ===")
        
        # Get all signals with ticker information
        signals = db_session.query(Signal).join(Ticker, Signal.ticker_id == Ticker.id).order_by(Signal.generated_at.desc()).limit(10).all()
        
        if not signals:
            print("No signals found in database")
            return
            
        print(f"Found {len(signals)} recent signals:")
        
        for signal in signals:
            ticker = db_session.query(Ticker).filter(Ticker.id == signal.ticker_id).first()
            signal_data = json.loads(signal.signal_data) if signal.signal_data else {}
            
            print(f"  {signal.id}: {ticker.symbol} ({ticker.exchange}) - {signal.signal_type}")
            print(f"    Generated: {signal.generated_at}")
            print(f"    Type: {signal_data.get('type', 'N/A')}")
            print(f"    Conditions: {signal_data.get('conditions_met', 0)}/6")
            print()
            
        # Check for specific exchanges
        print("\n=== Signals by Exchange ===")
        for exchange in ['ASX', 'NYSE', 'NASDAQ']:
            count = db_session.query(Signal).join(Ticker, Signal.ticker_id == Ticker.id).filter(
                Ticker.exchange == exchange,
                Ticker.market_type == MarketType.STOCK
            ).count()
            print(f"{exchange}: {count} signals")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db_session.close()

if __name__ == "__main__":
    check_signals()