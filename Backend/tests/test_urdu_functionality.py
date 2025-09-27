"""Test Urdu and Roman Urdu functionality."""

import pytest
from httpx import ASGITransport, AsyncClient

from server import app
from app.utils.urdu_language import (
    detect_urdu_language,
    extract_urdu_keywords,
    is_urdu_greeting,
    get_urdu_urgency_level,
    transliterate_roman_to_urdu,
)


class TestUrduLanguageDetection:
    """Test Urdu language detection functionality."""
    
    def test_detect_urdu_language_urdu(self):
        """Test detection of Urdu script."""
        assert detect_urdu_language("ایمرجنسی ہے") == "urdu"
        assert detect_urdu_language("ہسپتال جانا ہے") == "urdu"
        assert detect_urdu_language("پولیس چاہیے") == "urdu"
    
    def test_detect_urdu_language_roman_urdu(self):
        """Test detection of Roman Urdu."""
        assert detect_urdu_language("emergency hai") == "roman_urdu"
        assert detect_urdu_language("hospital jana hai") == "roman_urdu"
        assert detect_urdu_language("police chahiye") == "roman_urdu"
    
    def test_detect_urdu_language_mixed(self):
        """Test detection of mixed language."""
        assert detect_urdu_language("ایمرجنسی emergency hai") == "mixed"
        assert detect_urdu_language("hospital میں جانا ہے") == "mixed"
    
    def test_detect_urdu_language_english(self):
        """Test detection of English."""
        assert detect_urdu_language("I need help") == "english"
        assert detect_urdu_language("Call ambulance") == "english"


class TestUrduGreetings:
    """Test Urdu greeting detection."""
    
    def test_urdu_greetings(self):
        """Test Urdu greeting detection."""
        assert is_urdu_greeting("سلام") == True
        assert is_urdu_greeting("سلام علیکم") == True
        assert is_urdu_greeting("السلام علیکم") == True
        assert is_urdu_greeting("salam") == True
        assert is_urdu_greeting("salaam alaikum") == True
        assert is_urdu_greeting("assalamualaikum") == True
    
    def test_english_greetings(self):
        """Test English greeting detection."""
        assert is_urdu_greeting("hello") == True
        assert is_urdu_greeting("hi") == True
        assert is_urdu_greeting("hey") == True


class TestUrduKeywordExtraction:
    """Test Urdu keyword extraction."""
    
    def test_extract_medical_keywords_urdu(self):
        """Test extraction of medical keywords in Urdu."""
        keywords = extract_urdu_keywords("ایمبولینس چاہیے، مریض بے ہوش ہے")
        assert "ایمبولینس" in keywords
        assert "بے ہوش" in keywords
    
    def test_extract_medical_keywords_roman_urdu(self):
        """Test extraction of medical keywords in Roman Urdu."""
        keywords = extract_urdu_keywords("ambulance chahiye, patient be hosh hai")
        assert "ambulance" in keywords
        assert "be hosh" in keywords
    
    def test_extract_police_keywords_urdu(self):
        """Test extraction of police keywords in Urdu."""
        keywords = extract_urdu_keywords("ڈکیتی ہو رہی ہے، پولیس بلاو")
        assert "ڈکیتی" in keywords
        assert "پولیس" in keywords
    
    def test_extract_disaster_keywords_urdu(self):
        """Test extraction of disaster keywords in Urdu."""
        keywords = extract_urdu_keywords("سیلاب آ گیا ہے، مدد چاہیے")
        assert "سیلاب" in keywords
        assert "مدد" in keywords


class TestUrduUrgencyDetection:
    """Test Urdu urgency level detection."""
    
    def test_high_urgency_urdu(self):
        """Test high urgency detection in Urdu."""
        urgency, reason = get_urdu_urgency_level("مریض بے ہوش ہے، سانس نہیں آ رہی")
        assert urgency == 1
        assert "بے ہوش" in reason or "سانس نہیں" in reason
    
    def test_medium_urgency_urdu(self):
        """Test medium urgency detection in Urdu."""
        urgency, reason = get_urdu_urgency_level("ہاتھ ٹوٹ گیا ہے")
        assert urgency == 2
        assert "ٹوٹ" in reason
    
    def test_high_urgency_roman_urdu(self):
        """Test high urgency detection in Roman Urdu."""
        urgency, reason = get_urdu_urgency_level("patient be hosh hai, saans nahin aa rahi")
        assert urgency == 1
        assert "be hosh" in reason or "saans nahin" in reason


class TestUrduTransliteration:
    """Test Roman Urdu to Urdu transliteration."""
    
    def test_transliteration(self):
        """Test Roman Urdu to Urdu transliteration."""
        assert transliterate_roman_to_urdu("ambulance") == "ایمبولینس"
        assert transliterate_roman_to_urdu("hospital") == "ہسپتال"
        assert transliterate_roman_to_urdu("police") == "پولیس"
        assert transliterate_roman_to_urdu("salam") == "سلام"


class TestUrduEmergencyFlows:
    """Test complete emergency flows with Urdu."""
    
    @pytest.mark.asyncio
    async def test_urdu_medical_emergency(self):
        """Test medical emergency in Urdu."""
        # First create a test user
        user_payload = {
            "user_id": "u_urdu_1",
            "email": "urdu_test@example.com",
            "password": "TestPassword123",
            "name": "Urdu Test User",
            "lat": 24.8607,
            "lon": 67.0011
        }
        
        payload = {
            "userid": "u_urdu_1",
            "user_location": "کراچی",
            "lang": "ur",
            "lat": 24.8093,
            "lon": 67.05,
            "user_query": "ایمبولینس چاہیے، مریض بے ہوش ہے",
        }

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Create user first
            await client.post("/api/v1/users", json=user_payload)
            response = await client.post("/api/v1/dispatch", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["front_agent"]["selected_service"] == "medical"
        assert body["front_agent"]["urgency"] in {1, 2}
        assert body["service_agent_response"]["service"] == "medical"
    
    @pytest.mark.asyncio
    async def test_roman_urdu_police_emergency(self):
        """Test police emergency in Roman Urdu."""
        # First create a test user
        user_payload = {
            "user_id": "u_roman_1",
            "email": "roman_test@example.com",
            "password": "TestPassword123",
            "name": "Roman Test User",
            "lat": 24.8607,
            "lon": 67.0011
        }
        
        payload = {
            "userid": "u_roman_1",
            "user_location": "Lahore",
            "lang": "ur-en",
            "lat": 31.5497,
            "lon": 74.3436,
            "user_query": "dakaiti ho rahi hai, police bulao",
        }

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Create user first
            await client.post("/api/v1/users", json=user_payload)
            response = await client.post("/api/v1/dispatch", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["front_agent"]["selected_service"] == "police"
        assert body["front_agent"]["urgency"] in {1, 2}
        assert body["service_agent_response"]["service"] == "police"
    
    @pytest.mark.asyncio
    async def test_urdu_greeting_routing(self):
        """Test that Urdu greetings route to general service."""
        # First create a test user
        user_payload = {
            "user_id": "u_greeting_1",
            "email": "greeting_test@example.com",
            "password": "TestPassword123",
            "name": "Greeting Test User",
            "lat": 24.8607,
            "lon": 67.0011
        }
        
        payload = {
            "userid": "u_greeting_1",
            "user_location": "Islamabad",
            "lang": "ur",
            "lat": 33.6844,
            "lon": 73.0479,
            "user_query": "سلام علیکم",
        }

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Create user first
            await client.post("/api/v1/users", json=user_payload)
            response = await client.post("/api/v1/dispatch", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["front_agent"]["selected_service"] == "general"
        assert body["front_agent"]["follow_up_required"] == True
        assert body["service_agent_response"]["service"] == "general"
    
    @pytest.mark.asyncio
    async def test_mixed_language_emergency(self):
        """Test mixed language emergency."""
        # First create a test user
        user_payload = {
            "user_id": "u_mixed_1",
            "email": "mixed_test@example.com",
            "password": "TestPassword123",
            "name": "Mixed Test User",
            "lat": 24.8607,
            "lon": 67.0011
        }
        
        payload = {
            "userid": "u_mixed_1",
            "user_location": "Karachi",
            "lang": "ur-en",
            "lat": 24.8607,
            "lon": 67.0011,
            "user_query": "Fire لگ گئی ہے، آگ emergency",
        }

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Create user first
            await client.post("/api/v1/users", json=user_payload)
            response = await client.post("/api/v1/dispatch", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["front_agent"]["selected_service"] == "disaster"
        assert body["front_agent"]["urgency"] in {1, 2}
        assert body["service_agent_response"]["service"] == "disaster"


if __name__ == "__main__":
    pytest.main([__file__])
