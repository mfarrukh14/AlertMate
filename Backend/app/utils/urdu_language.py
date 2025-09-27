"""Urdu and Roman Urdu language support utilities."""

from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple

# Roman Urdu to Urdu transliteration mapping
ROMAN_TO_URDU = {
    # Common emergency terms
    "ambulance": "ایمبولینس",
    "ambulens": "ایمبولینس", 
    "hospital": "ہسپتال",
    "haspatal": "ہسپتال",
    "doctor": "ڈاکٹر",
    "daktar": "ڈاکٹر",
    "nurse": "نرس",
    "pain": "درد",
    "dard": "درد",
    "bleeding": "خون بہنا",
    "khoon": "خون",
    "khoon bahna": "خون بہنا",
    "broken": "ٹوٹا ہوا",
    "tuta": "ٹوٹا ہوا",
    "fracture": "فریکچر",
    "fracture": "فریکچر",
    "unconscious": "بے ہوش",
    "be hosh": "بے ہوش",
    "breathing": "سانس",
    "saans": "سانس",
    "emergency": "ایمرجنسی",
    "emergency": "ایمرجنسی",
    
    # Police terms
    "police": "پولیس",
    "police": "پولیس",
    "robbery": "ڈکیتی",
    "dakaiti": "ڈکیتی",
    "theft": "چوری",
    "chori": "چوری",
    "stolen": "چوری ہوا",
    "chori hua": "چوری ہوا",
    "stole": "چوری کی",
    "chori ki": "چوری کی",
    "thief": "چور",
    "chor": "چور",
    "attack": "حملہ",
    "hamla": "حملہ",
    "assault": "حملہ",
    "violence": "تشدد",
    "tashaddud": "تشدد",
    "gun": "بندوق",
    "banduq": "بندوق",
    "knife": "چاقو",
    "chaqoo": "چاقو",
    "shooting": "فائرنگ",
    "firing": "فائرنگ",
    
    # Disaster terms
    "fire": "آگ",
    "aag": "آگ",
    "flood": "سیلاب",
    "sailab": "سیلاب",
    "flooded": "سیلاب",
    "earthquake": "زلزلہ",
    "zalzala": "زلزلہ",
    "landslide": "پہاڑی تودہ",
    "pahari toda": "پہاڑی تودہ",
    "storm": "طوفان",
    "toofan": "طوفان",
    "evacuate": "خالی کرو",
    "khali karo": "خالی کرو",
    "evacuation": "خالی کرنا",
    "khali karna": "خالی کرنا",
    "shelter": "پناہ گاہ",
    "panah gah": "پناہ گاہ",
    "help": "مدد",
    "madad": "مدد",
    "need": "ضرورت",
    "zaroorat": "ضرورت",
    
    # Common words
    "yes": "ہاں",
    "haan": "ہاں",
    "no": "نہیں",
    "nahin": "نہیں",
    "please": "برائے کرم",
    "barae karam": "برائے کرم",
    "urgent": "فوری",
    "fori": "فوری",
    "immediate": "فوری",
    "quickly": "جلدی",
    "jaldi": "جلدی",
    "fast": "تیزی سے",
    "tezi se": "تیزی سے",
    
    # Greetings
    "salam": "سلام",
    "salaam": "سلام",
    "salam alaikum": "سلام علیکم",
    "salaam alaikum": "سلام علیکم",
    "assalamualaikum": "السلام علیکم",
    "assalamu alaikum": "السلام علیکم",
    "adaab": "آداب",
    "khuda hafiz": "خدا حافظ",
    "allah hafiz": "اللہ حافظ",
}

# Urdu emergency keywords by service type
URDU_SERVICE_KEYWORDS = {
    "medical": {
        "ایمبولینس", "ہسپتال", "ڈاکٹر", "نرس", "درد", "خون", "خون بہنا",
        "ٹوٹا ہوا", "فریکچر", "بے ہوش", "سانس", "ایمرجنسی", "زخمی",
        "مریض", "علاج", "دوا", "انجکشن", "سرجری", "ایکس رے"
    },
    "police": {
        "پولیس", "ڈکیتی", "چوری", "چور", "حملہ", "تشدد", "بندوق",
        "چاقو", "فائرنگ", "جرم", "سزا", "قانون", "محفوظ", "خطرہ"
    },
    "disaster": {
        "آگ", "سیلاب", "زلزلہ", "پہاڑی تودہ", "طوفان", "خالی کرو",
        "پناہ گاہ", "مدد", "ضرورت", "خطرہ", "بچاؤ", "انتباہ"
    }
}

# Roman Urdu emergency keywords by service type
ROMAN_URDU_SERVICE_KEYWORDS = {
    "medical": {
        "ambulance", "ambulens", "hospital", "haspatal", "doctor", "daktar",
        "nurse", "pain", "dard", "bleeding", "khoon", "khoon bahna",
        "broken", "tuta", "fracture", "unconscious", "be hosh", "breathing",
        "saans", "emergency", "injured", "mareez", "ilaj", "dawa"
    },
    "police": {
        "police", "robbery", "dakaiti", "theft", "chori", "stolen", "chori hua",
        "thief", "chor", "attack", "hamla", "assault", "violence", "tashaddud",
        "gun", "banduq", "knife", "chaqoo", "shooting", "firing", "crime"
    },
    "disaster": {
        "fire", "aag", "flood", "sailab", "flooded", "earthquake", "zalzala",
        "landslide", "pahari toda", "storm", "toofan", "evacuate", "khali karo",
        "shelter", "panah gah", "help", "madad", "need", "zaroorat", "danger"
    }
}

# Urdu urgency indicators
URDU_URGENCY_1 = {
    "بے ہوش", "سانس نہیں", "قلب کی دھڑکن رک گئی", "شدید خون بہنا",
    "بندوق", "فائرنگ", "آگ", "دھماکہ", "پھنس گیا", "فوری خطرہ"
}

URDU_URGENCY_2 = {
    "فریکچر", "ٹوٹا ہوا", "ٹوٹ", "شدید درد", "ڈکیتی", "حملہ", "خطرہ",
    "سیلاب", "گر گیا", "زلزلہ", "پہاڑی تودہ"
}

# Roman Urdu urgency indicators
ROMAN_URDU_URGENCY_1 = {
    "be hosh", "saans nahin", "dil ki dhadkan ruk gayi", "shadeed khoon",
    "banduq", "firing", "aag", "dhamaka", "phans gaya", "fori khatra"
}

ROMAN_URDU_URGENCY_2 = {
    "fracture", "tuta", "shadeed dard", "dakaiti", "hamla", "khatra",
    "sailab", "gir gaya", "zalzala", "pahari toda"
}

# Urdu greetings
URDU_GREETINGS = {
    "سلام", "سلام علیکم", "السلام علیکم", "آداب", "خدا حافظ", "اللہ حافظ",
    "صبح بخیر", "شام بخیر", "رات بخیر"
}

# Roman Urdu greetings
ROMAN_URDU_GREETINGS = {
    "salam", "salaam", "salam alaikum", "salaam alaikum", "assalamualaikum",
    "assalamu alaikum", "adaab", "khuda hafiz", "allah hafiz", "subah bakhair",
    "shaam bakhair", "raat bakhair"
}

def detect_urdu_language(text: str) -> str:
    """
    Detect if text contains Urdu, Roman Urdu, or English.
    Returns: 'urdu', 'roman_urdu', 'english', or 'mixed'
    """
    text = text.strip()
    if not text:
        return 'english'
    
    # Check for Urdu script (Arabic/Persian characters)
    urdu_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
    has_urdu = bool(urdu_pattern.search(text))
    
    # Check for Roman Urdu patterns (common Roman Urdu words)
    # But exclude very common English words that might be in the mapping
    common_english_words = {
        'help', 'need', 'please', 'yes', 'no', 'i', 'you', 'we', 'they', 'the', 'a', 'an', 'and', 'or', 'but',
        'call', 'ambulance'  # Common English emergency terms
    }
    roman_urdu_words = 0
    words = text.lower().split()
    
    for word in words:
        if word in ROMAN_TO_URDU and word not in common_english_words:
            roman_urdu_words += 1
    
    # Determine language
    if has_urdu and roman_urdu_words == 0:
        return 'urdu'
    elif not has_urdu and roman_urdu_words > 0:
        return 'roman_urdu'
    elif has_urdu and roman_urdu_words > 0:
        return 'mixed'
    else:
        # Check if it's likely English vs other languages
        # If no Urdu script and no Roman Urdu words, assume English
        return 'english'

def transliterate_roman_to_urdu(text: str) -> str:
    """Convert Roman Urdu text to Urdu script."""
    if not text:
        return text
    
    words = text.split()
    urdu_words = []
    
    for word in words:
        word_lower = word.lower()
        if word_lower in ROMAN_TO_URDU:
            urdu_words.append(ROMAN_TO_URDU[word_lower])
        else:
            urdu_words.append(word)  # Keep original if not found
    
    return ' '.join(urdu_words)

def extract_urdu_keywords(text: str, language: str = None) -> List[str]:
    """Extract emergency-related keywords from Urdu/Roman Urdu text."""
    if not language:
        language = detect_urdu_language(text)
    
    keywords = []
    text_lower = text.lower()
    
    if language in ['urdu', 'mixed']:
        # Check Urdu keywords
        for service, words in URDU_SERVICE_KEYWORDS.items():
            for word in words:
                if word in text:
                    keywords.append(word)
    
    if language in ['roman_urdu', 'mixed', 'english']:
        # Check Roman Urdu keywords
        for service, words in ROMAN_URDU_SERVICE_KEYWORDS.items():
            for word in words:
                if word in text_lower:
                    keywords.append(word)
    
    # Check urgency indicators
    if language in ['urdu', 'mixed']:
        for word in URDU_URGENCY_1 | URDU_URGENCY_2:
            if word in text:
                keywords.append(word)
    
    if language in ['roman_urdu', 'mixed', 'english']:
        for word in ROMAN_URDU_URGENCY_1 | ROMAN_URDU_URGENCY_2:
            if word in text_lower:
                keywords.append(word)
    
    return list(set(keywords))  # Remove duplicates

def is_urdu_greeting(text: str) -> bool:
    """Check if text is an Urdu greeting."""
    text_lower = text.lower().strip()
    
    # Check Roman Urdu greetings
    if text_lower in ROMAN_URDU_GREETINGS:
        return True
    
    # Check Urdu greetings
    if text.strip() in URDU_GREETINGS:
        return True
    
    # Check if it's a simple greeting
    simple_greetings = {"hi", "hello", "hey", "salam", "salaam"}
    return text_lower in simple_greetings

def get_urdu_service_keywords(service_type: str) -> Set[str]:
    """Get Urdu and Roman Urdu keywords for a specific service type."""
    urdu_keywords = URDU_SERVICE_KEYWORDS.get(service_type, set())
    roman_keywords = ROMAN_URDU_SERVICE_KEYWORDS.get(service_type, set())
    return urdu_keywords | roman_keywords

def get_urdu_urgency_level(text: str, language: str = None) -> Tuple[int, str]:
    """Determine urgency level from Urdu/Roman Urdu text."""
    if not language:
        language = detect_urdu_language(text)
    
    text_lower = text.lower()
    
    # Check for highest urgency (level 1)
    urgency_1_indicators = []
    if language in ['urdu', 'mixed']:
        for indicator in URDU_URGENCY_1:
            if indicator in text:
                urgency_1_indicators.append(indicator)
    
    if language in ['roman_urdu', 'mixed', 'english']:
        for indicator in ROMAN_URDU_URGENCY_1:
            if indicator in text_lower:
                urgency_1_indicators.append(indicator)
    
    if urgency_1_indicators:
        return 1, f"Detected critical Urdu indicator: '{urgency_1_indicators[0]}'"
    
    # Check for medium urgency (level 2)
    urgency_2_indicators = []
    if language in ['urdu', 'mixed']:
        # First check for exact matches
        for indicator in URDU_URGENCY_2:
            if indicator in text:
                urgency_2_indicators.append(indicator)
        
        # If no exact matches, check for partial matches
        if not urgency_2_indicators:
            for indicator in URDU_URGENCY_2:
                for word in indicator.split():
                    if word in text and len(word) > 2:  # Avoid very short word matches
                        urgency_2_indicators.append(word)
    
    if language in ['roman_urdu', 'mixed', 'english']:
        for indicator in ROMAN_URDU_URGENCY_2:
            if indicator in text_lower:
                urgency_2_indicators.append(indicator)
        
        # Also check for partial matches in Roman Urdu keywords
        for indicator in ROMAN_URDU_URGENCY_2:
            for word in indicator.split():
                if word in text_lower and len(word) > 2:  # Avoid very short word matches
                    urgency_2_indicators.append(word)
    
    if urgency_2_indicators:
        return 2, f"Detected serious Urdu indicator: '{urgency_2_indicators[0]}'"
    
    return 3, "Defaulted to informational urgency"

def get_urdu_follow_up_message(language: str = None) -> str:
    """Get appropriate follow-up message in Urdu/Roman Urdu."""
    if language == 'urdu':
        return "برائے کرم اپنا ایمرجنسی کی تفصیل بتائیں"
    elif language == 'roman_urdu':
        return "Barae karam apna emergency ki tafseel batayen"
    else:
        return "Could you describe the emergency or how I can assist you today?"
