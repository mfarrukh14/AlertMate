#!/usr/bin/env python3
"""
Simple test to check Google API connectivity
"""

import asyncio
import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

async def test_simple_connectivity():
    """Test basic HTTP connectivity to Google APIs."""
    
    print("🌐 Testing Google API Connectivity")
    print("=" * 40)
    
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        print("❌ No API key found in environment")
        return
    
    print(f"🔑 API Key: {api_key[:10]}...{api_key[-5:] if len(api_key) > 15 else 'SHORT'}")
    
    # Test 1: Simple HTTP request
    try:
        import httpx
        
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": "24.8607,67.0011",
            "radius": "5000",
            "type": "hospital",
            "key": api_key
        }
        
        print("🧪 Testing Places API...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            
            print(f"📡 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "UNKNOWN")
                print(f"✅ API Response: {status}")
                
                if status == "OK":
                    results = data.get("results", [])
                    print(f"🏥 Found {len(results)} hospitals")
                    
                    if results:
                        first_hospital = results[0]
                        print(f"   First: {first_hospital.get('name', 'Unknown')}")
                        print(f"   Rating: {first_hospital.get('rating', 'N/A')}")
                        
                elif status == "REQUEST_DENIED":
                    print("❌ API Key rejected - check key validity and restrictions")
                elif status == "ZERO_RESULTS":
                    print("⚠️  No results found (might be location/radius issue)")
                else:
                    print(f"⚠️  API Error: {status}")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("\nPossible issues:")
        print("1. Network firewall blocking HTTPS requests")
        print("2. Corporate proxy settings")
        print("3. API key restrictions too strict")
        print("4. APIs not enabled in Google Cloud Console")
    
    # Test 2: Check if it's a Python/httpx specific issue
    print("\n🔧 Testing basic Python HTTP...")
    try:
        import urllib.request
        import urllib.parse
        
        # Simple test URL
        test_url = "https://httpbin.org/get"
        response = urllib.request.urlopen(test_url, timeout=10)
        print("✅ Basic Python HTTP works")
        
    except Exception as e:
        print(f"❌ Basic HTTP failed: {e}")
        print("This suggests a network/proxy issue")

if __name__ == "__main__":
    asyncio.run(test_simple_connectivity())
