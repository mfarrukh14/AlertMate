# Urdu and Roman Urdu Support for AlertMate

This document describes the Urdu and Roman Urdu language support added to the AlertMate emergency response system.

## 🎯 Overview

AlertMate now supports emergency requests in:
- **Urdu Script** (اردو) - Traditional Urdu written in Arabic/Persian script
- **Roman Urdu** - Urdu written in Latin script
- **Mixed Language** - Combination of Urdu, Roman Urdu, and English
- **English** - Original language support maintained

## 🚀 Features Added

### 1. Language Detection
- Automatically detects the language of incoming emergency messages
- Supports Urdu script, Roman Urdu, English, and mixed language inputs
- Handles edge cases like common words that exist in multiple languages

### 2. Emergency Classification
- **Medical Emergencies**: Recognizes Urdu terms like "ایمبولینس", "ہسپتال", "ڈاکٹر"
- **Police Emergencies**: Understands "پولیس", "ڈکیتی", "چوری", "حملہ"
- **Disaster Relief**: Detects "آگ", "سیلاب", "زلزلہ", "طوفان"
- **General Inquiries**: Routes greetings like "سلام علیکم" to general service

### 3. Urgency Detection
- **Level 1 (Critical)**: "بے ہوش", "سانس نہیں", "شدید خون بہنا"
- **Level 2 (Serious)**: "ٹوٹا ہوا", "فریکچر", "ڈکیتی", "حملہ"
- **Level 3 (Informational)**: General inquiries and greetings

### 4. Roman Urdu to Urdu Transliteration
- Converts Roman Urdu terms to proper Urdu script
- Example: "ambulance" → "ایمبولینس", "police" → "پولیس"

### 5. Multi-language Responses
- Provides follow-up messages in appropriate language
- Urdu: "برائے کرم اپنا ایمرجنسی کی تفصیل بتائیں"
- Roman Urdu: "Barae karam apna emergency ki tafseel batayen"

## 📁 Files Modified/Added

### New Files
- `app/utils/urdu_language.py` - Core Urdu language utilities
- `tests/test_urdu_functionality.py` - Comprehensive test suite
- `urdu_demo.py` - Demonstration script
- `URDU_SUPPORT_README.md` - This documentation

### Modified Files
- `app/agents/front_agent.py` - Updated to handle Urdu keywords and language detection
- `app/models/dispatch.py` - Added Urdu language code support
- `app/templates.py` - Updated UI with Urdu language hints
- `app/agents/router.py` - Fixed timezone import issue

## 🔧 Technical Implementation

### Language Detection Algorithm
```python
def detect_urdu_language(text: str) -> str:
    # 1. Check for Urdu script (Arabic/Persian characters)
    # 2. Count Roman Urdu keywords (excluding common English words)
    # 3. Return: 'urdu', 'roman_urdu', 'mixed', or 'english'
```

### Keyword Extraction
- Extracts emergency-related keywords from Urdu and Roman Urdu text
- Maps to appropriate service types (medical, police, disaster)
- Handles partial word matches for better accuracy

### Urgency Classification
- Uses predefined urgency indicators in Urdu and Roman Urdu
- Supports partial matching for flexible text recognition
- Prioritizes critical indicators over general ones

## 🧪 Testing

Run the demonstration script to see all features in action:
```bash
python urdu_demo.py
```

Run the test suite:
```bash
python -m pytest tests/test_urdu_functionality.py -v
```

## 📝 Example Usage

### Urdu Emergency
```
Input: "ایمبولینس چاہیے، مریض بے ہوش ہے"
Output: 
- Language: Urdu
- Service: Medical
- Urgency: Level 1
- Action: Ambulance dispatch
```

### Roman Urdu Emergency
```
Input: "dakaiti ho rahi hai, police bulao jaldi"
Output:
- Language: Roman Urdu  
- Service: Police
- Urgency: Level 2
- Action: Police dispatch
```

### Mixed Language
```
Input: "Fire لگ گئی ہے، آگ emergency hai"
Output:
- Language: Mixed
- Service: Disaster
- Urgency: Level 1
- Action: Fire department alert
```

## 🌐 Language Codes

The system supports these language codes:
- `ur` or `urdu` - Urdu script
- `ur-en` or `roman_urdu` - Roman Urdu
- `en` - English (default)

## 🎯 Benefits

1. **Accessibility**: Serves Urdu-speaking communities in their native language
2. **Accuracy**: Better emergency classification for Urdu speakers
3. **Flexibility**: Supports both traditional and modern Urdu writing styles
4. **Integration**: Seamlessly works with existing English functionality
5. **Scalability**: Easy to extend with additional languages

## 🔮 Future Enhancements

- Voice recognition for Urdu speech
- Additional regional language variants
- SMS support for Urdu script
- Integration with local emergency services
- Real-time translation between languages

## 📞 Emergency Keywords Reference

### Medical (طب)
- Urdu: ایمبولینس، ہسپتال، ڈاکٹر، درد، خون، ٹوٹا ہوا، بے ہوش
- Roman Urdu: ambulance, hospital, doctor, pain, khoon, broken, be hosh

### Police (پولیس)
- Urdu: پولیس، ڈکیتی، چوری، حملہ، تشدد، بندوق، چاقو
- Roman Urdu: police, dakaiti, chori, hamla, tashaddud, banduq, chaqoo

### Disaster (آفات)
- Urdu: آگ، سیلاب، زلزلہ، طوفان، خالی کرو، پناہ گاہ
- Roman Urdu: fire, sailab, zalzala, toofan, khali karo, panah gah

---

