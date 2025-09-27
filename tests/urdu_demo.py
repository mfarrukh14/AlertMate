#!/usr/bin/env python3
"""Demonstration of Urdu and Roman Urdu functionality in AlertMate."""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.urdu_language import (
    detect_urdu_language,
    extract_urdu_keywords,
    is_urdu_greeting,
    get_urdu_urgency_level,
    transliterate_roman_to_urdu,
    get_urdu_follow_up_message,
)

def demonstrate_urdu_features():
    """Demonstrate various Urdu language features."""
    
    print("🚨 AlertMate Urdu & Roman Urdu Demo")
    print("=" * 60)
    
    # Test cases for different scenarios
    test_cases = [
        {
            "category": "Urdu Medical Emergency",
            "text": "ایمبولینس چاہیے، مریض بے ہوش ہے اور سانس نہیں آ رہی",
            "expected_lang": "urdu",
            "expected_urgency": 1,
            "expected_service": "medical"
        },
        {
            "category": "Roman Urdu Police Emergency", 
            "text": "dakaiti ho rahi hai, police bulao jaldi",
            "expected_lang": "roman_urdu",
            "expected_urgency": 2,
            "expected_service": "police"
        },
        {
            "category": "Mixed Language Disaster",
            "text": "Fire لگ گئی ہے، آگ emergency hai",
            "expected_lang": "mixed",
            "expected_urgency": 1,
            "expected_service": "disaster"
        },
        {
            "category": "Urdu Greeting",
            "text": "سلام علیکم",
            "expected_lang": "urdu",
            "expected_urgency": 3,
            "expected_service": "general"
        },
        {
            "category": "Roman Urdu Greeting",
            "text": "salaam alaikum",
            "expected_lang": "roman_urdu", 
            "expected_urgency": 3,
            "expected_service": "general"
        },
        {
            "category": "English Emergency",
            "text": "I need an ambulance, patient is unconscious",
            "expected_lang": "english",
            "expected_urgency": 2,
            "expected_service": "medical"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {case['category']}")
        print("-" * 50)
        print(f"Input: {case['text']}")
        
        # Language detection
        detected_lang = detect_urdu_language(case['text'])
        print(f"🌐 Language Detected: {detected_lang} (Expected: {case['expected_lang']})")
        
        # Greeting detection
        is_greeting = is_urdu_greeting(case['text'])
        print(f"👋 Is Greeting: {is_greeting}")
        
        # Keyword extraction
        keywords = extract_urdu_keywords(case['text'])
        print(f"🔑 Keywords Extracted: {keywords[:5]}...")  # Show first 5 keywords
        
        # Urgency detection
        urgency, reason = get_urdu_urgency_level(case['text'])
        print(f"⚡ Urgency Level: {urgency} (Expected: {case['expected_urgency']})")
        print(f"📋 Reason: {reason}")
        
        # Transliteration (if Roman Urdu)
        if detected_lang in ['roman_urdu', 'mixed']:
            transliterated = transliterate_roman_to_urdu(case['text'])
            print(f"🔄 Transliterated: {transliterated}")
        
        # Follow-up message
        follow_up = get_urdu_follow_up_message(detected_lang)
        print(f"💬 Follow-up Message: {follow_up}")
        
        # Validation
        lang_correct = detected_lang == case['expected_lang']
        urgency_correct = urgency == case['expected_urgency']
        
        if lang_correct and urgency_correct:
            print("✅ Test PASSED")
        else:
            print("❌ Test FAILED")
            if not lang_correct:
                print(f"   Language mismatch: got {detected_lang}, expected {case['expected_lang']}")
            if not urgency_correct:
                print(f"   Urgency mismatch: got {urgency}, expected {case['expected_urgency']}")

def demonstrate_transliteration():
    """Demonstrate Roman Urdu to Urdu transliteration."""
    print(f"\n🔄 Roman Urdu to Urdu Transliteration Examples")
    print("-" * 60)
    
    transliteration_examples = [
        "ambulance chahiye",
        "hospital jana hai", 
        "police bulao",
        "fire lag gayi hai",
        "emergency hai",
        "salam alaikum",
        "madad chahiye"
    ]
    
    for roman_text in transliteration_examples:
        urdu_text = transliterate_roman_to_urdu(roman_text)
        print(f"Roman: {roman_text}")
        print(f"Urdu:  {urdu_text}")
        print()

def demonstrate_keyword_extraction():
    """Demonstrate keyword extraction for different services."""
    print(f"\n🔑 Service-Specific Keyword Extraction")
    print("-" * 60)
    
    service_examples = {
        "Medical": [
            "ایمبولینس چاہیے",
            "ambulance chahiye",
            "doctor ko bulao",
            "patient be hosh hai"
        ],
        "Police": [
            "ڈکیتی ہو رہی ہے",
            "dakaiti ho rahi hai", 
            "police bulao",
            "chor ne chori ki hai"
        ],
        "Disaster": [
            "سیلاب آ گیا ہے",
            "fire lag gayi hai",
            "earthquake aaya hai",
            "evacuation chahiye"
        ]
    }
    
    for service, examples in service_examples.items():
        print(f"\n🏥 {service} Service:")
        for example in examples:
            keywords = extract_urdu_keywords(example)
            print(f"  '{example}' → {keywords}")

def main():
    """Run the complete demonstration."""
    try:
        demonstrate_urdu_features()
        demonstrate_transliteration()
        demonstrate_keyword_extraction()
        
        print("\n" + "=" * 60)
        print("🎉 Urdu & Roman Urdu functionality demonstration complete!")
        print("\nKey Features Demonstrated:")
        print("✅ Language detection (Urdu, Roman Urdu, Mixed, English)")
        print("✅ Greeting detection and routing")
        print("✅ Emergency keyword extraction")
        print("✅ Urgency level detection")
        print("✅ Roman Urdu to Urdu transliteration")
        print("✅ Service-specific classification")
        print("✅ Multi-language follow-up messages")
        
        print("\n🚀 AlertMate now supports:")
        print("• Urdu script (اردو)")
        print("• Roman Urdu (Roman script)")
        print("• Mixed language inputs")
        print("• Emergency classification in Urdu")
        print("• Urdu greetings and responses")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
