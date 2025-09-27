#!/usr/bin/env python3
"""
Test script to verify Google API keys are working
"""

import os
import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

async def test_google_apis():
    """Test Google API connectivity."""
    
    print("🔑 Testing Google API Keys")
    print("=" * 40)
    
    # Check environment variables
    places_key = os.getenv("GOOGLE_PLACES_API_KEY")
    maps_key = os.getenv("GOOGLE_MAPS_API_KEY")
    geocoding_key = os.getenv("GOOGLE_GEOCODING_API_KEY")
    
    print(f"Places API Key: {'✅ Set' if places_key else '❌ Missing'}")
    print(f"Maps API Key: {'✅ Set' if maps_key else '❌ Missing'}")
    print(f"Geocoding API Key: {'✅ Set' if geocoding_key else '❌ Missing'}")
    print()
    
    if not any([places_key, maps_key, geocoding_key]):
        print("❌ No API keys found!")
        print("Please add your Google API key to Backend/.env file:")
        print("GOOGLE_PLACES_API_KEY=your_key_here")
        print("GOOGLE_MAPS_API_KEY=your_key_here")
        print("GOOGLE_GEOCODING_API_KEY=your_key_here")
        return
    
    # Test API connectivity
    try:
        from app.services.google_api_client import GooglePlacesAPI, GoogleMapsAPI
        
        print("🧪 Testing API Connectivity...")
        
        # Test Places API
        places_api = GooglePlacesAPI(places_key)
        places_result = await places_api.nearby_search(
            location="24.8607,67.0011",  # Karachi coordinates
            radius=5000,
            type="hospital"
        )
        
        if places_result:
            print(f"✅ Places API: Found {len(places_result)} hospitals")
            print(f"   First result: {places_result[0].name}")
        else:
            print("⚠️  Places API: No results (might be API restrictions)")
        
        # Test Geocoding API
        maps_api = GoogleMapsAPI(maps_key)
        geocode_result = await maps_api.geocode("Karachi, Pakistan")
        
        if geocode_result:
            print(f"✅ Geocoding API: Karachi coordinates found")
            print(f"   Lat: {geocode_result['lat']}, Lon: {geocode_result['lon']}")
        else:
            print("⚠️  Geocoding API: No results")
        
        print()
        print("🎉 API Test Complete!")
        
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        print()
        print("Common issues:")
        print("1. API key not valid")
        print("2. APIs not enabled in Google Cloud Console")
        print("3. API key restrictions too strict")
        print("4. Billing not enabled")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
    
    asyncio.run(test_google_apis())
