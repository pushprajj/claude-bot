from app.database import engine
from sqlalchemy import text

def check_tables():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
        tables = [r[0] for r in result.fetchall()]
        print("Existing tables:", tables)
        
        # Check for our new tables
        if 'watchlist_signal_checks' in tables:
            print("✓ watchlist_signal_checks table exists")
        else:
            print("✗ watchlist_signal_checks table missing")
            
        if 'watchlist_signal_results' in tables:
            print("✓ watchlist_signal_results table exists")
        else:
            print("✗ watchlist_signal_results table missing")

if __name__ == "__main__":
    check_tables()