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
        "choking",
        "choke",
        "emergency",
        "urgent",
        "critical",
        "heart",
        "stroke",
        "seizure",
        "seizures",
        "fits",
        "fit",
        "convulsions",
        "convulsing",
        "epilepsy",
        "epileptic",
        "allergic",
        "reaction",
        "poison",
        "overdose",
        "drowning",
        "burn",
        "shock",
        "medical",
        "sick",
        "illness",
        "fever",
        "high temperature",
        "accident",
        "crash",
        "collision",
        "bike accident",
        "car accident",
        "road accident",
        "motorcycle accident",
        "vehicle accident",
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
    "choking",
    "can't breathe",
    "drowning",
    "severe allergic reaction",
    "fits",
    "seizure",
    "seizures",
    "convulsions",
    "having fits",
    "epileptic seizure",
    "medical emergency",
    "accident",
    "bike accident",
    "car accident",
    "road accident",
    "motorcycle accident",
    "vehicle accident",
    "crash",
    "collision",
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
    "choking",
    "choke",
    "emergency",
    "urgent",
    "critical",
    "fits",
    "fit",
    "seizure",
    "seizures",
    "convulsions",
    "epilepsy",
    "medical",
    "accident",
    "crash",
    "collision",
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
        
        # For Urdu text, also check the keywords directly since tokens might be empty
        language = detect_urdu_language(query)
        if language in ['urdu', 'mixed'] and not tokens:
            # Check if any of the extracted keywords indicate emergency
            urdu_emergency_tokens = set()
            for service_type in ServiceType:
                if service_type != ServiceType.GENERAL:
                    urdu_emergency_tokens.update(get_urdu_service_keywords(service_type.value))
            
            if any(keyword in urdu_emergency_tokens for keyword in keywords):
                return False
        
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
        
        # Check individual tokens
        if any(token in all_emergency_tokens for token in tokens):
            return False
        
        # Also check for emergency phrases in the query
        emergency_phrases = [
            "having fits", "having seizures", "having convulsions", 
            "cardiac arrest", "not breathing", "heavy bleeding",
            "medical emergency", "emergency", "urgent", "critical"
        ]
        if any(phrase in normalized for phrase in emergency_phrases):
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
        # Always try LLM first, even if not configured - let it fail and then fall back
        try:
            return self._run_with_llm(request, history)
        except (LLMError, ValidationError, ValueError, KeyError) as exc:
            logger.warning("Front agent LLM failed, falling back to heuristics: %s", exc)
        return self._run_with_rules(request, history)

    def _run_with_llm(self, request: DispatchRequest, history: Optional[List[dict]]) -> FrontAgentOutput:
        # Check if this is a slow connection
        from app.utils.network_utils import detect_network_quality
        network_quality = detect_network_quality(request.network_quality, request.connection_type)
        is_slow_connection = network_quality.value in ["slow", "unknown"]
        
        # Get heuristic keywords - use more heavily for slow connections
        heuristic_keywords = self.extract_keywords(request.user_query)
        if not heuristic_keywords:
            heuristic_keywords = []

        payload = request.model_dump()
        
        if is_slow_connection:
            # For slow connections, provide more heuristic guidance
            payload["heuristic_keywords"] = heuristic_keywords
            payload["network_condition"] = "slow_connection"
        else:
            # For good connections, let Gemini do its own keyword extraction
            if heuristic_keywords:
                payload["optional_keyword_hints"] = heuristic_keywords[:3]  # Only provide top 3 as hints
        
        payload["service_keywords"] = {
            service.value: sorted(list(keywords)) for service, keywords in _SERVICE_KEYWORDS.items()
        }

        # Detect language for appropriate prompt
        language = detect_urdu_language(request.user_query)
        
        if language in ['urdu', 'roman_urdu', 'mixed']:
            if is_slow_connection:
                system_prompt = (
                    "You are the Front Dispatcher for emergency services. You can handle Urdu, Roman Urdu, and English. "
                    "SLOW CONNECTION DETECTED - Use the provided heuristic keywords as guidance for faster processing."
                    "\nIMPORTANT: Use the conversation context to understand if this is a follow-up response to a previous question. "
                    "If the user_query is a short response (like a number, yes/no, brief answer) and this appears to be a follow-up to a previous question, "
                    "route to the same service as the previous interaction and set urgency based on the original emergency context."
                    "\nFollow the rules strictly:\n"
                    "1) Use the heuristic_keywords provided as a starting point, but refine them based on the user_query. Extract 3-8 concise keywords (can be in Urdu, Roman Urdu, or English)."
                    "\n2) Decide urgency in {1,2,3}. 1 = immediate life safety (choking, seizures, fits, unconscious, not breathing, cardiac arrest, heavy bleeding, drowning, severe allergic reaction, heart attack, stroke, drug overdose, poisoning, severe burns, trauma, head injury, chest pain, difficulty breathing, severe pain, emergency, urgent, critical, life-threatening, asthma attack, diabetic emergency, pregnancy complications, mental health crisis, suicidal thoughts, panic attack, anxiety attack); 2 = serious but not immediately fatal (broken bones, moderate injuries, theft, assault, moderate bleeding, sprains, cuts, bruises, non-emergency medical issues); 3 = informational (general questions, greetings, non-urgent inquiries)."
                    "\n3) Choose selected_service from ['medical','police','disaster','general']. MEDICAL for: choking, seizures, fits, convulsions, unconscious, not breathing, cardiac arrest, heavy bleeding, drowning, severe allergic reaction, heart attack, stroke, fever, illness, medical emergency, ambulance needed, drug overdose, poisoning, severe burns, trauma, head injury, chest pain, difficulty breathing, severe pain, asthma attack, diabetic emergency, pregnancy complications, mental health crisis, suicidal thoughts, panic attack, anxiety attack, any medical condition requiring immediate attention. POLICE for: theft, robbery, assault, attack, violence, crime, stolen items, suspicious activity, domestic violence, harassment, threats, burglary, vandalism, hit and run, traffic accident, missing person, child abduction, sexual assault, fraud, cybercrime, drug dealing, public disturbance, noise complaint, trespassing. DISASTER for: fire, flood, earthquake, storm, evacuation, natural disasters, building collapse, gas leak, chemical spill, power outage, water main break, road closure, landslide, tornado, hurricane, tsunami, volcanic activity, nuclear emergency, terrorist attack, bomb threat, active shooter. Use 'general' ONLY for greetings, wellness check-ins, or messages without actionable emergency clues."
                    "\n4) Provide a short explanation that mentions both urgency and service reasons."
                    "\n5) If confidence in the service is low or you select 'general', set follow_up_required true and include follow_up_reason requesting clarification; otherwise set follow_up_required false and follow_up_reason null."
                    "\n6) For Urdu greetings like 'salam', 'salaam alaikum', route to 'general' service."
                    "\nReturn strict JSON with keys: keywords (array), urgency (int), selected_service (string), explain (string), "
                    "follow_up_required (bool), follow_up_reason (string or null)."
                    "\nOnly respond with JSON, no extra text."
                )
            else:
                system_prompt = (
                    "You are the Front Dispatcher for emergency services. You can handle Urdu, Roman Urdu, and English. "
                    "Receive JSON with userid, user_location, lang, lat, lon, user_query, and optional helper keyword hints."
                    "\nIMPORTANT: Use the conversation context to understand if this is a follow-up response to a previous question. "
                    "If the user_query is a short response (like a number, yes/no, brief answer) and this appears to be a follow-up to a previous question, "
                    "route to the same service as the previous interaction and set urgency based on the original emergency context."
                    "\nFollow the rules strictly:\n"
                    "1) Extract 3-8 concise keywords or short phrases from user_query (can be in Urdu, Roman Urdu, or English). Focus on the most important emergency-related terms. Ignore common words like 'my', 'the', 'is', etc."
                    "\n2) Decide urgency in {1,2,3}. 1 = immediate life safety (choking, seizures, fits, unconscious, not breathing, cardiac arrest, heavy bleeding, drowning, severe allergic reaction, heart attack, stroke, drug overdose, poisoning, severe burns, trauma, head injury, chest pain, difficulty breathing, severe pain, emergency, urgent, critical, life-threatening, asthma attack, diabetic emergency, pregnancy complications, mental health crisis, suicidal thoughts, panic attack, anxiety attack); 2 = serious but not immediately fatal (broken bones, moderate injuries, theft, assault, moderate bleeding, sprains, cuts, bruises, non-emergency medical issues); 3 = informational (general questions, greetings, non-urgent inquiries)."
                    "\n3) Choose selected_service from ['medical','police','disaster','general']. MEDICAL for: choking, seizures, fits, convulsions, unconscious, not breathing, cardiac arrest, heavy bleeding, drowning, severe allergic reaction, heart attack, stroke, fever, illness, medical emergency, ambulance needed, drug overdose, poisoning, severe burns, trauma, head injury, chest pain, difficulty breathing, severe pain, asthma attack, diabetic emergency, pregnancy complications, mental health crisis, suicidal thoughts, panic attack, anxiety attack, any medical condition requiring immediate attention. POLICE for: theft, robbery, assault, attack, violence, crime, stolen items, suspicious activity, domestic violence, harassment, threats, burglary, vandalism, hit and run, traffic accident, missing person, child abduction, sexual assault, fraud, cybercrime, drug dealing, public disturbance, noise complaint, trespassing. DISASTER for: fire, flood, earthquake, storm, evacuation, natural disasters, building collapse, gas leak, chemical spill, power outage, water main break, road closure, landslide, tornado, hurricane, tsunami, volcanic activity, nuclear emergency, terrorist attack, bomb threat, active shooter. Use 'general' ONLY for greetings, wellness check-ins, or messages without actionable emergency clues."
                    "\n4) Provide a short explanation that mentions both urgency and service reasons."
                    "\n5) If confidence in the service is low or you select 'general', set follow_up_required true and include follow_up_reason requesting clarification; otherwise set follow_up_required false and follow_up_reason null."
                    "\n6) For Urdu greetings like 'salam', 'salaam alaikum', route to 'general' service."
                    "\nReturn strict JSON with keys: keywords (array), urgency (int), selected_service (string), explain (string), "
                    "follow_up_required (bool), follow_up_reason (string or null)."
                    "\nOnly respond with JSON, no extra text."
                )
        else:
            if is_slow_connection:
                system_prompt = (
                    "You are the Front Dispatcher for emergency services. "
                    "SLOW CONNECTION DETECTED - Use the provided heuristic keywords as guidance for faster processing."
                    "\nIMPORTANT: Use the conversation context to understand if this is a follow-up response to a previous question. "
                    "If the user_query is a short response (like a number, yes/no, brief answer) and this appears to be a follow-up to a previous question, "
                    "route to the same service as the previous interaction and set urgency based on the original emergency context."
                    "\nFollow the rules strictly:\n"
                    "1) Use the heuristic_keywords provided as a starting point, but refine them based on the user_query. Extract 3-8 concise keywords."
                    "\n2) Decide urgency in {1,2,3}. 1 = immediate life safety; 2 = serious but not immediately fatal; 3 = informational."
                    "\n3) Choose selected_service from ['medical','police','disaster','general']. Use 'general' for greetings, wellness check-ins, or messages without actionable emergency clues."
                    "\n4) Provide a short explanation that mentions both urgency and service reasons."
                    "\n5) If confidence in the service is low or you select 'general', set follow_up_required true and include follow_up_reason requesting clarification; otherwise set follow_up_required false and follow_up_reason null."
                    "\nReturn strict JSON with keys: keywords (array), urgency (int), selected_service (string), explain (string), "
                    "follow_up_required (bool), follow_up_reason (string or null)."
                    "\nOnly respond with JSON, no extra text."
                )
            else:
                system_prompt = (
                    "You are the Front Dispatcher for emergency services. Receive JSON with userid, user_location, lang, lat, lon, "
                    "user_query, optional helper keyword hints, and conversation_history."
                    "\nIMPORTANT: Use the conversation context to understand if this is a follow-up response to a previous question. "
                    "If the user_query is a short response (like a number, yes/no, brief answer) and this appears to be a follow-up to a previous question, "
                    "route to the same service as the previous interaction and set urgency based on the original emergency context."
                    "\nFollow the rules strictly:\n"
                    "1) Extract 3-8 concise keywords or short phrases from user_query. Focus on the most important emergency-related terms. Ignore common words like 'my', 'the', 'is', etc."
                    "\n2) Decide urgency in {1,2,3}. 1 = immediate life safety (choking, seizures, fits, unconscious, not breathing, cardiac arrest, heavy bleeding, drowning, severe allergic reaction, heart attack, stroke, drug overdose, poisoning, severe burns, trauma, head injury, chest pain, difficulty breathing, severe pain, emergency, urgent, critical, life-threatening, asthma attack, diabetic emergency, pregnancy complications, mental health crisis, suicidal thoughts, panic attack, anxiety attack, ACCIDENTS, crashes, collisions, bike accidents, car accidents, road accidents, motorcycle accidents, vehicle accidents, any accident with potential for injury); 2 = serious but not immediately fatal (broken bones, moderate injuries, theft, assault, moderate bleeding, sprains, cuts, bruises, non-emergency medical issues); 3 = informational (general questions, greetings, non-urgent inquiries)."
                    "\n3) Choose selected_service from ['medical','police','disaster','general']. MEDICAL for: choking, seizures, fits, convulsions, unconscious, not breathing, cardiac arrest, heavy bleeding, drowning, severe allergic reaction, heart attack, stroke, fever, illness, medical emergency, ambulance needed, drug overdose, poisoning, severe burns, trauma, head injury, chest pain, difficulty breathing, severe pain, asthma attack, diabetic emergency, pregnancy complications, mental health crisis, suicidal thoughts, panic attack, anxiety attack, ACCIDENTS, crashes, collisions, bike accidents, car accidents, road accidents, motorcycle accidents, vehicle accidents, any medical condition requiring immediate attention. POLICE for: theft, robbery, assault, attack, violence, crime, stolen items, suspicious activity, domestic violence, harassment, threats, burglary, vandalism, hit and run, traffic accident, missing person, child abduction, sexual assault, fraud, cybercrime, drug dealing, public disturbance, noise complaint, trespassing. DISASTER for: fire, flood, earthquake, storm, evacuation, natural disasters, building collapse, gas leak, chemical spill, power outage, water main break, road closure, landslide, tornado, hurricane, tsunami, volcanic activity, nuclear emergency, terrorist attack, bomb threat, active shooter. Use 'general' ONLY for greetings, wellness check-ins, or messages without actionable emergency clues."
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
            max_tokens=800,
            user_id=request.userid,
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

        # Handle keyword extraction based on connection quality
        gemini_keywords = result.get("keywords", [])
        
        if is_slow_connection:
            # For slow connections, use heuristic keywords more heavily
            if len(gemini_keywords) < 3 or not gemini_keywords:
                # Fall back to heuristic keywords
                result["keywords"] = self._ensure_minimum_keywords(heuristic_keywords, request.user_query)
            else:
                # Use Gemini's keywords but validate with heuristics
                combined_keywords = list(set(gemini_keywords + heuristic_keywords[:3]))
                result["keywords"] = combined_keywords[:8]
            
            # More aggressive heuristic validation for slow connections
            route_general = self._should_route_to_general(request.user_query, result["keywords"])
            if route_general:
                result["selected_service"] = ServiceType.GENERAL.value
                result["follow_up_required"] = True
                result["follow_up_reason"] = get_urdu_follow_up_message(language)
            
            # Use heuristic urgency for slow connections if it's more urgent
            heur_urgency, heur_reason = self.determine_urgency(request.user_query, result["keywords"])
            if heur_urgency < result.get("urgency", 3):
                result["urgency"] = heur_urgency
                explain = result.get("explain") or ""
                if heur_reason not in explain:
                    explain = f"{heur_reason}; {explain}".strip("; ")
                result["explain"] = explain
        else:
            # For good connections, TRUST GEMINI completely - no heuristic overrides
            if len(gemini_keywords) < 3:
                # Only fall back to heuristics if Gemini didn't extract enough keywords
                result["keywords"] = self._ensure_minimum_keywords(gemini_keywords, request.user_query)
            else:
                # Trust Gemini's keywords completely
                result["keywords"] = [kw for kw in gemini_keywords if kw and len(kw.strip()) > 0][:8]
            
            # NO heuristic validation for good connections - trust Gemini's intelligence
            # Only ensure we have valid service type
            if result.get("selected_service") not in {svc.value for svc in ServiceType}:
                result["selected_service"] = ServiceType.GENERAL.value

        return FrontAgentOutput.model_validate(result)

    def _run_with_rules(self, request: DispatchRequest, _history: Optional[List[dict]] = None) -> FrontAgentOutput:
        raw_keywords = self.extract_keywords(request.user_query)
        if not raw_keywords:
            raw_keywords = [request.user_query.lower()[:30]]

        # Check if this is a follow-up response
        query_lower = request.user_query.lower()
        is_followup = (
            # Short numeric responses
            (len(request.user_query.strip()) <= 10 and any(char.isdigit() for char in request.user_query)) or
            # Medical follow-up responses (but not initial accident reports)
            any(term in query_lower for term in ["yes", "no", "bleeding", "conscious", "breathing", "unconscious", "pain", "hurt", "injured", "wounded", "cut", "bruise", "swelling", "nausea", "dizzy", "faint", "weak", "tired", "sick", "ill", "fever", "temperature", "headache", "chest pain", "back pain", "leg pain", "arm pain", "neck pain", "stomach pain", "abdominal pain", "severe", "mild", "moderate", "bad", "worse", "better", "same", "okay", "fine", "good", "alright", "not good", "terrible", "awful", "critical", "urgent", "emergency", "help", "assistance", "ambulance", "hospital", "doctor", "medic", "nurse", "paramedic", "first aid", "bandage", "pressure", "stop bleeding", "control bleeding", "apply pressure", "elevate", "ice", "heat", "rest", "lie down", "sit up", "stand", "walk", "move", "can't move", "stuck", "trapped", "pinned", "crushed", "hit", "struck", "fell", "fallen", "dropped", "slipped", "tripped", "collision", "impact", "crash", "incident", "injury", "wound", "laceration", "abrasion", "contusion", "fracture", "broken", "sprain", "strain", "dislocation", "concussion", "head injury", "chest injury", "back injury", "neck injury", "spine injury", "internal injury", "external injury", "visible injury", "hidden injury", "serious injury", "minor injury", "major injury", "life-threatening", "life threatening", "fatal", "deadly", "dangerous", "safe", "stable", "unstable", "critical condition", "serious condition", "stable condition", "improving", "worsening", "getting worse", "getting better", "no change", "same as before", "different", "new", "additional", "more", "less", "increased", "decreased", "stopped", "started", "began", "continued", "persistent", "constant", "intermittent", "occasional", "frequent", "rare", "never", "always", "sometimes", "often", "seldom", "recently", "just now", "a moment ago", "few minutes ago", "hour ago", "today", "yesterday", "this morning", "this afternoon", "this evening", "tonight", "last night", "this week", "this month", "this year", "recent", "recently", "lately", "now", "currently", "presently", "at present", "at the moment", "right now", "immediately", "urgently", "quickly", "fast", "slowly", "gradually", "suddenly", "instantly", "immediately", "right away", "asap", "as soon as possible", "quick", "rapid", "swift", "prompt", "immediate", "instant", "direct", "straight", "directly", "immediately", "right now", "now", "currently", "presently", "at present", "at the moment", "right now", "immediately", "urgently", "quickly", "fast", "slowly", "gradually", "suddenly", "instantly", "immediately", "right away", "asap", "as soon as possible", "quick", "rapid", "swift", "prompt", "immediate", "instant", "direct", "straight", "directly"]) and not any(term in query_lower for term in ["accident", "crash", "collision", "bike accident", "car accident", "road accident", "motorcycle accident", "vehicle accident"])
        )
        
        if is_followup:
            # For follow-up responses, try to determine the service based on context
            # This is a simplified approach - in a real system, you'd use conversation history
            
            # Check for medical follow-up responses
            if any(term in query_lower for term in ["bleeding", "conscious", "breathing", "unconscious", "pain", "hurt", "injured", "wounded", "cut", "bruise", "swelling", "nausea", "dizzy", "faint", "weak", "tired", "sick", "ill", "fever", "temperature", "headache", "chest pain", "back pain", "leg pain", "arm pain", "neck pain", "stomach pain", "abdominal pain", "severe", "mild", "moderate", "bad", "worse", "better", "same", "okay", "fine", "good", "alright", "not good", "terrible", "awful", "critical", "urgent", "emergency", "help", "assistance", "ambulance", "hospital", "doctor", "medic", "nurse", "paramedic", "first aid", "bandage", "pressure", "stop bleeding", "control bleeding", "apply pressure", "elevate", "ice", "heat", "rest", "lie down", "sit up", "stand", "walk", "move", "can't move", "stuck", "trapped", "pinned", "crushed", "hit", "struck", "fell", "fallen", "dropped", "slipped", "tripped", "collision", "impact", "crash", "accident", "incident", "injury", "wound", "laceration", "abrasion", "contusion", "fracture", "broken", "sprain", "strain", "dislocation", "concussion", "head injury", "chest injury", "back injury", "neck injury", "spine injury", "internal injury", "external injury", "visible injury", "hidden injury", "serious injury", "minor injury", "major injury", "life-threatening", "life threatening", "fatal", "deadly", "dangerous", "safe", "stable", "unstable", "critical condition", "serious condition", "stable condition", "improving", "worsening", "getting worse", "getting better", "no change", "same as before", "different", "new", "additional", "more", "less", "increased", "decreased", "stopped", "started", "began", "continued", "persistent", "constant", "intermittent", "occasional", "frequent", "rare", "never", "always", "sometimes", "often", "seldom", "recently", "just now", "a moment ago", "few minutes ago", "hour ago", "today", "yesterday", "this morning", "this afternoon", "this evening", "tonight", "last night", "this week", "this month", "this year", "recent", "recently", "lately", "now", "currently", "presently", "at present", "at the moment", "right now", "immediately", "urgently", "quickly", "fast", "slowly", "gradually", "suddenly", "instantly", "immediately", "right away", "asap", "as soon as possible", "quick", "rapid", "swift", "prompt", "immediate", "instant", "direct", "straight", "directly"]):
                # This looks like a medical follow-up response
                keywords = ["medical", "follow_up", "injury", "bleeding", "emergency", "urgent", "critical"]
                return FrontAgentOutput(
                    keywords=keywords,
                    urgency=1,
                    selected_service=ServiceType.MEDICAL,
                    explain="Follow-up response to medical emergency, processing injury details.",
                    follow_up_required=False,
                    follow_up_reason=None,
                )
            
            # Check for disaster-related follow-up (evacuation count)
            elif any(char.isdigit() for char in query_lower) and len(query_lower) <= 10:
                # This looks like an evacuation count response
                keywords = ["evacuation", "count", "people", "assistance", "disaster", "follow_up"]
                return FrontAgentOutput(
                    keywords=keywords,
                    urgency=1,
                    selected_service=ServiceType.DISASTER,
                    explain="Follow-up response to disaster emergency, processing evacuation count.",
                    follow_up_required=False,
                    follow_up_reason=None,
                )

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
