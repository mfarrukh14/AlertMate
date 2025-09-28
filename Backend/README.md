# AlertMate Dispatch MVP

Minimal FastAPI + LangGraph multi-agent router that triages emergency requests across medical, police, and disaster services.

## Features

- `/api/v1/dispatch` endpoint accepting location, language, and user query metadata.
- Front dispatcher agent extracts keywords, sets urgency (1–3), and selects the appropriate downstream service.
- LangGraph orchestrates the front and downstream service agents while sharing structured state between nodes.
- Service agents (medical, police, disaster) choose subservices, trigger mocked actions, and ask targeted follow-up questions when needed.
- Smart conversation guardrails detect casual greetings or low-information chat, keep the request with the front agent, and ask for more detail before paging any service.
- Optional Gemini LLM integration for nuanced routing with graceful fallback to deterministic heuristics.
- Structured JSON responses containing front-agent reasoning, downstream action, `trace_id`, and follow-up prompts.
- Rotating file + console logging pipeline for observability.
- Friendly landing page at `/` linking to Swagger UI, OpenAPI JSON, and chat usage tips.

## Design Diagram


![Design Diagram](/Design_diagram.png)

## Setup

```powershell
cd C:\Users\hp\Desktop\MyArchive\Code\AlertMate
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Configuration

Create a `.env` file (or set environment variables) if you plan to use the Gemini LLM-backed agents:

```text
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

Without these variables the system falls back to heuristic routing logic.

## Running the server

```powershell
uvicorn server:app --reload --port 8000
```

Once the server is running, visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to open the live chat console. Enter an emergency message, tweak optional metadata, and the page will display the conversational reply alongside the raw agent decisions.

## Web console

The in-browser console lets you:

- Submit a natural-language emergency description and instantly relay it to `/api/v1/chat`.
- Start with a simple greeting (“hello”)—the front agent will stay in conversation mode and ask clarifying questions until a real incident is described.
- Inspect the front agent's classification, urgency score, and keywords.
- Review the downstream service agent routing, actions, metadata, and trace ID.
- Iterate quickly without needing external REST tools.

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
  -d '{"user_query": "There is smoke coming from the apartment next door"}'
```

> Tip: while the UI is ideal for exploration, the API remains fully scriptable via `curl` or any HTTP client.

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
