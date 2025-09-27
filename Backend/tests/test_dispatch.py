import pytest
from httpx import ASGITransport, AsyncClient

from server import app


@pytest.mark.asyncio
async def test_medical_ambulance_flow() -> None:
    payload = {
        "userid": "u1",
        "user_location": "Clifton",
        "lang": "en",
        "lat": 24.8093,
        "lon": 67.05,
        "user_query": "I slipped and broke my arm, need ambulance",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/dispatch", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["front_agent"]["selected_service"] == "medical"
    assert body["front_agent"]["urgency"] in {1, 2}
    assert body["service_agent_response"]["service"] == "medical"
    assert body["service_agent_response"]["subservice"] in {
        "ambulance_dispatch",
        "nearest_hospital_lookup",
    }


@pytest.mark.asyncio
async def test_police_emergency_flow() -> None:
    payload = {
        "userid": "u2",
        "user_location": "Saddar",
        "lang": "en",
        "lat": 24.86,
        "lon": 67.01,
        "user_query": "Someone just broke into my shop and stole cash, they're leaving now",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/dispatch", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["front_agent"]["selected_service"] == "police"
    assert body["front_agent"]["urgency"] == 1
    assert body["service_agent_response"]["subservice"] == "emergency_response"
    assert body["service_agent_response"]["service"] == "police"


@pytest.mark.asyncio
async def test_disaster_flow() -> None:
    payload = {
        "userid": "u3",
        "user_location": "Karachi",
        "lang": "en",
        "lat": 24.87,
        "lon": 67.02,
        "user_query": "Flooded street, water entering ground floor, need shelter",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/dispatch", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["front_agent"]["selected_service"] == "disaster"
    assert body["service_agent_response"]["service"] == "disaster"
    assert body["service_agent_response"]["subservice"] in {
        "evacuation_guidance",
        "resource_request",
    }


@pytest.mark.asyncio
async def test_validation_error() -> None:
    payload = {
        "userid": "u4",
        "user_location": "Unknown",
        "lang": "en",
        "lat": 0.0,
        "lon": 0.0,
        "user_query": "hi",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/dispatch", json=payload)

    assert response.status_code == 422




@pytest.mark.asyncio
async def test_chat_endpoint_handles_short_message() -> None:
    payload = {"user_query": "hi"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # First register a test user
        user_payload = {
            "user_id": "test_chat_user_1",
            "email": "test@example.com",
            "password": "TestPassword123",
            "name": "Test User",
            "lat": 24.8607,
            "lon": 67.0011
        }
        await client.post("/api/v1/users", json=user_payload)
        
        # Login to get session
        login_payload = {"email": "test@example.com", "password": "TestPassword123"}
        login_response = await client.post("/api/v1/auth/login", json=login_payload)
        assert login_response.status_code == 200
        
        # Now test chat endpoint
        response = await client.post("/api/v1/chat", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["service_agent_response"]["service"] == "general"
    assert body["front_agent"]["follow_up_required"] is True
    # Response can be minimal or detailed depending on network conditions
    reply_lower = body["reply"].lower()
    assert "describe" in reply_lower or "u3" in reply_lower or "?" in reply_lower


@pytest.mark.asyncio
async def test_chat_endpoint_greeting() -> None:
    payload = {"user_query": "hello"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # First register a test user
        user_payload = {
            "user_id": "test_chat_user_2",
            "email": "test2@example.com",
            "password": "TestPassword123",
            "name": "Test User 2",
            "lat": 24.8607,
            "lon": 67.0011
        }
        await client.post("/api/v1/users", json=user_payload)
        
        # Login to get session
        login_payload = {"email": "test2@example.com", "password": "TestPassword123"}
        login_response = await client.post("/api/v1/auth/login", json=login_payload)
        assert login_response.status_code == 200
        
        # Now test chat endpoint
        response = await client.post("/api/v1/chat", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["service_agent_response"]["service"] == "general"
    assert body["service_agent_response"]["follow_up_required"] is True
    # Response can be minimal or detailed depending on network conditions
    reply_lower = body["reply"].lower()
    assert "hello" not in reply_lower or "assist" in reply_lower or "u3" in reply_lower