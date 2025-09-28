#!/usr/bin/env python3
"""Test script to verify admin service fixes."""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.db import get_session
from app.services.admin import get_dispatch_locations, get_dashboard_stats, get_active_queue

def test_admin_services():
    """Test admin services to ensure they work without errors."""
    print("Testing admin services...")
    
    with get_session() as session:
        try:
            # Test dashboard stats
            print("Testing dashboard stats...")
            stats = get_dashboard_stats(session)
            print(f"✓ Dashboard stats: {stats}")
            
            # Test active queue
            print("Testing active queue...")
            queue = get_active_queue(session)
            print(f"✓ Active queue: {len(queue)} items")
            
            # Test dispatch locations
            print("Testing dispatch locations...")
            locations = get_dispatch_locations(session)
            print(f"✓ Dispatch locations: {len(locations)} items")
            
            print("\n✅ All admin services working correctly!")
            
        except Exception as e:
            print(f"❌ Error testing admin services: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_admin_services()
