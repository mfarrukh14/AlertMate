#!/usr/bin/env python3
"""
Test smart service selection and calling capabilities
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

async def test_smart_selection_and_calling():
    """Test smart service selection with calling options."""
    
    print("🎯 Testing Smart Service Selection & Calling Options")
    print("=" * 60)
    
    # Test coordinates (Karachi, Pakistan)
    test_lat = 24.8607
    test_lon = 67.0011
    
    try:
        from app.services.smart_service_selector import smart_selector
        
        # Test 1: Smart Medical Service Selection
        print("1. 🏥 Smart Medical Service Selection...")
        medical_result = await smart_selector.select_and_contact_nearest_service(
            lat=test_lat,
            lon=test_lon,
            service_type="medical",
            emergency_level=1,  # High priority
            preferred_contact="phone"
        )
        
        service = medical_result["selected_service"]
        contact = medical_result["contact_result"]
        
        print(f"   ✅ Selected Service:")
        print(f"      🏥 Name: {service.name}")
        print(f"      📞 Phone: {service.phone}")
        print(f"      📍 Address: {service.address}")
        print(f"      📏 Distance: {service.distance_km:.2f} km")
        print(f"      ⏱️ ETA: {service.eta_minutes} minutes")
        print(f"      🎯 Priority Score: {service.priority_score:.2f}")
        print(f"      ✅ Verified: {service.verified}")
        
        print(f"\n   📞 Contact Attempt:")
        print(f"      Method: {contact['contact_method']}")
        print(f"      Status: {contact.get('call_status', contact.get('sms_status', contact.get('api_status', 'unknown')))}")
        print(f"      Success: {contact['success']}")
        
        # Test 2: Smart Police Service Selection
        print("\n2. 🚔 Smart Police Service Selection...")
        police_result = await smart_selector.select_and_contact_nearest_service(
            lat=test_lat,
            lon=test_lon,
            service_type="police",
            emergency_level=1,
            preferred_contact="sms"
        )
        
        service = police_result["selected_service"]
        contact = police_result["contact_result"]
        
        print(f"   ✅ Selected Service:")
        print(f"      🚔 Name: {service.name}")
        print(f"      📞 Phone: {service.phone}")
        print(f"      📏 Distance: {service.distance_km:.2f} km")
        print(f"      ⏱️ ETA: {service.eta_minutes} minutes")
        print(f"      🎯 Priority Score: {service.priority_score:.2f}")
        
        print(f"\n   📱 SMS Contact Attempt:")
        print(f"      Status: {contact.get('sms_status', 'unknown')}")
        print(f"      Success: {contact['success']}")
        
        # Test 3: Smart Fire Service Selection
        print("\n3. 🚒 Smart Fire Service Selection...")
        fire_result = await smart_selector.select_and_contact_nearest_service(
            lat=test_lat,
            lon=test_lon,
            service_type="fire",
            emergency_level=2,
            preferred_contact="api"
        )
        
        service = fire_result["selected_service"]
        contact = fire_result["contact_result"]
        
        print(f"   ✅ Selected Service:")
        print(f"      🚒 Name: {service.name}")
        print(f"      📞 Phone: {service.phone}")
        print(f"      📏 Distance: {service.distance_km:.2f} km")
        print(f"      ⏱️ ETA: {service.eta_minutes} minutes")
        print(f"      🎯 Priority Score: {service.priority_score:.2f}")
        
        print(f"\n   🔌 API Contact Attempt:")
        print(f"      Status: {contact.get('api_status', 'unknown')}")
        print(f"      Success: {contact['success']}")
        
        print("\n" + "=" * 60)
        print("📞 CALLING OPTIONS AVAILABLE:")
        print("=" * 60)
        
        print("\n1. 📞 PHONE CALLS (Twilio Integration)")
        print("   ✅ Make actual phone calls to emergency services")
        print("   💰 Cost: ~$0.02 per minute")
        print("   🔧 Setup: Get Twilio account + phone number")
        print("   📋 Example:")
        print("      - Call hospital: 'Emergency at [location], patient needs immediate care'")
        print("      - Call police: 'Crime in progress at [location], suspects [description]'")
        print("      - Call fire: 'Fire emergency at [location], [fire type]'")
        
        print("\n2. 📱 SMS MESSAGES (Twilio/AWS SNS)")
        print("   ✅ Send automated SMS to emergency services")
        print("   💰 Cost: ~$0.0075 per SMS")
        print("   🔧 Setup: Twilio or AWS SNS account")
        print("   📋 Example SMS:")
        print("      'EMERGENCY ALERT: Medical emergency at 24.8607,67.0011. Patient needs ambulance. Contact: [user_phone]'")
        
        print("\n3. 🔌 API INTEGRATION")
        print("   ✅ Direct API calls to emergency service systems")
        print("   💰 Cost: Usually free (if they provide APIs)")
        print("   🔧 Setup: Emergency service API credentials")
        print("   📋 Example:")
        print("      - Hospital dispatch API")
        print("      - Police CAD system API")
        print("      - Fire department dispatch API")
        
        print("\n4. 📧 EMAIL NOTIFICATIONS")
        print("   ✅ Send detailed email alerts")
        print("   💰 Cost: ~$0.10 per 1000 emails (AWS SES)")
        print("   🔧 Setup: Email service provider")
        print("   📋 Example:")
        print("      - Detailed emergency report")
        print("      - Patient information")
        print("      - Location coordinates and directions")
        
        print("\n5. 🌐 WEBHOOK INTEGRATION")
        print("   ✅ Real-time notifications to emergency services")
        print("   💰 Cost: Free (if they accept webhooks)")
        print("   🔧 Setup: Emergency service webhook endpoints")
        print("   📋 Example:")
        print("      - Instant dispatch to nearest units")
        print("      - Real-time location updates")
        print("      - Status tracking")
        
        print("\n" + "=" * 60)
        print("🚀 IMPLEMENTATION RECOMMENDATIONS:")
        print("=" * 60)
        
        print("\n🎯 PRIORITY 1: Twilio Phone Integration")
        print("   - Most reliable for emergency situations")
        print("   - Direct voice communication")
        print("   - Works with any phone number")
        
        print("\n🎯 PRIORITY 2: SMS Backup")
        print("   - Backup when phone calls fail")
        print("   - Can include detailed information")
        print("   - Works internationally")
        
        print("\n🎯 PRIORITY 3: Emergency Service APIs")
        print("   - Most efficient for dispatch")
        print("   - Real-time integration")
        print("   - Automatic status updates")
        
        print("\n💡 NEXT STEPS:")
        print("   1. Sign up for Twilio account")
        print("   2. Get emergency service API access")
        print("   3. Implement phone calling first")
        print("   4. Add SMS as backup")
        print("   5. Integrate with emergency service APIs")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_smart_selection_and_calling())
