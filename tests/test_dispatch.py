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
async def test_chat_ui_served() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/")

    assert response.status_code == 200
    body = response.text
    assert "AlertMate Ops Console" in body
    assert "Send to AlertMate" in body


@pytest.mark.asyncio
async def test_chat_endpoint_handles_short_message() -> None:
    payload = {"user_query": "hi"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/chat", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["service_agent_response"]["service"] == "general"
    assert body["front_agent"]["follow_up_required"] is True
    assert "describe" in body["reply"].lower()


@pytest.mark.asyncio
async def test_chat_endpoint_greeting() -> None:
    payload = {"user_query": "hello"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/chat", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["service_agent_response"]["service"] == "general"
    assert body["service_agent_response"]["follow_up_required"] is True
    assert "hello" not in body["reply"].lower() or "assist" in body["reply"].lower()