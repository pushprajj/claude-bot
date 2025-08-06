#!/usr/bin/env python3
"""
Clean old signals from database for better performance
"""
from app.database import SessionLocal
from app.models import Signal
from datetime import datetime, timedelta

def clean_old_signals():
    """Remove old signals to improve performance"""
    db = SessionLocal()
    try:
        # Delete signals older than 1 hour for testing
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        old_signals = db.query(Signal).filter(Signal.generated_at < cutoff_time)
        count = old_signals.count()
        old_signals.delete()
        db.commit()
        print(f"Deleted {count} old signals")
        
        # Count remaining signals
        remaining = db.query(Signal).count()
        print(f"Remaining signals: {remaining}")
        
    except Exception as e:
        print(f"Error cleaning signals: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clean_old_signals()