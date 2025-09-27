#!/usr/bin/env python3
"""
Demo of calling options for emergency services
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

async def demo_calling_options():
    """Demo different calling options for emergency services."""
    
    print("📞 EMERGENCY SERVICE CALLING OPTIONS")
    print("=" * 50)
    
    # Test coordinates (Karachi, Pakistan)
    test_lat = 24.8607
    test_lon = 67.0011
    
    try:
        from app.services.hybrid_service_discovery import HybridServiceDiscovery
        
        discovery = HybridServiceDiscovery()
        
        # Find real services using Google APIs
        print("🔍 Finding Real Emergency Services...")
        
        medical_result = await discovery.find_emergency_services(
            lat=test_lat,
            lon=test_lon,
            service_type="medical",
            radius_km=10,
            max_results=3
        )
        
        police_result = await discovery.find_emergency_services(
            lat=test_lat,
            lon=test_lon,
            service_type="police", 
            radius_km=15,
            max_results=3
        )
        
        fire_result = await discovery.find_emergency_services(
            lat=test_lat,
            lon=test_lon,
            service_type="fire",
            radius_km=15,
            max_results=3
        )
        
        print(f"✅ Found {len(medical_result.services)} hospitals")
        print(f"✅ Found {len(police_result.services)} police stations") 
        print(f"✅ Found {len(fire_result.services)} fire stations")
        
        # Show nearest services
        if medical_result.services:
            best_hospital = medical_result.services[0]
            print(f"\n🏥 NEAREST HOSPITAL:")
            print(f"   Name: {best_hospital.name}")
            print(f"   Phone: {best_hospital.phone or 'Not available'}")
            print(f"   Distance: {best_hospital.distance_km:.2f} km")
            print(f"   Rating: {best_hospital.rating or 'N/A'}")
            
        if police_result.services:
            best_police = police_result.services[0]
            print(f"\n🚔 NEAREST POLICE STATION:")
            print(f"   Name: {best_police.name}")
            print(f"   Phone: {best_police.phone or 'Not available'}")
            print(f"   Distance: {best_police.distance_km:.2f} km")
            print(f"   Rating: {best_police.rating or 'N/A'}")
            
        if fire_result.services:
            best_fire = fire_result.services[0]
            print(f"\n🚒 NEAREST FIRE STATION:")
            print(f"   Name: {best_fire.name}")
            print(f"   Phone: {best_fire.phone or 'Not available'}")
            print(f"   Distance: {best_fire.distance_km:.2f} km")
            print(f"   Rating: {best_fire.rating or 'N/A'}")
        
        print("\n" + "=" * 50)
        print("📞 CALLING OPTIONS AVAILABLE:")
        print("=" * 50)
        
        print("\n1. 📞 TWILIO PHONE CALLS")
        print("   ✅ Make actual phone calls to emergency services")
        print("   💰 Cost: ~$0.02 per minute")
        print("   🔧 Setup: Twilio account + phone number")
        print("   📋 Implementation:")
        print("      ```python")
        print("      from twilio.rest import Client")
        print("      client = Client(account_sid, auth_token)")
        print("      call = client.calls.create(")
        print("          to='+92-21-1234567',  # Hospital phone")
        print("          from_='+1234567890',  # Your Twilio number")
        print("          url='http://your-server.com/emergency-script.xml'")
        print("      )")
        print("      ```")
        
        print("\n2. 📱 TWILIO SMS")
        print("   ✅ Send automated SMS to emergency services")
        print("   💰 Cost: ~$0.0075 per SMS")
        print("   📋 Implementation:")
        print("      ```python")
        print("      message = client.messages.create(")
        print("          body='EMERGENCY: Medical emergency at location. Patient needs immediate care.'")
        print("          from_='+1234567890',")
        print("          to='+92-21-1234567'")
        print("      )")
        print("      ```")
        
        print("\n3. 🔌 EMERGENCY SERVICE APIs")
        print("   ✅ Direct API integration with emergency systems")
        print("   💰 Cost: Usually free")
        print("   📋 Implementation:")
        print("      ```python")
        print("      # Hospital dispatch API")
        print("      response = await client.post(")
        print("          'https://hospital-api.com/dispatch',")
        print("          json={")
        print("              'location': {'lat': 24.8607, 'lon': 67.0011},")
        print("              'emergency_type': 'medical',")
        print("              'patient_info': 'Critical condition'")
        print("          }")
        print("      )")
        print("      ```")
        
        print("\n4. 📧 EMAIL NOTIFICATIONS")
        print("   ✅ Send detailed email alerts")
        print("   💰 Cost: ~$0.10 per 1000 emails")
        print("   📋 Implementation:")
        print("      ```python")
        print("      # AWS SES or SendGrid")
        print("      response = client.send_email(")
        print("          to='emergency@hospital.com',")
        print("          subject='EMERGENCY ALERT',")
        print("          body='Detailed emergency report...'")
        print("      )")
        print("      ```")
        
        print("\n5. 🌐 WEBHOOK INTEGRATION")
        print("   ✅ Real-time notifications to emergency services")
        print("   💰 Cost: Free")
        print("   📋 Implementation:")
        print("      ```python")
        print("      webhook_data = {")
        print("          'emergency_id': 'EMG-12345',")
        print("          'service_type': 'medical',")
        print("          'location': {'lat': 24.8607, 'lon': 67.0011},")
        print("          'patient_info': {...}")
        print("      }")
        print("      await client.post('https://emergency-service.com/webhook', json=webhook_data)")
        print("      ```")
        
        print("\n" + "=" * 50)
        print("🚀 RECOMMENDED IMPLEMENTATION ORDER:")
        print("=" * 50)
        
        print("\n🎯 PHASE 1: Basic Phone Integration")
        print("   1. Sign up for Twilio account")
        print("   2. Get a Twilio phone number")
        print("   3. Implement phone calling to nearest services")
        print("   4. Add emergency message templates")
        
        print("\n🎯 PHASE 2: SMS Backup")
        print("   1. Implement SMS as backup method")
        print("   2. Create detailed emergency SMS templates")
        print("   3. Add SMS confirmation system")
        
        print("\n🎯 PHASE 3: API Integration")
        print("   1. Contact emergency services for API access")
        print("   2. Implement direct dispatch APIs")
        print("   3. Add real-time status tracking")
        
        print("\n🎯 PHASE 4: Advanced Features")
        print("   1. Multi-channel notifications")
        print("   2. Emergency service dashboard")
        print("   3. Real-time tracking and updates")
        
        print("\n💡 QUICK START:")
        print("   1. Get Twilio account: https://www.twilio.com/try-twilio")
        print("   2. Add credentials to .env file")
        print("   3. Implement phone calling in your agents")
        print("   4. Test with real emergency services")
        
        print("\n🔧 INTEGRATION WITH YOUR AGENTS:")
        print("   Your agents already find the nearest services!")
        print("   Now they just need to:")
        print("   1. Select the best service (already implemented)")
        print("   2. Make the phone call/SMS/API call")
        print("   3. Track the response")
        print("   4. Update the user with status")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo_calling_options())
