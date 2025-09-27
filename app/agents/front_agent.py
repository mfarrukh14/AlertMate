"""Front dispatcher agent implementing Groq-powered routing with rule fallback."""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Iterable, List, Tuple

from pydantic import ValidationError

from app.models.dispatch import DispatchRequest, FrontAgentOutput, ServiceType
from app.utils.llm_client import LLMError, llm_client

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

logger = logging.getLogger(__name__)


class FrontDispatcherAgent:
    """Front dispatcher using Groq LLM with rule-based fallback."""

    def extract_keywords(self, query: str) -> List[str]:
        query = query.lower()
        raw_tokens = re.findall(r"[a-z0-9']+", query)
        filtered = [token for token in raw_tokens if token not in _STOPWORDS and len(token) > 2]

        counts = Counter(filtered)
        keywords: List[str] = []

        for phrase, pattern in _PHRASE_PATTERNS:
            if pattern.search(query):
                keywords.append(phrase)

        for token, _ in counts.most_common():
            if token not in keywords:
                keywords.append(token)
            if len(keywords) >= 8:
                break

        return keywords[:8]

    def classify_service(self, query: str, keywords: Iterable[str]) -> Tuple[ServiceType, str, bool, str]:
        query_lower = query.lower()
        matched_scores = {service: 0 for service in ServiceType}

        for keyword in keywords:
            for service, service_words in _SERVICE_KEYWORDS.items():
                if keyword in service_words:
                    matched_scores[service] += 2
        for service, service_words in _SERVICE_KEYWORDS.items():
            matched_scores[service] += sum(
                1 for word in service_words if word in query_lower
            )

        selected_service = max(matched_scores, key=lambda svc: matched_scores[svc])
        confidence = matched_scores[selected_service]
        follow_up_required = confidence < 2
        reason = (
            f"Selected {selected_service.value} based on keywords: "
            + ", ".join(sorted(set(_SERVICE_KEYWORDS[selected_service]) & set(keywords)))
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
        tokens = {token.lower() for token in keywords}

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

    def run(self, request: DispatchRequest) -> FrontAgentOutput:
        if llm_client.is_configured:
            try:
                return self._run_with_llm(request)
            except (LLMError, ValidationError, ValueError, KeyError) as exc:
                logger.warning("Front agent LLM failed, falling back to heuristics: %s", exc)
        return self._run_with_rules(request)

    def _run_with_llm(self, request: DispatchRequest) -> FrontAgentOutput:
        payload = request.model_dump()
        payload["historical_keywords"] = self.extract_keywords(request.user_query)
        payload["service_keywords"] = {
            service.value: sorted(list(keywords)) for service, keywords in _SERVICE_KEYWORDS.items()
        }

        system_prompt = (
            "You are the Front Dispatcher. Receive JSON with userid, user_location, lang, lat, lon, "
            "user_query, and helper keyword hints."
            "\nFollow the rules strictly:\n"
            "1) Extract 3-8 concise keywords or short phrases from user_query."
            "\n2) Decide urgency in {1,2,3}. 1 = immediate life safety; 2 = serious but not immediately fatal; 3 = informational."
            "\n3) Choose selected_service from ['medical','police','disaster'] using the heuristics provided."
            "\n4) Provide a short explanation that mentions both urgency and service reasons."
            "\n5) If confidence in the service is low, set follow_up_required true and include follow_up_reason requesting clarification; otherwise set follow_up_required false and follow_up_reason null."
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
        if "keywords" in result and isinstance(result["keywords"], list):
            result["keywords"] = [str(keyword).strip() for keyword in result["keywords"] if str(keyword).strip()]

        return FrontAgentOutput.model_validate(result)

    def _run_with_rules(self, request: DispatchRequest) -> FrontAgentOutput:
        keywords = self.extract_keywords(request.user_query)
        if not keywords:
            keywords = [request.user_query.lower()[:30]]

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
