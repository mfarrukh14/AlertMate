#!/usr/bin/env python3
"""Test user-friendly response formatting."""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.agents.router import DispatchRouter
from app.models.dispatch import DispatchRequest

def test_user_friendly_responses():
    """Test that responses are user-friendly without technical jargon."""
    print("🔍 Testing User-Friendly Response Formatting...")
    print("=" * 60)
    
    router = DispatchRouter()
    
    # Test scenarios from the user's examples
    test_cases = [
        {
            "name": "Theft in Shop (Urdu)",
            "query": "Dukaaan men chori hogyi hai",
            "expected_no_tech": ["urgency", "selected", "non_emergency_guidance_sent"]
        },
        {
            "name": "Broken Arm (Urdu)",
            "query": "Merey betay ka bazu toot gya hai",
            "expected_no_tech": ["urgency", "selected", "triage_questions_sent"]
        },
        {
            "name": "Flood Emergency",
            "query": "There is flood in soan river",
            "expected_no_tech": ["urgency", "selected", "evacuation_guidance_shared"]
        },
        {
            "name": "Flood Follow-up",
            "query": "45-60 persons",
            "expected_no_tech": ["urgency", "selected"]
        }
    ]
    
    results = []
    for case in test_cases:
        print(f"\n🔍 Testing: {case['name']}")
        print(f"Query: '{case['query']}'")
        
        request = DispatchRequest(
            userid="test_user",
            user_query=case["query"],
            user_location="Test Location",
            lat=33.550274,
            lon=73.094238,
            lang="en",
            network_quality="fast",
            connection_type="4g"
        )
        
        try:
            front_output, service_response = router.process(request, f"test-{case['name'].lower().replace(' ', '-')}")
            
            # Check front message
            front_message = router._format_front_message(front_output)
            print(f"  Front message: {front_message}")
            
            # Check service message
            service_message = router._format_service_message(service_response)
            print(f"  Service message: {service_message}")
            
            # Check for technical jargon
            full_response = f"{front_message} {service_message}".lower()
            has_tech_jargon = any(tech_word in full_response for tech_word in case["expected_no_tech"])
            
            if has_tech_jargon:
                print(f"  ❌ Contains technical jargon: {[word for word in case['expected_no_tech'] if word in full_response]}")
                results.append(False)
            else:
                print(f"  ✅ User-friendly response")
                results.append(True)
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 USER-FRIENDLY RESPONSE TEST RESULTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Responses are now user-friendly!")
        print("✅ No more technical jargon shown to users")
    else:
        print("⚠️  Some tests failed. Technical jargon still present.")
    
    return passed == total

if __name__ == "__main__":
    success = test_user_friendly_responses()
    sys.exit(0 if success else 1)
