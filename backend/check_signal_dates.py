#!/usr/bin/env python3
"""
Check signal dates to verify they're using today's date
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Signal, Ticker
from datetime import datetime, timedelta, date

def check_signal_dates():
    """Check recent signals and their dates"""
    print("=" * 60)
    print("CHECKING SIGNAL DATES")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Get signals from the last 2 hours
        two_hours_ago = datetime.utcnow() - timedelta(hours=2)
        recent_signals = db.query(Signal).join(Ticker).filter(
            Signal.generated_at >= two_hours_ago
        ).order_by(Signal.generated_at.desc()).all()
        
        print(f"Recent signals (last 2 hours): {len(recent_signals)}")
        today = date.today()
        
        if recent_signals:
            print(f"\nToday's date: {today}")
            print("\nSignal details:")
            
            for i, signal in enumerate(recent_signals[:10], 1):  # Show first 10
                signal_date = signal.signal_date
                generated_at = signal.generated_at
                exchange = signal.ticker.exchange
                symbol = signal.ticker.symbol
                
                # Check if signal_date matches today
                date_match = signal_date == today if signal_date else "N/A"
                
                print(f"  {i}. {symbol} ({exchange})")
                print(f"     Signal Date: {signal_date} {'[TODAY]' if date_match == True else '[NOT TODAY]' if date_match == False else 'N/A'}")
                print(f"     Generated At: {generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"     Price: ${signal.price:.2f}")
                print()
                
            # Summary
            today_signals = [s for s in recent_signals if s.signal_date == today]
            print(f"Summary:")
            print(f"  Total recent signals: {len(recent_signals)}")
            print(f"  Signals with today's date: {len(today_signals)}")
            print(f"  Signals with other dates: {len(recent_signals) - len(today_signals)}")
            
            if len(today_signals) == len(recent_signals):
                print("  SUCCESS: All recent signals have today's date!")
            else:
                print("  ISSUE: Some signals don't have today's date")
                
        else:
            print("No signals generated in the last 2 hours.")
            
    except Exception as e:
        print(f"ERROR checking signals: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_signal_dates()