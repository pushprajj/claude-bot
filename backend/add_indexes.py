#!/usr/bin/env python3
"""
Add database indexes for performance optimization
"""
from app.database import engine
from sqlalchemy import text

def add_indexes():
    """Add indexes to improve query performance"""
    print("Adding database indexes...")
    
    with engine.connect() as conn:
        # Check if indexes already exist before creating them
        try:
            # Add index on generated_at for ORDER BY performance
            result = conn.execute(text("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'signals' AND indexname = 'ix_signals_generated_at'
            """))
            if not result.fetchone():
                conn.execute(text("CREATE INDEX ix_signals_generated_at ON signals (generated_at DESC)"))
                print("Created index on signals.generated_at")
            else:
                print("Index on signals.generated_at already exists")
            
            # Add index on is_processed for filtering
            result = conn.execute(text("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'signals' AND indexname = 'ix_signals_is_processed'
            """))
            if not result.fetchone():
                conn.execute(text("CREATE INDEX ix_signals_is_processed ON signals (is_processed)"))
                print("Created index on signals.is_processed")
            else:
                print("Index on signals.is_processed already exists")
            
            # Add composite index for common queries
            result = conn.execute(text("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'signals' AND indexname = 'ix_signals_generated_at_processed'
            """))
            if not result.fetchone():
                conn.execute(text("CREATE INDEX ix_signals_generated_at_processed ON signals (generated_at DESC, is_processed)"))
                print("Created composite index on signals.generated_at + is_processed")
            else:
                print("Composite index already exists")
            
            conn.commit()
            print("Indexes added successfully!")
            
        except Exception as e:
            print(f"Error adding indexes: {e}")
            conn.rollback()

if __name__ == "__main__":
    add_indexes()