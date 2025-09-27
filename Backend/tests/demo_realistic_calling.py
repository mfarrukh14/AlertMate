#!/usr/bin/env python3
"""
Realistic emergency calling simulation demo for PoC
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

async def demo_realistic_emergency_calling():
    """Demo realistic emergency calling simulation."""
    
    print("🚨 REALISTIC EMERGENCY CALLING SIMULATION")
    print("=" * 60)
    print("📱 Simulating real-world emergency service calls")
    print("🔧 PoC demonstration without actual Twilio integration")
    print()
    
    # Test coordinates (Karachi, Pakistan)
    test_lat = 24.8607
    test_lon = 67.0011
    
    try:
        from app.services.hybrid_service_discovery import HybridServiceDiscovery
        from app.services.emergency_calling_simulator import calling_simulator
        
        discovery = HybridServiceDiscovery()
        
        # Find real emergency services
        print("🔍 Finding Real Emergency Services...")
        
        medical_result = await discovery.find_emergency_services(
            lat=test_lat, lon=test_lon, service_type="medical", radius_km=10, max_results=3
        )
        police_result = await discovery.find_emergency_services(
            lat=test_lat, lon=test_lon, service_type="police", radius_km=15, max_results=3
        )
        fire_result = await discovery.find_emergency_services(
            lat=test_lat, lon=test_lon, service_type="fire", radius_km=15, max_results=3
        )
        
        print(f"✅ Found {len(medical_result.services)} hospitals")
        print(f"✅ Found {len(police_result.services)} police stations")
        print(f"✅ Found {len(fire_result.services)} fire stations")
        
        # Test 1: Single Medical Emergency Call
        print("\n" + "=" * 60)
        print("1. 🏥 MEDICAL EMERGENCY - Single Service Call")
        print("=" * 60)
        
        if medical_result.services:
            best_hospital = medical_result.services[0]
            
            print(f"📍 Location: Karachi, Pakistan ({test_lat}, {test_lon})")
            print(f"🚨 Emergency: Medical emergency - Patient needs immediate care")
            print(f"🏥 Calling: {best_hospital.name}")
            print(f"📞 Phone: {best_hospital.phone or 'Emergency number: 1122'}")
            print(f"📏 Distance: {best_hospital.distance_km:.2f} km")
            print()
            
            # Simulate the call
            call_result = await calling_simulator.simulate_emergency_call(
                service_name=best_hospital.name,
                phone_number=best_hospital.phone or "1122",
                service_type="medical",
                emergency_level=1,  # High priority
                location={"lat": test_lat, "lon": test_lon},
                emergency_details="Patient unconscious, breathing difficulties"
            )
            
            print(f"📞 Call Result:")
            print(f"   📋 Call ID: {call_result.call_id}")
            print(f"   📱 Status: {call_result.call_status.value}")
            print(f"   ⏱️ Response Time: {call_result.response_time} seconds")
            print(f"   ⏰ Call Duration: {call_result.call_duration} seconds")
            print(f"   🚑 Dispatched: {'Yes' if call_result.dispatched else 'No'}")
            if call_result.dispatched:
                print(f"   🕐 ETA: {call_result.eta_minutes} minutes")
            print(f"   📝 Notes: {call_result.notes}")
        
        # Test 2: Police Emergency with Backup
        print("\n" + "=" * 60)
        print("2. 🚔 POLICE EMERGENCY - With Backup Service")
        print("=" * 60)
        
        if police_result.services:
            primary_police = police_result.services[0]
            
            print(f"🚨 Emergency: Crime in progress - Armed robbery")
            print(f"🚔 Primary: {primary_police.name}")
            print(f"📞 Phone: {primary_police.phone or 'Emergency number: 15'}")
            print()
            
            # Simulate primary call
            primary_call = await calling_simulator.simulate_emergency_call(
                service_name=primary_police.name,
                phone_number=primary_police.phone or "15",
                service_type="police",
                emergency_level=1
            )
            
            print(f"📞 Primary Call Result:")
            print(f"   📋 Call ID: {primary_call.call_id}")
            print(f"   📱 Status: {primary_call.call_status.value}")
            print(f"   🚑 Dispatched: {'Yes' if primary_call.dispatched else 'No'}")
            
            # If primary failed, try backup
            if not primary_call.dispatched and len(police_result.services) > 1:
                backup_police = police_result.services[1]
                print(f"\n🔄 Trying backup service: {backup_police.name}")
                
                backup_call = await calling_simulator.simulate_emergency_call(
                    service_name=backup_police.name,
                    phone_number=backup_police.phone or "15",
                    service_type="police",
                    emergency_level=1
                )
                
                print(f"📞 Backup Call Result:")
                print(f"   📋 Call ID: {backup_call.call_id}")
                print(f"   📱 Status: {backup_call.call_status.value}")
                print(f"   🚑 Dispatched: {'Yes' if backup_call.dispatched else 'No'}")
        
        # Test 3: Multi-Service Disaster Response
        print("\n" + "=" * 60)
        print("3. 🌪️ DISASTER EMERGENCY - Multi-Service Coordination")
        print("=" * 60)
        
        print(f"🚨 Emergency: Building collapse - Multiple casualties")
        print(f"🎯 Coordinating: Medical, Fire, Police services")
        print()
        
        # Prepare services for coordination
        services_to_coordinate = []
        
        if medical_result.services:
            best_hospital = medical_result.services[0]
            services_to_coordinate.append({
                "name": best_hospital.name,
                "phone": best_hospital.phone or "1122",
                "type": "medical"
            })
        
        if fire_result.services:
            best_fire = fire_result.services[0]
            services_to_coordinate.append({
                "name": best_fire.name,
                "phone": best_fire.phone or "16",
                "type": "fire"
            })
        
        if police_result.services:
            best_police = police_result.services[0]
            services_to_coordinate.append({
                "name": best_police.name,
                "phone": best_police.phone or "15",
                "type": "police"
            })
        
        # Simulate multi-service coordination
        coordination_result = await calling_simulator.simulate_multi_service_coordination(
            services=services_to_coordinate,
            emergency_type="building_collapse",
            emergency_level=1
        )
        
        print(f"🎯 Coordination Result:")
        print(f"   📋 Coordination ID: {coordination_result['coordination_id']}")
        print(f"   🚨 Emergency Type: {coordination_result['emergency_type']}")
        print(f"   📞 Services Contacted: {coordination_result['services_contacted']}")
        print(f"   🚑 Services Dispatched: {coordination_result['services_dispatched']}")
        print(f"   📊 Success Rate: {coordination_result['success_rate']:.1%}")
        print(f"   ✅ Overall Status: {coordination_result['overall_status']}")
        
        print(f"\n📞 Individual Service Results:")
        for service_type, call_result in coordination_result['results'].items():
            status_emoji = "✅" if call_result.dispatched else "❌"
            print(f"   {status_emoji} {service_type.title()}: {call_result.service_name}")
            print(f"      📱 Status: {call_result.call_status.value}")
            if call_result.dispatched:
                print(f"      🕐 ETA: {call_result.eta_minutes} minutes")
        
        # Test 4: SMS Backup
        print("\n" + "=" * 60)
        print("4. 📱 SMS BACKUP NOTIFICATION")
        print("=" * 60)
        
        if medical_result.services:
            hospital = medical_result.services[0]
            
            print(f"📱 Sending SMS backup to: {hospital.name}")
            print(f"📞 Phone: {hospital.phone or 'Emergency number: 1122'}")
            
            sms_result = await calling_simulator.simulate_sms_notification(
                service_name=hospital.name,
                phone_number=hospital.phone or "1122",
                emergency_details="URGENT: Medical emergency at location. Patient needs immediate assistance. Location: Karachi coordinates provided."
            )
            
            print(f"📱 SMS Result:")
            print(f"   📋 Message ID: {sms_result['message_id']}")
            print(f"   ✅ Status: {sms_result['status']}")
            print(f"   ⏰ Delivery Time: {sms_result['delivery_time']}")
            print(f"   🕐 Response Expected: {sms_result['response_expected']} seconds")
        
        # Show overall statistics
        print("\n" + "=" * 60)
        print("📊 CALLING STATISTICS")
        print("=" * 60)
        
        stats = calling_simulator.get_call_statistics()
        
        print(f"📞 Total Calls Made: {stats['total_calls']}")
        print(f"✅ Successful Dispatches: {stats['successful_dispatches']}")
        print(f"📊 Success Rate: {stats['success_rate']:.1%}")
        print(f"⏱️ Average Response Time: {stats['average_response_time']} seconds")
        print(f"⏰ Average Call Duration: {stats['average_call_duration']} seconds")
        
        print("\n🔄 Recent Calls:")
        for call in stats['recent_calls']:
            status_emoji = "✅" if call.dispatched else "❌"
            print(f"   {status_emoji} {call.service_name} - {call.call_status.value}")
            if call.dispatched:
                print(f"      🕐 ETA: {call.eta_minutes} minutes")
        
        print("\n" + "=" * 60)
        print("🎉 REALISTIC CALLING SIMULATION COMPLETE!")
        print("=" * 60)
        print("✅ Simulated real emergency service calls")
        print("✅ Demonstrated multi-service coordination")
        print("✅ Showed backup and SMS options")
        print("✅ Provided realistic response times and ETAs")
        print()
        print("🚀 Ready for Production:")
        print("   - Replace simulator with actual Twilio integration")
        print("   - Add real emergency service APIs")
        print("   - Implement status tracking and updates")
        print("   - Add user notification system")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo_realistic_emergency_calling())
