#!/usr/bin/env python3
"""Interactive test script for Urdu functionality."""

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

def test_urdu_input(text):
    """Test a single Urdu input and show all results."""
    print(f"\n📝 Testing: '{text}'")
    print("-" * 50)
    
    # Language detection
    language = detect_urdu_language(text)
    print(f"🌐 Language: {language}")
    
    # Greeting check
    is_greeting = is_urdu_greeting(text)
    print(f"👋 Is Greeting: {is_greeting}")
    
    # Keyword extraction
    keywords = extract_urdu_keywords(text)
    print(f"🔑 Keywords: {keywords}")
    
    # Urgency detection
    urgency, reason = get_urdu_urgency_level(text)
    print(f"⚡ Urgency: {urgency} ({reason})")
    
    # Transliteration (if applicable)
    if language in ['roman_urdu', 'mixed']:
        transliterated = transliterate_roman_to_urdu(text)
        print(f"🔄 Transliterated: {transliterated}")
    
    # Follow-up message
    follow_up = get_urdu_follow_up_message(language)
    print(f"💬 Follow-up: {follow_up}")
    
    # Service classification based on keywords
    medical_keywords = ['ایمبولینس', 'ہسپتال', 'ڈاکٹر', 'ambulance', 'hospital', 'doctor', 'pain', 'dard', 'be hosh']
    police_keywords = ['پولیس', 'ڈکیتی', 'چوری', 'police', 'dakaiti', 'chori', 'hamla']
    disaster_keywords = ['آگ', 'سیلاب', 'زلزلہ', 'fire', 'sailab', 'zalzala', 'toofan']
    
    detected_service = "General"
    if any(kw in text.lower() for kw in medical_keywords):
        detected_service = "Medical"
    elif any(kw in text.lower() for kw in police_keywords):
        detected_service = "Police"
    elif any(kw in text.lower() for kw in disaster_keywords):
        detected_service = "Disaster"
    
    print(f"🚨 Detected Service: {detected_service}")

def main():
    """Interactive test interface."""
    print("🚨 AlertMate Urdu Testing Interface")
    print("=" * 50)
    print("Enter Urdu, Roman Urdu, or English emergency messages to test.")
    print("Type 'quit' to exit, 'examples' for sample inputs.")
    print()
    
    # Pre-defined examples
    examples = [
        "ایمبولینس چاہیے، مریض بے ہوش ہے",
        "dakaiti ho rahi hai, police bulao jaldi",
        "fire lag gayi hai, aag emergency",
        "سلام علیکم",
        "salaam alaikum",
        "I need an ambulance",
        "ہاتھ ٹوٹ گیا ہے",
        "ambulance chahiye, patient be hosh hai"
    ]
    
    while True:
        try:
            user_input = input("\n💬 Enter emergency message: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == 'examples':
                print("\n📚 Example inputs:")
                for i, example in enumerate(examples, 1):
                    print(f"{i}. {example}")
                continue
            
            if not user_input:
                print("⚠️ Please enter some text to test.")
                continue
            
            # Test the input
            test_urdu_input(user_input)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
