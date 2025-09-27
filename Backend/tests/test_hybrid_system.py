#!/usr/bin/env python3
"""
Test script for the AlertMate Hybrid Emergency Services System
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.hybrid_service_discovery import HybridServiceDiscovery
from app.services.enhanced_medical import enhanced_medical
from app.services.enhanced_police import enhanced_police
from app.services.enhanced_fire import enhanced_fire

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_hybrid_system():
    """Test the hybrid emergency services system."""
    
    print("🚨 Testing AlertMate Hybrid Emergency Services System")
    print("=" * 60)
    
    # Check if Google APIs are configured
    from app import config
    has_google_apis = any([
        getattr(config, 'GOOGLE_PLACES_API_KEY', None),
        getattr(config, 'GOOGLE_MAPS_API_KEY', None),
        getattr(config, 'GOOGLE_GEOCODING_API_KEY', None)
    ])
    
    if not has_google_apis:
        print("⚠️  Google APIs not configured - testing with fallback data only")
        print("   To enable Google APIs, add keys to Backend/.env file")
    else:
        print("✅ Google APIs configured - testing with real-time data")
    
    # Test coordinates (Karachi, Pakistan)
    test_lat = 24.8607
    test_lon = 67.0011
    test_userid = "TEST123"
    test_location = "Karachi, Pakistan"
    
    # Test 1: Hybrid Service Discovery
    print("\n1. Testing Hybrid Service Discovery...")
    discovery = HybridServiceDiscovery()
    
    try:
        # Test medical services
        medical_result = await discovery.find_emergency_services(
            lat=test_lat,
            lon=test_lon,
            service_type="medical",
            radius_km=25,
            max_results=3
        )
        
        print(f"✅ Medical Services Found: {len(medical_result.services)}")
        print(f"   Source: {medical_result.source}")
        print(f"   Search Time: {medical_result.search_time:.2f}s")
        print(f"   Cache Hit: {medical_result.cache_hit}")
        
        if medical_result.services:
            best_hospital = medical_result.services[0]
            print(f"   Best Hospital: {best_hospital.name}")
            print(f"   Distance: {best_hospital.distance_km:.2f} km")
            print(f"   Emergency Capability: {best_hospital.emergency_capability}/10")
        
    except Exception as e:
        print(f"❌ Medical services test failed: {e}")
    
    # Test 2: Enhanced Medical Service
    print("\n2. Testing Enhanced Medical Service...")
    
    try:
        dispatch_packet = await enhanced_medical.ambulance_dispatch_packet(
            userid=test_userid,
            user_lat=test_lat,
            user_lon=test_lon
        )
        
        print(f"✅ Ambulance Dispatch Created")
        print(f"   Dispatch ID: {dispatch_packet['dispatch_reference']}")
        print(f"   Destination: {dispatch_packet['destination']['name']}")
        print(f"   ETA: {dispatch_packet['eta_minutes']} minutes")
        print(f"   Distance: {dispatch_packet['distance_km']:.2f} km")
        print(f"   Search Source: {dispatch_packet['dispatch_metadata']['search_source']}")
        
    except Exception as e:
        print(f"❌ Medical dispatch test failed: {e}")
    
    # Test 3: Enhanced Police Service
    print("\n3. Testing Enhanced Police Service...")
    
    try:
        police_dispatch = await enhanced_police.dispatch_unit(
            userid=test_userid,
            location=test_location,
            lat=test_lat,
            lon=test_lon
        )
        
        print(f"✅ Police Dispatch Created")
        print(f"   Dispatch ID: {police_dispatch['dispatch_id']}")
        print(f"   ETA: {police_dispatch['eta_min']} minutes")
        print(f"   Units: {', '.join(police_dispatch['units'])}")
        print(f"   Search Source: {police_dispatch['dispatch_metadata']['search_source']}")
        
    except Exception as e:
        print(f"❌ Police dispatch test failed: {e}")
    
    # Test 4: Enhanced Fire Service
    print("\n4. Testing Enhanced Fire Service...")
    
    try:
        fire_dispatch = await enhanced_fire.dispatch_fire_units(
            userid=test_userid,
            location=test_location,
            lat=test_lat,
            lon=test_lon,
            emergency_type="fire"
        )
        
        print(f"✅ Fire Dispatch Created")
        print(f"   Dispatch ID: {fire_dispatch['dispatch_id']}")
        print(f"   ETA: {fire_dispatch['eta_minutes']} minutes")
        print(f"   Emergency Type: {fire_dispatch['emergency_type']}")
        print(f"   Search Source: {fire_dispatch['dispatch_metadata']['search_source']}")
        
    except Exception as e:
        print(f"❌ Fire dispatch test failed: {e}")
    
    # Test 5: Disaster Response
    print("\n5. Testing Disaster Response...")
    
    try:
        disaster_response = await enhanced_fire.create_disaster_response(
            userid=test_userid,
            disaster_type="earthquake",
            location=test_location,
            severity=2
        )
        
        print(f"✅ Disaster Response Created")
        print(f"   Response ID: {disaster_response['response_id']}")
        print(f"   Disaster Type: {disaster_response['disaster_type']}")
        print(f"   Coordinated Services: {len(disaster_response['coordinated_services'])}")
        
        for service in disaster_response['coordinated_services']:
            print(f"   - {service['service_type']}: {service['status']}")
        
    except Exception as e:
        print(f"❌ Disaster response test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Hybrid System Test Complete!")
    print("\nTo enable Google APIs:")
    print("1. Copy Backend/env.example to Backend/.env")
    print("2. Add your Google API keys to the .env file")
    print("3. Enable required APIs in Google Cloud Console")


if __name__ == "__main__":
    asyncio.run(test_hybrid_system())
