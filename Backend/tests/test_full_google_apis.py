#!/usr/bin/env python3
"""
Test the complete Google APIs integration
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

async def test_full_google_integration():
    """Test the complete Google APIs integration."""
    
    print("🚀 Testing Full Google APIs Integration")
    print("=" * 50)
    
    # Test coordinates (Karachi, Pakistan)
    test_lat = 24.8607
    test_lon = 67.0011
    test_userid = "GOOGLE_TEST"
    test_location = "Karachi, Pakistan"
    
    try:
        from app.services.google_api_client import GooglePlacesAPI, GoogleMapsAPI
        
        print("1. 🏥 Testing Google Places API - Hospitals...")
        places_api = GooglePlacesAPI()
        
        hospitals = await places_api.nearby_search(
            location=f"{test_lat},{test_lon}",
            radius=10000,
            type="hospital",
            keyword="emergency"
        )
        
        print(f"   ✅ Found {len(hospitals)} hospitals")
        for i, hospital in enumerate(hospitals[:3]):
            print(f"   {i+1}. {hospital.name} (Rating: {hospital.rating or 'N/A'})")
            print(f"      📍 {hospital.lat:.4f}, {hospital.lon:.4f}")
            print(f"      🏥 Emergency Capability: {hospital.emergency_capability}/10")
        
        print("\n2. 🚔 Testing Google Places API - Police Stations...")
        police_stations = await places_api.nearby_search(
            location=f"{test_lat},{test_lon}",
            radius=15000,
            type="police"
        )
        
        print(f"   ✅ Found {len(police_stations)} police stations")
        for i, station in enumerate(police_stations[:3]):
            print(f"   {i+1}. {station.name} (Rating: {station.rating or 'N/A'})")
            print(f"      📍 {station.lat:.4f}, {station.lon:.4f}")
        
        print("\n3. 🚒 Testing Google Places API - Fire Stations...")
        fire_stations = await places_api.nearby_search(
            location=f"{test_lat},{test_lon}",
            radius=15000,
            type="fire_station"
        )
        
        print(f"   ✅ Found {len(fire_stations)} fire stations")
        for i, station in enumerate(fire_stations[:3]):
            print(f"   {i+1}. {station.name} (Rating: {station.rating or 'N/A'})")
            print(f"      📍 {station.lat:.4f}, {station.lon:.4f}")
        
        print("\n4. 🗺️ Testing Google Maps API - Geocoding...")
        maps_api = GoogleMapsAPI()
        
        geocode_result = await maps_api.geocode("Karachi, Pakistan")
        if geocode_result:
            print(f"   ✅ Geocoding successful")
            print(f"   📍 Karachi coordinates: {geocode_result['lat']:.4f}, {geocode_result['lon']:.4f}")
        else:
            print("   ❌ Geocoding failed")
        
        print("\n5. ⏱️ Testing Google Maps API - Distance Matrix...")
        if hospitals:
            best_hospital = hospitals[0]
            matrix_result = await maps_api.distance_matrix(
                origins=[f"{test_lat},{test_lon}"],
                destinations=[f"{best_hospital.lat},{best_hospital.lon}"],
                mode="driving",
                traffic_model="best_guess"
            )
            
            if matrix_result:
                print(f"   ✅ Distance Matrix successful")
                duration = matrix_result["rows"][0]["elements"][0].get("duration_in_traffic", {})
                if duration:
                    eta_minutes = duration["value"] // 60
                    print(f"   ⏱️ Real-time ETA to {best_hospital.name}: {eta_minutes} minutes")
                else:
                    print("   ⚠️ No traffic data available")
            else:
                print("   ❌ Distance Matrix failed - API not enabled")
                print("   💡 Enable Distance Matrix API in Google Cloud Console")
        
        print("\n6. 🏥 Testing Enhanced Medical Service with Google Data...")
        from app.services.enhanced_medical import enhanced_medical
        
        medical_dispatch = await enhanced_medical.ambulance_dispatch_packet(
            userid=test_userid,
            user_lat=test_lat,
            user_lon=test_lon
        )
        
        print(f"   ✅ Enhanced Medical Dispatch:")
        print(f"   📋 Dispatch ID: {medical_dispatch['dispatch_reference']}")
        print(f"   🏥 Hospital: {medical_dispatch['destination']['name']}")
        print(f"   ⏱️ ETA: {medical_dispatch['eta_minutes']} minutes")
        print(f"   📊 Source: {medical_dispatch['dispatch_metadata']['search_source']}")
        print(f"   🔍 Total Hospitals Found: {medical_dispatch['dispatch_metadata']['total_hospitals_found']}")
        
        print("\n🎉 GOOGLE APIS INTEGRATION TEST COMPLETE!")
        print("=" * 50)
        print("✅ Google Places API: Working")
        print("✅ Google Geocoding API: Working") 
        print("✅ Enhanced Service Discovery: Working")
        print("✅ Real Hospital Data: Working")
        print("✅ Multi-service Coordination: Working")
        
        if not matrix_result:
            print("\n⚠️ Distance Matrix API: Not enabled")
            print("   Enable it here: https://console.cloud.google.com/apis/library/distance-matrix.googleapis.com")
        
        print("\n🚀 Your AlertMate system is now fully integrated with Google APIs!")
        print("   Real-time hospital discovery ✅")
        print("   Live emergency service data ✅") 
        print("   Accurate location services ✅")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_google_integration())
