"""Front dispatcher agent implementing Groq-powered routing with rule fallback."""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Iterable, List, Optional, Tuple

from pydantic import ValidationError

from app.models.dispatch import DispatchRequest, FrontAgentOutput, ServiceType
from app.utils.llm_client import LLMError, llm_client
from app.utils.urdu_language import (
    detect_urdu_language,
    extract_urdu_keywords,
    is_urdu_greeting,
    get_urdu_service_keywords,
    get_urdu_urgency_level,
    get_urdu_follow_up_message,
    transliterate_roman_to_urdu,
)

_STOPWORDS = {
    "i",
    "the",
    "and",
    "a",
    "an",
    "to",
    "for",
    "my",
    "me",
    "is",
    "of",
    "on",
    "in",
    "with",
    "need",
    "please",
    "help",
    "it",
    "we",
    "us",
    "our",
    "am",
}

_SERVICE_KEYWORDS = {
    ServiceType.MEDICAL: {
        "ambulance",
        "bleeding",
        "broken",
        "fracture",
        "injury",
        "pain",
        "hospital",
        "doctor",
        "medic",
        "unconscious",
        "chest",
        "breathing",
        "leg",
        "arm",
    },
    ServiceType.POLICE: {
        "robbery",
        "robbed",
        "assault",
        "attack",
        "threat",
        "gun",
        "knife",
        "suspect",
        "stole",
        "steal",
        "violence",
        "shooting",
        "burglary",
        "theft",
        "crime",
    },
    ServiceType.DISASTER: {
        "flood",
        "earthquake",
        "landslide",
        "tsunami",
        "fire",
        "wildfire",
        "evacuate",
        "evacuation",
        "hazard",
        "storm",
        "cyclone",
        "hurricane",
        "collapse",
        "damage",
    },
}

_URGENCY_1 = {
    "not breathing",
    "unconscious",
    "cardiac arrest",
    "heavy bleeding",
    "gun",
    "shooting",
    "fire",
    "explosion",
    "trapped",
    "immediate danger",
}

_URGENCY_2 = {
    "fracture",
    "broken",
    "severe pain",
    "robbery",
    "assault",
    "threat",
    "flood",
    "collapse",
    "landslide",
    "earthquake",
}

_URGENCY_1_TOKENS = {
    "ambulance",
    "unconscious",
    "shooting",
    "gun",
    "fire",
    "bleeding",
    "threat",
    "attack",
}

_URGENCY_2_TOKENS = {
    "broken",
    "broke",
    "fracture",
    "robbery",
    "stole",
    "assault",
    "flood",
    "collapse",
    "landslide",
    "earthquake",
}

_PHRASE_PATTERNS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    ("broke leg", re.compile(r"broke (my )?leg")),
    ("broke arm", re.compile(r"broke (my )?arm")),
    ("heavy bleeding", re.compile(r"heavy bleeding")),
    ("need ambulance", re.compile(r"need (an )?ambulance")),
    ("robbery in progress", re.compile(r"(robbery|robbed).*(now|just)")),
    ("flooded street", re.compile(r"flood(ed)? street")),
)

_GREETINGS = {
    "hi",
    "hello",
    "hey",
    "salam",
    "salaam",
    "salaam alaikum",
    "salam alaikum",
    "good morning",
    "good afternoon",
    "good evening",
    "greetings",
    "assalamualaikum",
    "assalamu alaikum",
}

logger = logging.getLogger(__name__)


class FrontDispatcherAgent:
    """Front dispatcher using Groq LLM with rule-based fallback."""

    def extract_keywords(self, query: str) -> List[str]:
        # Detect language
        language = detect_urdu_language(query)
        
        # Extract Urdu-specific keywords first
        urdu_keywords = extract_urdu_keywords(query, language)
        
        # Extract English keywords
        query_lower = query.lower()
        raw_tokens = re.findall(r"[a-z0-9']+", query_lower)
        filtered = [token for token in raw_tokens if token not in _STOPWORDS and len(token) > 2]

        counts = Counter(filtered)
        english_keywords: List[str] = []

        for phrase, pattern in _PHRASE_PATTERNS:
            if pattern.search(query_lower):
                english_keywords.append(phrase)

        for token, _ in counts.most_common():
            if token not in english_keywords:
                english_keywords.append(token)
            if len(english_keywords) >= 8:
                break

        # Combine Urdu and English keywords, prioritizing emergency-related ones
        all_keywords = urdu_keywords + english_keywords
        return all_keywords[:8]

    def _ensure_minimum_keywords(self, keywords: List[str], query: str) -> List[str]:
        normalized = [kw.strip() for kw in keywords if kw and kw.strip()]

        if len(normalized) >= 3:
            return normalized[:8]

        query_tokens = re.findall(r"[a-z0-9']+", query.lower())
        for token in query_tokens:
            if token in _STOPWORDS or len(token) <= 2:
                continue
            if token not in normalized:
                normalized.append(token)
            if len(normalized) >= 3:
                break

        fallback_pool = ["emergency", "assistance", "support", "help"]
        for filler in fallback_pool:
            if len(normalized) >= 3:
                break
            if filler not in normalized:
                normalized.append(filler)

        return normalized[:8]

    def _should_route_to_general(self, query: str, keywords: Iterable[str]) -> bool:
        normalized = query.strip().lower()
        if not normalized:
            return True

        # Check for Urdu greetings
        if is_urdu_greeting(query):
            return True

        # Check for English greetings
        if normalized in _GREETINGS:
            return True

        tokens = [token for token in re.findall(r"[a-z0-9']+", normalized) if token not in _STOPWORDS]
        if not tokens:
            return True

        # Detect emergency indicators to avoid misclassifying critical incidents.
        emergency_tokens = set().union(*_SERVICE_KEYWORDS.values()) | _URGENCY_1_TOKENS | _URGENCY_2_TOKENS
        
        # Add Urdu emergency keywords
        urdu_emergency_tokens = set()
        for service_type in ServiceType:
            if service_type != ServiceType.GENERAL:
                urdu_emergency_tokens.update(get_urdu_service_keywords(service_type.value))
        
        all_emergency_tokens = emergency_tokens | urdu_emergency_tokens
        
        if any(token in all_emergency_tokens for token in tokens):
            return False

        if len(tokens) <= 3:
            return True

        return False

    def classify_service(self, query: str, keywords: Iterable[str]) -> Tuple[ServiceType, str, bool, str]:
        query_lower = query.lower()
        language = detect_urdu_language(query)
        matched_scores = {service: 0 for service in (ServiceType.MEDICAL, ServiceType.POLICE, ServiceType.DISASTER)}

        # Check English keywords
        for keyword in keywords:
            for service, service_words in _SERVICE_KEYWORDS.items():
                if keyword in service_words:
                    matched_scores[service] += 2
        for service, service_words in _SERVICE_KEYWORDS.items():
            matched_scores[service] += sum(
                1 for word in service_words if word in query_lower
            )

        # Check Urdu keywords
        for service_type in (ServiceType.MEDICAL, ServiceType.POLICE, ServiceType.DISASTER):
            urdu_keywords = get_urdu_service_keywords(service_type.value)
            for keyword in keywords:
                if keyword in urdu_keywords:
                    matched_scores[service_type] += 2
            matched_scores[service_type] += sum(
                1 for word in urdu_keywords if word in query_lower
            )

        selected_service = max(matched_scores, key=lambda svc: matched_scores[svc])
        confidence = matched_scores[selected_service]
        follow_up_required = confidence < 2
        
        # Build reason with both English and Urdu keywords
        english_matches = set(_SERVICE_KEYWORDS[selected_service]) & set(keywords)
        urdu_matches = set(get_urdu_service_keywords(selected_service.value)) & set(keywords)
        all_matches = english_matches | urdu_matches
        
        reason = (
            f"Selected {selected_service.value} based on keywords: "
            + ", ".join(sorted(all_matches))
            if confidence > 0
            else "Low confidence classification; requesting follow-up"
        )
        follow_up_reason = (
            "Unable to confidently determine service type, need clarification"
            if follow_up_required
            else None
        )
        return selected_service, reason, follow_up_required, follow_up_reason or ""

    def determine_urgency(self, query: str, keywords: Iterable[str]) -> Tuple[int, str]:
        query_lower = query.lower()
        language = detect_urdu_language(query)
        
        # Check Urdu urgency first
        urdu_urgency, urdu_reason = get_urdu_urgency_level(query, language)
        if urdu_urgency < 3:
            return urdu_urgency, urdu_reason
        
        tokens = {token.lower() for token in keywords}

        # Check English urgency indicators
        for phrase in _URGENCY_1:
            if phrase in query_lower:
                return 1, f"Detected critical phrase: '{phrase}'"
        token_match = tokens & _URGENCY_1_TOKENS
        if token_match:
            token = sorted(token_match)[0]
            return 1, f"Detected critical keyword: '{token}'"

        for phrase in _URGENCY_2:
            if phrase in query_lower:
                if phrase in {"robbery", "assault"} and (" now" in query_lower or "just" in query_lower):
                    return 1, "Detected real-time crime in progress"
                return 2, f"Detected serious phrase: '{phrase}'"
        token_match = tokens & _URGENCY_2_TOKENS
        if token_match:
            if (
                {"robbery", "stole", "broke"} & token_match
                and (" now" in query_lower or "just" in query_lower)
            ):
                return 1, "Detected real-time crime in progress"
            token = sorted(token_match)[0]
            return 2, f"Detected serious keyword: '{token}'"

        return 3, "Defaulted to informational urgency"

    def run(self, request: DispatchRequest, history: Optional[List[dict]] = None) -> FrontAgentOutput:
        if llm_client.is_configured:
            try:
                return self._run_with_llm(request, history)
            except (LLMError, ValidationError, ValueError, KeyError) as exc:
                logger.warning("Front agent LLM failed, falling back to heuristics: %s", exc)
        return self._run_with_rules(request, history)

    def _run_with_llm(self, request: DispatchRequest, history: Optional[List[dict]]) -> FrontAgentOutput:
        heuristic_keywords = self.extract_keywords(request.user_query)
        if not heuristic_keywords:
            heuristic_keywords = [request.user_query.lower()[:30]]

        payload = request.model_dump()
        payload["historical_keywords"] = heuristic_keywords
        payload["service_keywords"] = {
            service.value: sorted(list(keywords)) for service, keywords in _SERVICE_KEYWORDS.items()
        }
        if history:
            payload["conversation_history"] = history

        # Detect language for appropriate prompt
        language = detect_urdu_language(request.user_query)
        
        if language in ['urdu', 'roman_urdu', 'mixed']:
            system_prompt = (
                "You are the Front Dispatcher for emergency services. You can handle Urdu, Roman Urdu, and English. "
                "Receive JSON with userid, user_location, lang, lat, lon, user_query, and helper keyword hints."
                "\nFollow the rules strictly:\n"
                "1) Extract 3-8 concise keywords or short phrases from user_query (can be in Urdu, Roman Urdu, or English)."
                "\n2) Decide urgency in {1,2,3}. 1 = immediate life safety; 2 = serious but not immediately fatal; 3 = informational."
                "\n3) Choose selected_service from ['medical','police','disaster','general']. Use 'general' for greetings, wellness check-ins, or messages without actionable emergency clues."
                "\n4) Provide a short explanation that mentions both urgency and service reasons."
                "\n5) If confidence in the service is low or you select 'general', set follow_up_required true and include follow_up_reason requesting clarification; otherwise set follow_up_required false and follow_up_reason null."
                "\n6) For Urdu greetings like 'salam', 'salaam alaikum', route to 'general' service."
                "\nReturn strict JSON with keys: keywords (array), urgency (int), selected_service (string), explain (string), "
                "follow_up_required (bool), follow_up_reason (string or null)."
                "\nOnly respond with JSON, no extra text."
            )
        else:
            system_prompt = (
                "You are the Front Dispatcher. Receive JSON with userid, user_location, lang, lat, lon, "
                "user_query, and helper keyword hints."
                "\nFollow the rules strictly:\n"
                "1) Extract 3-8 concise keywords or short phrases from user_query."
                "\n2) Decide urgency in {1,2,3}. 1 = immediate life safety; 2 = serious but not immediately fatal; 3 = informational."
                "\n3) Choose selected_service from ['medical','police','disaster','general']. Use 'general' for greetings, wellness check-ins, or messages without actionable emergency clues."
                "\n4) Provide a short explanation that mentions both urgency and service reasons."
                "\n5) If confidence in the service is low or you select 'general', set follow_up_required true and include follow_up_reason requesting clarification; otherwise set follow_up_required false and follow_up_reason null."
                "\nReturn strict JSON with keys: keywords (array), urgency (int), selected_service (string), explain (string), "
                "follow_up_required (bool), follow_up_reason (string or null)."
                "\nOnly respond with JSON, no extra text."
            )

        result = llm_client.structured_completion(
            system_prompt=system_prompt,
            payload=payload,
            temperature=0.1,
            max_tokens=500,
        )

        result.setdefault("follow_up_required", False)
        if result.get("follow_up_reason") in {"", None}:
            result["follow_up_reason"] = None
        if "selected_service" in result and isinstance(result["selected_service"], str):
            result["selected_service"] = result["selected_service"].lower().strip()
            if result["selected_service"] not in {svc.value for svc in ServiceType}:
                result["selected_service"] = ServiceType.GENERAL.value
            if result["selected_service"] == ServiceType.GENERAL.value:
                result["follow_up_required"] = True
                if not result.get("follow_up_reason"):
                    result["follow_up_reason"] = "Could you describe the emergency or how I can assist you today?"
        if "keywords" in result and isinstance(result["keywords"], list):
            result["keywords"] = [str(keyword).strip() for keyword in result["keywords"] if str(keyword).strip()]

        heur_keywords = heuristic_keywords[:]
        heur_keywords = self._ensure_minimum_keywords(heur_keywords, request.user_query)
        route_general = self._should_route_to_general(request.user_query, heuristic_keywords)
        result["keywords"] = self._ensure_minimum_keywords(result.get("keywords", []), request.user_query)

        if route_general:
            result["selected_service"] = ServiceType.GENERAL.value
            result["follow_up_required"] = True
            result["follow_up_reason"] = get_urdu_follow_up_message(language)

        heur_urgency, heur_reason = self.determine_urgency(request.user_query, heur_keywords)
        if heur_urgency < result.get("urgency", 3):
            result["urgency"] = heur_urgency
            explain = result.get("explain") or ""
            if heur_reason not in explain:
                explain = f"{heur_reason}; {explain}".strip("; ")
            result["explain"] = explain

        return FrontAgentOutput.model_validate(result)

    def _run_with_rules(self, request: DispatchRequest, _history: Optional[List[dict]] = None) -> FrontAgentOutput:
        raw_keywords = self.extract_keywords(request.user_query)
        if not raw_keywords:
            raw_keywords = [request.user_query.lower()[:30]]

        route_general = self._should_route_to_general(request.user_query, raw_keywords)
        keywords = self._ensure_minimum_keywords(raw_keywords, request.user_query)

        if route_general:
            language = detect_urdu_language(request.user_query)
            explain = "Identified a general greeting or low-information message; awaiting more details before routing."
            follow_up = get_urdu_follow_up_message(language)
            general_keywords = keywords if keywords else ["greeting", "general", "follow_up_needed"]
            return FrontAgentOutput(
                keywords=general_keywords[:8],
                urgency=3,
                selected_service=ServiceType.GENERAL,
                explain=explain,
                follow_up_required=True,
                follow_up_reason=follow_up,
            )

        urgency, urgency_reason = self.determine_urgency(request.user_query, keywords)
        selected_service, service_reason, follow_up_required, follow_up_reason = self.classify_service(
            request.user_query, keywords
        )

        explain_parts = [urgency_reason, service_reason]
        explain = "; ".join(part for part in explain_parts if part)

        return FrontAgentOutput(
            keywords=keywords[:8],
            urgency=urgency,
            selected_service=selected_service,
            explain=explain,
            follow_up_required=follow_up_required,
            follow_up_reason=follow_up_reason if follow_up_required else None,
        )
