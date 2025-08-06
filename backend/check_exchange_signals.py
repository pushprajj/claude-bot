#!/usr/bin/env python3
"""
Check signals by exchange to verify multi-exchange functionality
"""
from app.database import SessionLocal
from app.models import Signal, Ticker
from datetime import datetime, timedelta
import json

def check_signals_by_exchange():
    """Check recent signals grouped by exchange"""
    db = SessionLocal()
    
    try:
        # Get signals from the last hour
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        recent_signals = db.query(Signal).filter(
            Signal.generated_at >= cutoff_time
        ).order_by(Signal.generated_at.desc()).all()
        
        print(f"Found {len(recent_signals)} signals in the last hour\n")
        
        # Group by exchange
        exchanges = {}
        for signal in recent_signals:
            ticker = db.query(Ticker).filter(Ticker.id == signal.ticker_id).first()
            if ticker:
                exchange = ticker.exchange
                if exchange not in exchanges:
                    exchanges[exchange] = []
                exchanges[exchange].append((signal, ticker))
        
        # Display by exchange
        for exchange, signals in exchanges.items():
            print(f"=== {exchange} Exchange ({len(signals)} signals) ===")
            for signal, ticker in signals[:3]:  # Show first 3 from each exchange
                try:
                    details = json.loads(signal.signal_data) if signal.signal_data else {}
                except:
                    details = {}
                
                print(f"  {ticker.symbol}: {signal.signal_type} - {signal.signal_strength}")
                print(f"    Price: ${signal.price:.4f} | Confidence: {signal.confidence_score:.0%}")
                print(f"    Reason: {details.get('reason', 'N/A')}")
            print()
        
        # Summary
        total_by_exchange = {exchange: len(signals) for exchange, signals in exchanges.items()}
        print("Signal count by exchange:")
        for exchange, count in total_by_exchange.items():
            print(f"  {exchange}: {count} signals")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_signals_by_exchange()