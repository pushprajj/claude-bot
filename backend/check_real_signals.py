#!/usr/bin/env python3
"""
Check if real signals were generated successfully
"""
from app.database import SessionLocal
from app.models import Signal, Ticker
from datetime import datetime, timedelta
import json

def check_real_signals():
    """Check the latest signals in the database"""
    db = SessionLocal()
    
    try:
        # Get the 5 most recent signals
        recent_signals = db.query(Signal).order_by(Signal.generated_at.desc()).limit(5).all()
        
        print(f"Found {len(recent_signals)} recent signals:")
        for signal in recent_signals:
            # Get ticker info
            ticker = db.query(Ticker).filter(Ticker.id == signal.ticker_id).first()
            
            # Parse signal data
            try:
                details = json.loads(signal.signal_data) if signal.signal_data else {}
            except:
                details = {}
            
            print(f"\nSignal #{signal.id}:")
            print(f"  Ticker: {ticker.symbol if ticker else 'Unknown'} ({ticker.exchange if ticker else 'Unknown'})")
            print(f"  Type: {signal.signal_type}")
            print(f"  Strength: {signal.signal_strength}")
            print(f"  Price: ${signal.price:.4f}")
            print(f"  Confidence: {signal.confidence_score:.2%}")
            print(f"  Generated: {signal.generated_at}")
            print(f"  Details: {details.get('type', 'N/A')} - {details.get('reason', 'N/A')}")
        
    except Exception as e:
        print(f"Error checking signals: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_real_signals()