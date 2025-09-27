"""Test network optimization and minimal response generation."""

import pytest
from app.utils.network_utils import (
    detect_network_quality,
    should_use_minimal_response,
    build_minimal_response,
    build_standard_response,
    NetworkQuality
)
from app.models.dispatch import FrontAgentOutput, ServiceAgentResponse, ServiceType


def test_network_quality_detection():
    """Test network quality detection logic."""
    # Test explicit network quality
    assert detect_network_quality("slow", None) == NetworkQuality.SLOW
    assert detect_network_quality("fast", None) == NetworkQuality.FAST
    
    # Test connection type mapping
    assert detect_network_quality(None, "2g") == NetworkQuality.SLOW
    assert detect_network_quality(None, "3g") == NetworkQuality.MEDIUM
    assert detect_network_quality(None, "4g") == NetworkQuality.FAST
    assert detect_network_quality(None, "wifi") == NetworkQuality.FAST
    
    # Test unknown cases
    assert detect_network_quality(None, None) == NetworkQuality.UNKNOWN


def test_minimal_response_decision():
    """Test when minimal responses should be used."""
    # Slow connection should always use minimal
    assert should_use_minimal_response(NetworkQuality.SLOW, 1) == True
    assert should_use_minimal_response(NetworkQuality.SLOW, 3) == True
    
    # Medium connection with high urgency should use minimal
    assert should_use_minimal_response(NetworkQuality.MEDIUM, 2) == True
    assert should_use_minimal_response(NetworkQuality.MEDIUM, 1) == True
    
    # Medium connection with low urgency should not use minimal
    assert should_use_minimal_response(NetworkQuality.MEDIUM, 3) == False
    
    # Fast connection should not use minimal
    assert should_use_minimal_response(NetworkQuality.FAST, 1) == False
    assert should_use_minimal_response(NetworkQuality.FAST, 3) == False
    
    # Unknown connection should use minimal
    assert should_use_minimal_response(NetworkQuality.UNKNOWN, 1) == True


def test_minimal_response_generation():
    """Test minimal response generation for different languages."""
    # Create test data
    front = FrontAgentOutput(
        keywords=["ambulance", "bleeding", "emergency"],
        urgency=1,
        selected_service=ServiceType.MEDICAL,
        explain="Medical emergency detected",
        follow_up_required=True,
        follow_up_reason="Need more details"
    )
    
    service = ServiceAgentResponse(
        service=ServiceType.MEDICAL,
        subservice="ambulance_dispatch",
        action_taken="dispatched_request_to_ambulance_provider",
        follow_up_required=True,
        follow_up_question="Is the patient conscious and breathing?"
    )
    
    # Test English minimal response
    english_response = build_minimal_response(front, service, "en")
    assert "🏥 MEDICAL" in english_response
    assert "🔴 U1" in english_response
    assert "✓" in english_response  # Action indicator
    assert "?" in english_response  # Follow-up indicator
    assert len(english_response) < 100  # Should be much shorter than standard
    
    # Test Urdu minimal response
    urdu_response = build_minimal_response(front, service, "ur")
    assert "🏥 طبی" in urdu_response or "MEDICAL" in urdu_response
    assert "🔴" in urdu_response
    assert len(urdu_response) < 100
    
    # Test Roman Urdu minimal response
    roman_response = build_minimal_response(front, service, "ur-en")
    assert "🏥 Medical" in roman_response
    assert "🔴" in roman_response
    assert len(roman_response) < 100


def test_standard_vs_minimal_length():
    """Test that minimal responses are significantly shorter."""
    front = FrontAgentOutput(
        keywords=["storm", "flood", "emergency"],
        urgency=2,
        selected_service=ServiceType.DISASTER,
        explain="Disaster situation detected with flooding concerns",
        follow_up_required=True,
        follow_up_reason="Need evacuation details"
    )
    
    service = ServiceAgentResponse(
        service=ServiceType.DISASTER,
        subservice="evacuation_guidance",
        action_taken="evacuation_guidance_shared",
        follow_up_required=True,
        follow_up_question="How many people need evacuation assistance?",
        metadata={"shelter_locations": ["School A", "Community Center B"]}
    )
    
    standard_response = build_standard_response(front, service)
    minimal_response = build_minimal_response(front, service, "en")
    
    # Minimal response should be much shorter
    assert len(minimal_response) < len(standard_response) * 0.5
    
    # Both should contain essential information
    assert "DISASTER" in minimal_response.upper()
    assert "🌪️" in minimal_response or "DISASTER" in minimal_response.upper()
    assert "🟡" in minimal_response or "U2" in minimal_response


def test_stormy_weather_scenario():
    """Test the specific stormy weather scenario mentioned by user."""
    # Simulate user reporting storm with poor 4G connection
    front = FrontAgentOutput(
        keywords=["storm", "heavy rain", "flooding", "emergency"],
        urgency=1,
        selected_service=ServiceType.DISASTER,
        explain="Critical weather emergency detected",
        follow_up_required=True,
        follow_up_reason="Need immediate evacuation details"
    )
    
    service = ServiceAgentResponse(
        service=ServiceType.DISASTER,
        subservice="evacuation_guidance",
        action_taken="emergency_evacuation_dispatched",
        follow_up_required=True,
        follow_up_question="Are you in immediate danger? How many people?"
    )
    
    # Test with slow network (poor 4G during storm)
    network_quality = NetworkQuality.SLOW
    use_minimal = should_use_minimal_response(network_quality, front.urgency)
    
    assert use_minimal == True
    
    minimal_response = build_minimal_response(front, service, "en")
    
    # Response should be very concise for poor connectivity
    assert len(minimal_response) < 80
    assert "🌪️ DISASTER" in minimal_response
    assert "🔴 U1" in minimal_response
    assert "✓" in minimal_response  # Action taken
    assert "?" in minimal_response  # Follow-up needed
    
    print(f"\nStorm scenario minimal response: {minimal_response}")
    print(f"Response length: {len(minimal_response)} characters")


if __name__ == "__main__":
    # Run the stormy weather test
    test_stormy_weather_scenario()
    print("\n✅ Network optimization tests passed!")
