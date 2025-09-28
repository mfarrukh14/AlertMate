"""Network connectivity detection and response optimization utilities."""

from __future__ import annotations

import enum
import logging
from typing import Dict, Any, Optional

from app.models.dispatch import ServiceType, FrontAgentOutput, ServiceAgentResponse

logger = logging.getLogger(__name__)


class NetworkQuality(str, enum.Enum):
    SLOW = "slow"
    MEDIUM = "medium"
    FAST = "fast"
    UNKNOWN = "unknown"


class ConnectionType(str, enum.Enum):
    G2 = "2g"
    G3 = "3g"
    G4 = "4g"
    WIFI = "wifi"
    UNKNOWN = "unknown"


def detect_network_quality(network_quality: Optional[str], connection_type: Optional[str]) -> NetworkQuality:
    """Detect network quality based on provided parameters and heuristics."""
    if network_quality and network_quality.lower() in [q.value for q in NetworkQuality]:
        return NetworkQuality(network_quality.lower())
    
    if connection_type:
        connection_lower = connection_type.lower()
        if connection_lower in ["2g"]:
            return NetworkQuality.SLOW
        elif connection_lower in ["3g"]:
            return NetworkQuality.MEDIUM
        elif connection_lower in ["4g", "wifi"]:
            return NetworkQuality.FAST
    
    return NetworkQuality.UNKNOWN


def should_use_minimal_response(network_quality: NetworkQuality, urgency: int) -> bool:
    """Determine if minimal response should be used based on network quality and urgency."""
    # Always use minimal responses for slow connections
    if network_quality == NetworkQuality.SLOW:
        return True
    
    # For medium connections, use minimal for high urgency (need quick responses)
    if network_quality == NetworkQuality.MEDIUM and urgency <= 2:
        return True
    
    # For unknown connections, assume good connection and use full responses
    if network_quality == NetworkQuality.UNKNOWN:
        return False
    
    return False


def build_minimal_response(front: FrontAgentOutput, service: ServiceAgentResponse, language: str = "en") -> str:
    """Build ultra-minimal response for poor network conditions."""
    
    # Language-specific minimal responses
    if language in ["ur", "urdu"]:
        return _build_minimal_urdu_response(front, service)
    elif language == "ur-en":
        return _build_minimal_roman_urdu_response(front, service)
    else:
        return _build_minimal_english_response(front, service)


def _build_minimal_english_response(front: FrontAgentOutput, service: ServiceAgentResponse) -> str:
    """Build minimal English response."""
    parts = []
    
    # Service routing (critical info)
    if service.service != ServiceType.GENERAL:
        service_emoji = {"medical": "🏥", "police": "🚔", "disaster": "🌪️"}.get(service.service.value, "📞")
        parts.append(f"{service_emoji} {service.service.value.upper()}")
    
    # Urgency indicator
    urgency_emoji = {1: "🔴", 2: "🟡", 3: "🟢"}.get(front.urgency, "⚪")
    parts.append(f"{urgency_emoji} U{front.urgency}")
    
    # Action taken (if critical)
    if service.action_taken and front.urgency <= 2:
        action_short = _shorten_action(service.action_taken)
        parts.append(f"✓ {action_short}")
    
    # Follow-up (only if urgent)
    if service.follow_up_required and front.urgency <= 2:
        follow_short = _shorten_follow_up(service.follow_up_question)
        parts.append(f"? {follow_short}")
    
    return " | ".join(parts)


def _build_minimal_urdu_response(front: FrontAgentOutput, service: ServiceAgentResponse) -> str:
    """Build minimal Urdu response."""
    parts = []
    
    # Service routing in Urdu
    if service.service != ServiceType.GENERAL:
        urdu_services = {
            "medical": "🏥 طبی",
            "police": "🚔 پولیس", 
            "disaster": "🌪️ آفت"
        }
        parts.append(urdu_services.get(service.service.value, f"📞 {service.service.value}"))
    
    # Urgency in Urdu
    urdu_urgency = {1: "🔴 فوری", 2: "🟡 ضروری", 3: "🟢 عام"}.get(front.urgency, "⚪")
    parts.append(urdu_urgency)
    
    # Action taken
    if service.action_taken and front.urgency <= 2:
        urdu_action = _translate_action_urdu(service.action_taken)
        parts.append(f"✓ {urdu_action}")
    
    # Follow-up
    if service.follow_up_required and front.urgency <= 2:
        urdu_follow = _translate_follow_up_urdu(service.follow_up_question)
        parts.append(f"? {urdu_follow}")
    
    return " | ".join(parts)


def _build_minimal_roman_urdu_response(front: FrontAgentOutput, service: ServiceAgentResponse) -> str:
    """Build minimal Roman Urdu response."""
    parts = []
    
    # Service routing in Roman Urdu
    if service.service != ServiceType.GENERAL:
        roman_services = {
            "medical": "🏥 Medical",
            "police": "🚔 Police", 
            "disaster": "🌪️ Disaster"
        }
        parts.append(roman_services.get(service.service.value, f"📞 {service.service.value}"))
    
    # Urgency
    roman_urgency = {1: "🔴 Zaroori", 2: "🟡 Important", 3: "🟢 Normal"}.get(front.urgency, "⚪")
    parts.append(roman_urgency)
    
    # Action taken
    if service.action_taken and front.urgency <= 2:
        roman_action = _translate_action_roman_urdu(service.action_taken)
        parts.append(f"✓ {roman_action}")
    
    # Follow-up
    if service.follow_up_required and front.urgency <= 2:
        roman_follow = _translate_follow_up_roman_urdu(service.follow_up_question)
        parts.append(f"? {roman_follow}")
    
    return " | ".join(parts)


def _shorten_action(action: str) -> str:
    """Shorten action descriptions for minimal responses."""
    if not action:
        return ""
    
    action_lower = action.lower()
    if "dispatch" in action_lower:
        return "Dispatched"
    elif "alert" in action_lower:
        return "Alerted"
    elif "request" in action_lower:
        return "Requested"
    elif "sent" in action_lower:
        return "Sent"
    elif "created" in action_lower:
        return "Created"
    else:
        # Return first word or first 8 chars
        words = action.split()
        return words[0] if words else action[:8]


def _shorten_follow_up(follow_up: str) -> str:
    """Shorten follow-up questions for minimal responses."""
    if not follow_up:
        return ""
    
    # Extract key question words
    follow_lower = follow_up.lower()
    if "conscious" in follow_lower:
        return "Conscious?"
    elif "breathing" in follow_lower:
        return "Breathing?"
    elif "bleeding" in follow_lower:
        return "Bleeding?"
    elif "safe" in follow_lower:
        return "Safe?"
    elif "location" in follow_lower:
        return "Where?"
    else:
        # Return first 15 chars
        return follow_up[:15] + "..." if len(follow_up) > 15 else follow_up


def _translate_action_urdu(action: str) -> str:
    """Translate action to Urdu for minimal responses."""
    if not action:
        return ""
    
    action_lower = action.lower()
    urdu_actions = {
        "dispatch": "بھیجا",
        "alert": "الرٹ",
        "request": "درخواست",
        "sent": "بھیجا",
        "created": "بنایا"
    }
    
    for eng, urdu in urdu_actions.items():
        if eng in action_lower:
            return urdu
    
    return action[:8]


def _translate_follow_up_urdu(follow_up: str) -> str:
    """Translate follow-up to Urdu for minimal responses."""
    if not follow_up:
        return ""
    
    follow_lower = follow_up.lower()
    urdu_questions = {
        "conscious": "ہوش میں؟",
        "breathing": "سانس؟",
        "bleeding": "خون؟",
        "safe": "محفوظ؟",
        "location": "کہاں؟"
    }
    
    for eng, urdu in urdu_questions.items():
        if eng in follow_lower:
            return urdu
    
    return follow_up[:12]


def _translate_action_roman_urdu(action: str) -> str:
    """Translate action to Roman Urdu for minimal responses."""
    if not action:
        return ""
    
    action_lower = action.lower()
    roman_actions = {
        "dispatch": "Bhijaya",
        "alert": "Alert",
        "request": "Request",
        "sent": "Bhijaya",
        "created": "Banaya"
    }
    
    for eng, roman in roman_actions.items():
        if eng in action_lower:
            return roman
    
    return action[:8]


def _translate_follow_up_roman_urdu(follow_up: str) -> str:
    """Translate follow-up to Roman Urdu for minimal responses."""
    if not follow_up:
        return ""
    
    follow_lower = follow_up.lower()
    roman_questions = {
        "conscious": "Hosh mein?",
        "breathing": "Saans?",
        "bleeding": "Khoon?",
        "safe": "Mehfooz?",
        "location": "Kahan?"
    }
    
    for eng, roman in roman_questions.items():
        if eng in follow_lower:
            return roman
    
    return follow_up[:12]


def build_standard_response(front: FrontAgentOutput, service: ServiceAgentResponse) -> str:
    """Build standard detailed response for good network conditions."""
    sections: list[str] = []

    # Use conversational front message format - don't show technical explain content
    if front.explain:
        explain = front.explain
        # Check if it's a technical explanation that should be converted to conversational
        if ("urgency" in explain.lower() or "selected" in explain.lower() or 
            "property theft" in explain.lower() or "car stolen" in explain.lower() or
            "theft has occurred" in explain.lower() or "broken arm" in explain.lower() or
            "flood has been reported" in explain.lower() or "bike accident" in explain.lower() or
            "bleeding" in explain.lower() or "broken leg" in explain.lower()):
            # Convert technical format to conversational - don't show the technical line
            if "immediate life-threatening" in explain.lower():
                sections.append("🚨 I understand this is a life-threatening emergency. Let me get you help immediately.")
            elif ("serious" in explain.lower() or "property theft" in explain.lower() or "car stolen" in explain.lower() or 
                  "medical attention" in explain.lower() or "fits" in explain.lower() or "seizure" in explain.lower() or
                  "theft has occurred" in explain.lower() or "broken arm" in explain.lower() or
                  "flood has been reported" in explain.lower() or "bike accident" in explain.lower() or
                  "bleeding" in explain.lower() or "broken leg" in explain.lower()):
                sections.append("⚠️ I can see this is a serious situation. I'm connecting you with the right service.")
            elif "informational" in explain.lower():
                sections.append("ℹ️ I've noted your request and I'm here to help.")
            else:
                sections.append("I understand your situation and I'm here to help.")
        else:
            # Only show non-technical explanations
            if not any(tech_word in explain.lower() for tech_word in ["urgency", "selected", "priority", "keywords", "has occurred", "has been reported", "bike accident", "bleeding", "broken leg"]):
                sections.append(explain)
    
    if front.follow_up_required and front.follow_up_reason:
        sections.append(f"Quick question: {front.follow_up_reason}")

    # Check if this is a follow-up response that should be handled differently
    is_followup_to_medical = (
        service.service == ServiceType.MEDICAL and 
        service.action_taken and 
        "triage_questions_sent" in service.action_taken.lower() and
        front.explain and 
        any(medical_term in front.explain.lower() for medical_term in [
            "bleeding", "broken", "leg", "arm", "conscious", "breathing", "patient"
        ])
    )
    
    is_followup_to_police = (
        service.service == ServiceType.POLICE and 
        service.action_taken and 
        "non_emergency_guidance_sent" in service.action_taken.lower() and
        front.explain and 
        any(police_term in front.explain.lower() for police_term in [
            "theft", "stolen", "bike", "suspect", "description"
        ])
    )

    # Use conversational service message format
    service_emojis = {
        "medical": "🏥",
        "police": "🚔", 
        "disaster": "🌪️",
        "general": "📞"
    }
    emoji = service_emojis.get(service.service.value, "📞")
    
    if service.service == ServiceType.GENERAL:
        sections.append("📞 I'm here to help. Let me know what you need.")
    else:
        # Handle follow-up responses differently
        if is_followup_to_medical or is_followup_to_police:
            # For follow-up responses, just acknowledge the additional information
            if is_followup_to_medical:
                sections.append("✅ Thank you for the additional medical information. I've updated the emergency response.")
            elif is_followup_to_police:
                sections.append("✅ Thank you for the additional incident details. I've updated the police report.")
        else:
            # Build service connection message with actual service center info
            service_message = f"{emoji} I've connected you with {service.service.value.upper()} services."
            
            # Add service center information from metadata if available
            if service.metadata:
                if "destination" in service.metadata and isinstance(service.metadata["destination"], dict):
                    dest = service.metadata["destination"]
                    if "name" in dest and "phone" in dest:
                        service_message += f"\n\n🏢 Nearest {service.service.value.title()} Center: {dest['name']}\n📞 Phone: {dest['phone']}"
                        if "distance_km" in service.metadata:
                            service_message += f"\n📍 Distance: {service.metadata['distance_km']} km"
                        if "eta_minutes" in service.metadata:
                            service_message += f"\n⏱️ ETA: {service.metadata['eta_minutes']} minutes"
                elif "assigned_station" in service.metadata and isinstance(service.metadata["assigned_station"], dict):
                    station = service.metadata["assigned_station"]
                    if "name" in station and "phone" in station:
                        service_message += f"\n\n🏢 Assigned Station: {station['name']}\n📞 Phone: {station['phone']}"
                        if "distance_km" in station:
                            service_message += f"\n📍 Distance: {station['distance_km']} km"
                elif "ranked_options" in service.metadata and isinstance(service.metadata["ranked_options"], list) and len(service.metadata["ranked_options"]) > 0:
                    # For medical services with hospital options
                    best_hospital = service.metadata["ranked_options"][0]
                    if "name" in best_hospital and "phone" in best_hospital:
                        service_message += f"\n\n🏥 Nearest Hospital: {best_hospital['name']}\n📞 Phone: {best_hospital['phone']}"
                        if "distance_km" in best_hospital:
                            service_message += f"\n📍 Distance: {best_hospital['distance_km']} km"
                        if "eta_minutes" in best_hospital:
                            service_message += f"\n⏱️ ETA: {best_hospital['eta_minutes']} minutes"
            
            sections.append(service_message)
        
        # Make action taken more conversational - hide technical status messages
        # Only show action messages if we don't have service center info (to avoid duplication)
        has_service_center_info = (
            (service.metadata and "destination" in service.metadata) or
            (service.metadata and "assigned_station" in service.metadata) or
            (service.metadata and "ranked_options" in service.metadata)
        )
        
        # Also check if this is a follow-up response that should be handled differently
        is_followup_response = (
            service.action_taken and 
            any(followup_action in service.action_taken.lower() for followup_action in [
                "triage_questions_sent", "non_emergency_guidance_sent", "evacuation_guidance_shared"
            ])
        )
        
        if service.action_taken and not has_service_center_info and not is_followup_response:
            action_lower = service.action_taken.lower()
            if "incident_report_created" in action_lower:
                sections.append("✅ I've created an incident report for you.")
            elif "dispatch" in action_lower:
                sections.append("✅ Emergency units have been dispatched to your location.")
            elif "alert" in action_lower:
                sections.append("✅ I've sent out emergency alerts.")
            elif "triage_questions_sent" in action_lower:
                sections.append("✅ I've connected you with medical services.")
            elif "non_emergency_guidance_sent" in action_lower:
                sections.append("✅ I've connected you with police services.")
            elif "evacuation_guidance_shared" in action_lower:
                sections.append("✅ I've connected you with disaster services.")
            elif "evacuation_coordination_initiated" in action_lower:
                sections.append("✅ Emergency evacuation coordination has been initiated.")
            elif "resource_request_logged" in action_lower:
                sections.append("✅ I've logged your resource request.")
            elif "infrastructure_team_alerted" in action_lower:
                sections.append("✅ Infrastructure teams have been alerted.")
            elif "emergency_units_dispatched" in action_lower:
                sections.append("✅ Emergency units have been dispatched.")
            elif "evidence_preservation_guidance_shared" in action_lower:
                sections.append("✅ I've shared evidence preservation guidance.")
            elif "suspect_information_requested" in action_lower:
                sections.append("✅ I've requested suspect information.")
            elif "appointment_booking_guidance_shared" in action_lower:
                sections.append("✅ I've shared appointment booking guidance.")
            elif "prescription_refill_guidance_provided" in action_lower:
                sections.append("✅ I've provided prescription refill guidance.")
            elif "returned_nearest_hospitals" in action_lower:
                sections.append("✅ I've found the nearest hospitals for you.")
            elif "dispatched_request_to_ambulance_provider" in action_lower:
                sections.append("✅ I've dispatched an ambulance request.")
            # Only show action if it's not a technical status message
            elif not any(tech_status in action_lower for tech_status in [
                "_sent", "_shared", "_logged", "_alerted", "_initiated", "_requested", 
                "_provided", "_returned", "_dispatched", "_created"
            ]):
                sections.append(f"✅ {service.action_taken}")
        
        # Make follow-up questions more conversational
        if service.follow_up_required and service.follow_up_question:
            sections.append(f"❓ {service.follow_up_question}")

    return "\n\n".join(section.strip() for section in sections if section)
