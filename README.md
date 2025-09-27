# AlertMate Dispatch MVP

Minimal FastAPI + LangGraph-inspired multi-agent router that triages emergency requests across medical, police, and disaster services.

## Features

- `/api/v1/dispatch` endpoint accepting location, language, and user query metadata.
- Front dispatcher agent extracts keywords, sets urgency (1–3), and selects the appropriate downstream service.
- Service agents (medical, police, disaster) choose subservices, trigger mocked actions, and ask targeted follow-up questions when needed.
- Optional Groq LLM integration for nuanced routing with graceful fallback to deterministic heuristics.
- Structured JSON responses containing front-agent reasoning, downstream action, `trace_id`, and follow-up prompts.
- Rotating file + console logging pipeline for observability.
- Friendly landing page at `/` linking to Swagger UI, OpenAPI JSON, and chat usage tips.

## Setup

```powershell
cd C:\Users\hp\Desktop\MyArchive\Code\AlertMate
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Configuration

Create a `.env` file (or set environment variables) if you plan to use the Groq LLM-backed agents:

```text
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Without these variables the system falls back to heuristic routing logic.

## Running the server

```powershell
uvicorn server:app --reload --port 8000
```

Once the server is running, visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to see the landing page with quick links to documentation and sample payloads.

## Example dispatch request

```json
{
  "userid": "u1",
  "user_location": "Clifton",
  "lang": "en",
  "lat": 24.8093,
  "lon": 67.0500,
  "user_query": "I slipped and broke my arm, need ambulance"
}
```

## Chat endpoint

Send free-form text to the chat interface, which internally reuses the dispatch pipeline and returns a conversational summary of the routing decision:

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/chat ^
  -H "Content-Type: application/json" ^
  -d '{"message": "There is smoke coming from the apartment next door"}'
```

The response includes a `reply` field along with the same structured agent data returned by `/api/v1/dispatch`.

## Running tests

```powershell
pytest
```

## Directory highlights

- `server.py` – FastAPI entry point and API routes.
- `app/agents/` – Front dispatcher and service agent implementations (LLM + heuristic logic).
- `app/services/` – Mock integrations (hospitals, police dispatch, disaster shelters).
- `app/models/` – Pydantic models for requests and responses.
- `app/utils/` – Logging and Groq client helpers.
- `tests/` – End-to-end async pytest suite covering core flows.
