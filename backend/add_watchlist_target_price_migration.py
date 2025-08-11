#!/usr/bin/env python3
"""
Manual database migration script to add target_price and related fields to watchlist table
Run this after updating the models.py file
"""

import sys
import os

# Add the current directory to Python path to import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from sqlalchemy import text

def run_migration():
    """Add new columns to watchlist table"""
    
    migration_sql = """
    -- Add new columns to watchlist table
    ALTER TABLE watchlist 
    ADD COLUMN target_price FLOAT,
    ADD COLUMN signal_price FLOAT,
    ADD COLUMN signal_type VARCHAR(10),
    ADD COLUMN signal_date DATE;
    """
    
    rollback_sql = """
    -- Rollback: Remove the added columns
    ALTER TABLE watchlist 
    DROP COLUMN IF EXISTS target_price,
    DROP COLUMN IF EXISTS signal_price,
    DROP COLUMN IF EXISTS signal_type,
    DROP COLUMN IF EXISTS signal_date;
    """
    
    print("Running watchlist target price migration...")
    
    try:
        with engine.connect() as connection:
            # Check if columns already exist
            check_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'watchlist' 
            AND column_name IN ('target_price', 'signal_price', 'signal_type', 'signal_date');
            """
            
            result = connection.execute(text(check_sql))
            existing_columns = [row[0] for row in result]
            
            if len(existing_columns) > 0:
                print(f"Columns already exist: {existing_columns}")
                print("Migration may have already been run. Skipping...")
                return
            
            # Run the migration
            connection.execute(text(migration_sql))
            connection.commit()
            
            print("SUCCESS: Added target_price, signal_price, signal_type, signal_date columns to watchlist table")
            
            # Verify the migration
            verify_sql = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'watchlist' 
            AND column_name IN ('target_price', 'signal_price', 'signal_type', 'signal_date')
            ORDER BY column_name;
            """
            
            result = connection.execute(text(verify_sql))
            print("\nNew columns verified:")
            for row in result:
                print(f"  - {row[0]}: {row[1]}")
                
    except Exception as e:
        print(f"ERROR: Migration failed: {str(e)}")
        print(f"\nTo rollback, run:")
        print(rollback_sql)
        raise

if __name__ == "__main__":
    run_migration()