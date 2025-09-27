#!/usr/bin/env python3
"""
Test Google APIs with different network configurations
"""

import asyncio
import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

async def test_with_proxy_settings():
    """Test with different proxy configurations."""
    
    print("🌐 Testing with Proxy Settings")
    print("=" * 40)
    
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        print("❌ No API key found")
        return
    
    # Test different configurations
    configurations = [
        {"name": "No Proxy", "proxies": None},
        {"name": "System Proxy", "proxies": "system"},
        {"name": "HTTP Proxy", "proxies": {"http://": None, "https://": None}},
    ]
    
    for config in configurations:
        print(f"\n🧪 Testing: {config['name']}")
        
        try:
            import httpx
            
            client_config = {"timeout": 30.0}
            if config["proxies"] == "system":
                # Let httpx use system proxy settings
                pass
            elif config["proxies"]:
                client_config["proxies"] = config["proxies"]
            
            async with httpx.AsyncClient(**client_config) as client:
                url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                params = {
                    "location": "24.8607,67.0011",
                    "radius": "5000",
                    "type": "hospital",
                    "key": api_key
                }
                
                response = await client.get(url, params=params)
                print(f"   ✅ Success! Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "UNKNOWN")
                    print(f"   📊 API Status: {status}")
                    
                    if status == "OK":
                        results = data.get("results", [])
                        print(f"   🏥 Found {len(results)} hospitals")
                        return True  # Success, no need to try other configs
                        
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    return False

async def test_with_different_dns():
    """Test with different DNS settings."""
    
    print("\n🔧 Testing DNS Resolution...")
    
    try:
        import socket
        
        # Test DNS resolution
        ip = socket.gethostbyname("maps.googleapis.com")
        print(f"✅ DNS Resolution: maps.googleapis.com -> {ip}")
        
        # Test connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((ip, 443))
        sock.close()
        
        if result == 0:
            print("✅ Port 443 (HTTPS) accessible")
            return True
        else:
            print("❌ Port 443 not accessible")
            
    except Exception as e:
        print(f"❌ DNS test failed: {e}")
    
    return False

if __name__ == "__main__":
    print("🚨 Network Troubleshooting for Google APIs")
    print("=" * 50)
    
    # Test DNS first
    dns_ok = asyncio.run(test_with_different_dns())
    
    if dns_ok:
        # Test with different proxy settings
        asyncio.run(test_with_proxy_settings())
    else:
        print("\n💡 Suggestions:")
        print("1. Check your internet connection")
        print("2. Try using a VPN")
        print("3. Check Windows Firewall settings")
        print("4. Try from a different network")
        print("5. Contact your network administrator")
