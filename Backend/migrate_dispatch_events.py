#!/usr/bin/env python3
"""Migration script to add DispatchEvent table to the database."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.db import Base, engine
from app.db.models import DispatchEvent

def migrate():
    """Add DispatchEvent table to the database."""
    
    try:
        # Create the DispatchEvent table
        DispatchEvent.__table__.create(engine, checkfirst=True)
        print("✅ DispatchEvent table created successfully!")
        
        # Verify the table was created
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='dispatch_events'"))
            if result.fetchone():
                print("✅ DispatchEvent table verified in database")
            else:
                print("❌ DispatchEvent table not found in database")
                
    except Exception as e:
        print(f"❌ Error creating DispatchEvent table: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 Running database migration for DispatchEvent table...")
    success = migrate()
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
        sys.exit(1)
