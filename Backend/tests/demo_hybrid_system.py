#!/usr/bin/env python3
"""
Simple demo script for the AlertMate Hybrid Emergency Services System
Works without Google APIs - uses fallback data
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

async def demo_hybrid_system():
    """Demo the hybrid emergency services system with fallback data."""
    
    print("🚨 AlertMate Hybrid Emergency Services System - DEMO")
    print("=" * 60)
    print("📍 Testing with Karachi, Pakistan coordinates")
    print("🔄 Using fallback data (Google APIs not required for demo)")
    print()
    
    # Test coordinates (Karachi, Pakistan)
    test_lat = 24.8607
    test_lon = 67.0011
    test_userid = "DEMO123"
    test_location = "Karachi, Pakistan"
    
    try:
        # Import services
        from app.services.enhanced_medical import enhanced_medical
        from app.services.enhanced_police import enhanced_police
        from app.services.enhanced_fire import enhanced_fire
        
        print("1. 🏥 Testing Enhanced Medical Service...")
        medical_dispatch = await enhanced_medical.ambulance_dispatch_packet(
            userid=test_userid,
            user_lat=test_lat,
            user_lon=test_lon
        )
        
        print(f"   ✅ Ambulance dispatched!")
        print(f"   📋 Dispatch ID: {medical_dispatch['dispatch_reference']}")
        print(f"   🏥 Hospital: {medical_dispatch['destination']['name']}")
        print(f"   ⏱️  ETA: {medical_dispatch['eta_minutes']} minutes")
        print(f"   📊 Source: {medical_dispatch['dispatch_metadata']['search_source']}")
        print()
        
        print("2. 🚔 Testing Enhanced Police Service...")
        police_dispatch = await enhanced_police.dispatch_unit(
            userid=test_userid,
            location=test_location,
            lat=test_lat,
            lon=test_lon
        )
        
        print(f"   ✅ Police units dispatched!")
        print(f"   📋 Dispatch ID: {police_dispatch['dispatch_id']}")
        print(f"   ⏱️  ETA: {police_dispatch['eta_min']} minutes")
        print(f"   🚔 Units: {', '.join(police_dispatch['units'])}")
        print(f"   📊 Source: {police_dispatch['dispatch_metadata']['search_source']}")
        print()
        
        print("3. 🚒 Testing Enhanced Fire Service...")
        fire_dispatch = await enhanced_fire.dispatch_fire_units(
            userid=test_userid,
            location=test_location,
            lat=test_lat,
            lon=test_lon,
            emergency_type="fire"
        )
        
        print(f"   ✅ Fire units dispatched!")
        print(f"   📋 Dispatch ID: {fire_dispatch['dispatch_id']}")
        print(f"   ⏱️  ETA: {fire_dispatch['eta_minutes']} minutes")
        print(f"   🔥 Emergency Type: {fire_dispatch['emergency_type']}")
        print(f"   📊 Source: {fire_dispatch['dispatch_metadata']['search_source']}")
        print()
        
        print("4. 🌪️ Testing Disaster Response...")
        disaster_response = await enhanced_fire.create_disaster_response(
            userid=test_userid,
            disaster_type="earthquake",
            location=test_location,
            severity=2
        )
        
        print(f"   ✅ Disaster response coordinated!")
        print(f"   📋 Response ID: {disaster_response['response_id']}")
        print(f"   🌪️  Disaster Type: {disaster_response['disaster_type']}")
        print(f"   🚨 Services Coordinated: {len(disaster_response['coordinated_services'])}")
        
        for service in disaster_response['coordinated_services']:
            status_emoji = "✅" if service['status'] == "dispatched" else "⚠️"
            print(f"   {status_emoji} {service['service_type'].title()}: {service['status']}")
        print()
        
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("📈 System Features Demonstrated:")
        print("   ✅ Multi-source service discovery")
        print("   ✅ Real-time dispatch coordination")
        print("   ✅ Fallback mechanisms")
        print("   ✅ Enhanced metadata tracking")
        print("   ✅ Multi-agency coordination")
        print()
        print("🚀 Next Steps:")
        print("   1. Add Google API keys to Backend/.env for real-time data")
        print("   2. Deploy to production environment")
        print("   3. Integrate with actual emergency services")
        print("   4. Monitor performance and costs")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(demo_hybrid_system())
