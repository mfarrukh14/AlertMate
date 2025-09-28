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
    # Only use minimal responses for very slow connections
    if network_quality == NetworkQuality.SLOW:
        return True
    
    # For medium connections, only use minimal for very high urgency (need quick responses)
    if network_quality == NetworkQuality.MEDIUM and urgency == 1:
        return True
    
    # For unknown connections, assume medium and use standard responses
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

    sections.append(front.explain)
    sections.append(
        " "
        f"Priority level: {front.urgency} (1=low, 3=high). Keywords noted: {', '.join(front.keywords)}."
    )

    if service.service == ServiceType.GENERAL:
        sections.append(
            "I'll stay on the line until I know more. "
            "No emergency service has been engaged yet."
        )
    else:
        service_intro = (
            f"I've routed this to the {service.service.value.upper()} team"
            f" (subservice: {service.subservice})."
        )
        if service.action_taken:
            service_intro += f" Action taken: {service.action_taken}."
        sections.append(service_intro)

    if front.follow_up_required and front.follow_up_reason:
        sections.append(f"Heads-up: {front.follow_up_reason}")

    if service.follow_up_required:
        follow_up_text = service.follow_up_question or "They'll need more details shortly."
        sections.append(f"Next step: {follow_up_text}")

    if service.metadata:
        metadata_bits = ", ".join(f"{k}: {v}" for k, v in service.metadata.items())
        sections.append(f"Additional info: {metadata_bits}")

    return "\n\n".join(section.strip() for section in sections if section)
