"""FastAPI application entry point for AlertMate MVP."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
from sqlalchemy.orm import Session

from app.agents.base import AgentError
from app.agents.router import DispatchRouter
from app.models.dispatch import (
    ChatRequest,
    ChatResponse,
    DispatchRequest,
    DispatchResponse,
    ErrorResponse,
    ServiceType,
    FrontAgentOutput,
    ServiceAgentResponse,
)
from app.db import get_session, init_db
from app.utils.logging_utils import configure_logging
from app.models.user import UserRegistrationRequest, UserResponse
from app.services.user_service import (
    UserConflictError,
    UserNotFoundError,
    get_user_by_user_id,
    register_user,
)

configure_logging()
logger = logging.getLogger("alertmate.server")

app = FastAPI(
    title="AlertMate Dispatch Service",
    version="0.1.0",
    description="MVP FastAPI + LangGraph multi-agent router",
)

dispatch_router = DispatchRouter()
init_db()


@app.exception_handler(AgentError)
async def agent_error_handler(_, exc: AgentError):
    logger.exception("AgentError: %s", exc)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(detail=str(exc)).model_dump(),
    )


@app.post("/api/v1/dispatch", response_model=DispatchResponse)
async def dispatch_endpoint(request: DispatchRequest) -> DispatchResponse:
    trace_id = str(uuid.uuid4())
    start_time = time.perf_counter()
    try:
        front_output, service_response = await asyncio.to_thread(
            dispatch_router.process, request, trace_id
        )
    except AgentError as exc:
        logger.exception("Failed to process request", extra={"trace_id": trace_id})
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unhandled error during dispatch", extra={"trace_id": trace_id})
        raise HTTPException(status_code=500, detail="internal server error") from exc

    latency = time.perf_counter() - start_time
    logger.info(
        "Dispatch completed",
        extra={
            "trace_id": trace_id,
            "latency_ms": round(latency * 1000, 2),
            "service": service_response.service.value,
            "urgency": front_output.urgency,
        },
    )

    response = DispatchResponse(
        status="ok",
        trace_id=trace_id,
        front_agent=front_output,
        service_agent_response=service_response,
    )
    return response


def _build_chat_reply(front: FrontAgentOutput, service: ServiceAgentResponse) -> str:
    sections: list[str] = []

    sections.append(front.explain)
    sections.append(
        " "
        f"Priority level: {front.urgency} (1=low, 3=high). Keywords noted: {', '.join(front.keywords)}."
    )

    if service.service == ServiceType.GENERAL:
        sections.append(
            "I'll stay on the line until I know more. "
            "No emergency service has been engaged yet."
        )
    else:
        service_intro = (
            f"I've routed this to the {service.service.value.upper()} team"
            f" (subservice: {service.subservice})."
        )
        if service.action_taken:
            service_intro += f" Action taken: {service.action_taken}."
        sections.append(service_intro)

    if front.follow_up_required and front.follow_up_reason:
        sections.append(f"Heads-up: {front.follow_up_reason}")

    if service.follow_up_required:
        follow_up_text = service.follow_up_question or "They'll need more details shortly."
        sections.append(f"Next step: {follow_up_text}")

    if service.metadata:
        metadata_bits = ", ".join(f"{k}: {v}" for k, v in service.metadata.items())
        sections.append(f"Additional info: {metadata_bits}")

    return "\n\n".join(section.strip() for section in sections if section)


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    dispatch_request = request.to_dispatch_request()
    trace_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    try:
        front_output, service_response = await asyncio.to_thread(
            dispatch_router.process, dispatch_request, trace_id
        )
    except AgentError as exc:
        logger.exception("Chat dispatch failed", extra={"trace_id": trace_id})
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unhandled error during chat", extra={"trace_id": trace_id})
        raise HTTPException(status_code=500, detail="internal server error") from exc

    latency = time.perf_counter() - start_time
    logger.info(
        "Chat completed",
        extra={
            "trace_id": trace_id,
            "latency_ms": round(latency * 1000, 2),
            "service": service_response.service.value,
            "urgency": front_output.urgency,
        },
    )

    reply = _build_chat_reply(front_output, service_response)

    return ChatResponse(
        status="ok",
        trace_id=trace_id,
        reply=reply,
        front_agent=front_output,
        service_agent_response=service_response,
    )


@app.post("/api/v1/users", response_model=UserResponse)
def register_user_endpoint(
    payload: UserRegistrationRequest,
    session: Session = Depends(get_session),
) -> UserResponse:
    try:
        user, created = register_user(session, payload)
        session.commit()
    except UserConflictError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        session.rollback()
        logger.exception(
            "Failed to register user",
            extra={"userid": payload.user_id, "error": str(exc)},
        )
        raise HTTPException(status_code=500, detail="internal server error") from exc

    response_model = UserResponse.model_validate(user)
    if created:
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_model.model_dump(mode="json"),
        )
    return response_model


@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
def get_user_endpoint(
    user_id: str,
    session: Session = Depends(get_session),
) -> UserResponse:
    try:
        user = get_user_by_user_id(session, user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return UserResponse.model_validate(user)


@app.get("/", response_class=HTMLResponse)
async def chat_ui() -> str:
    return """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>AlertMate Chat Console</title>
    <style>
        :root {
            color-scheme: light dark;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif;
            background: #0f172a;
            color: #e2e8f0;
        }
        body {
            margin: 0;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        header {
            padding: 1.5rem 2rem;
            background: linear-gradient(135deg, #1d4ed8, #0ea5e9);
            color: #f8fafc;
            box-shadow: 0 4px 20px rgba(15, 23, 42, 0.35);
        }
        main {
            flex: 1;
            padding: 2rem;
            display: grid;
            grid-template-columns: 3fr 2fr;
            gap: 1.5rem;
        }
        @media (max-width: 960px) {
            main {
                grid-template-columns: 1fr;
            }
        }
        section {
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(16px);
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.45);
        }
        h1 {
            margin: 0 0 0.25rem 0;
            font-size: clamp(1.8rem, 4vw, 2.5rem);
            letter-spacing: -0.03em;
        }
        p.subtitle {
            margin: 0;
            opacity: 0.9;
            max-width: 48rem;
        }
        label {
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            display: block;
            margin-bottom: 0.35rem;
        }
        input, textarea, select, button {
            width: 100%;
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.35);
            background: rgba(15, 23, 42, 0.6);
            color: inherit;
            padding: 0.75rem 1rem;
            transition: border-color 0.2s ease, transform 0.15s ease;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #38bdf8;
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.25);
        }
        textarea {
            min-height: 140px;
            resize: vertical;
        }
        button {
            font-weight: 600;
            cursor: pointer;
            background: linear-gradient(135deg, #2563eb, #38bdf8);
            border: none;
            margin-top: 0.75rem;
        }
        button:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 12px 24px rgba(37, 99, 235, 0.35);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .chat-log {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            max-height: 70vh;
            overflow-y: auto;
        }
        .bubble {
            padding: 1rem;
            border-radius: 14px;
            line-height: 1.5;
            white-space: pre-wrap;
            border: 1px solid rgba(148, 163, 184, 0.2);
        }
        .bubble.user {
            align-self: flex-end;
            background: rgba(59, 130, 246, 0.2);
            border-color: rgba(59, 130, 246, 0.35);
        }
        .bubble.agent {
            background: rgba(30, 41, 59, 0.8);
        }
        .response-meta {
            display: grid;
            gap: 0.75rem;
            font-size: 0.85rem;
            margin-top: 1rem;
        }
        .meta-card {
            background: rgba(15, 23, 42, 0.55);
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.25);
            padding: 0.75rem;
        }
        code, pre {
            font-family: "JetBrains Mono", "Fira Code", monospace;
        }
        footer {
            padding: 1rem 2rem;
            font-size: 0.85rem;
            opacity: 0.75;
            text-align: center;
        }
        .error {
            color: #f87171;
            margin-top: 0.5rem;
        }
    </style>
</head>
<body>
    <header>
        <h1>AlertMate Ops Console</h1>
        <p class=\"subtitle\">Simulate incoming emergency messages and inspect how the LangGraph-powered agents route the request.</p>
    </header>
    <main>
        <section>
            <form id=\"chat-form\">
                <label for=\"user-query\">Emergency message</label>
                <textarea id=\"user-query\" name=\"user_query\" placeholder=\"Describe the situation...\" required></textarea>

                <label for=\"userid\">User ID (optional)</label>
                <input id=\"userid\" name=\"userid\" placeholder=\"guest\" />

                <label for=\"user-location\">Location (optional)</label>
                <input id=\"user-location\" name=\"user_location\" placeholder=\"Karachi, PK\" />

                <label for=\"language\">Language</label>
                <select id=\"language\" name=\"lang\">
                    <option value=\"en\" selected>English (en)</option>
                    <option value=\"ur\">Urdu (ur)</option>
                    <option value=\"ar\">Arabic (ar)</option>
                </select>

                <div style=\"display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 0.75rem; margin-top: 0.75rem;\">
                    <div>
                        <label for=\"lat\">Latitude</label>
                        <input id=\"lat\" name=\"lat\" type=\"number\" step=\"any\" placeholder=\"24.86\" />
                    </div>
                    <div>
                        <label for=\"lon\">Longitude</label>
                        <input id=\"lon\" name=\"lon\" type=\"number\" step=\"any\" placeholder=\"67.01\" />
                    </div>
                </div>

                <button id=\"submit-btn\" type=\"submit\">Send to AlertMate</button>
                <p id=\"error\" class=\"error\" hidden></p>
            </form>
        </section>
        <section>
            <h2 style=\"margin-top:0;\">Conversation</h2>
            <div id=\"chat-log\" class=\"chat-log\"></div>
            <div id=\"metadata\" class=\"response-meta\"></div>
        </section>
    </main>
    <footer>
        Powered by Groq + LangGraph · Inspect responses via /docs for full API schema.
    </footer>
    <script>
        const form = document.getElementById('chat-form');
        const chatLog = document.getElementById('chat-log');
        const metadata = document.getElementById('metadata');
        const submitBtn = document.getElementById('submit-btn');
        const errorBox = document.getElementById('error');

        function appendBubble(text, role) {
            const bubble = document.createElement('div');
            bubble.className = `bubble ${role}`;
            bubble.textContent = text.trim();
            chatLog.appendChild(bubble);
            chatLog.scrollTop = chatLog.scrollHeight;
        }

        function renderMetadata(data) {
            metadata.innerHTML = '';

            const frontCard = document.createElement('div');
            frontCard.className = 'meta-card';
            frontCard.innerHTML = `
                <strong>Front Agent</strong><br/>
                Service: <code>${data.front_agent.selected_service}</code><br/>
                Urgency: <code>${data.front_agent.urgency}</code><br/>
                Keywords: ${data.front_agent.keywords.join(', ')}<br/>
                Follow-up: ${data.front_agent.follow_up_required ? 'Required' : 'Not required'}
                ${data.front_agent.follow_up_reason ? `<br/>Reason: ${data.front_agent.follow_up_reason}` : ''}
            `;

            const serviceCard = document.createElement('div');
            serviceCard.className = 'meta-card';
            serviceCard.innerHTML = `
                <strong>${data.service_agent_response.service.toUpperCase()} Service</strong><br/>
                Subservice: <code>${data.service_agent_response.subservice}</code><br/>
                Action: ${data.service_agent_response.action_taken || 'N/A'}<br/>
                Metadata: <pre>${JSON.stringify(data.service_agent_response.metadata, null, 2)}</pre>
            `;

            const traceCard = document.createElement('div');
            traceCard.className = 'meta-card';
            traceCard.innerHTML = `Trace ID: <code>${data.trace_id}</code>`;

            metadata.appendChild(frontCard);
            metadata.appendChild(serviceCard);
            metadata.appendChild(traceCard);
        }

        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            errorBox.hidden = true;
            const formData = new FormData(form);
            const userQuery = formData.get('user_query').trim();

            if (!userQuery) {
                errorBox.textContent = 'Please describe the emergency.';
                errorBox.hidden = false;
                return;
            }

            const payload = {
                user_query: userQuery,
                userid: formData.get('userid')?.trim() || 'guest',
                user_location: formData.get('user_location')?.trim() || undefined,
                lang: formData.get('lang') || 'en',
                lat: formData.get('lat') ? Number(formData.get('lat')) : undefined,
                lon: formData.get('lon') ? Number(formData.get('lon')) : undefined
            };

            appendBubble(userQuery, 'user');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Routing...';

            try {
                const response = await fetch('/api/v1/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    const detail = await response.json().catch(() => ({}));
                    throw new Error(detail.detail || 'Request failed');
                }

                const data = await response.json();
                appendBubble(data.reply, 'agent');
                renderMetadata(data);
            } catch (err) {
                errorBox.textContent = err.message || 'Something went wrong.';
                errorBox.hidden = false;
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Send to AlertMate';
                form.user_query.value = '';
                form.user_query.focus();
            }
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def landing_page() -> str:
        return """
        <html>
            <head>
                <title>AlertMate Dispatch Service</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 2rem auto; max-width: 720px; line-height: 1.6; color: #1f2933; }
                    h1 { color: #1f2933; }
                    a { color: #2563eb; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                    code { background-color: #f3f4f6; padding: 0.2rem 0.4rem; border-radius: 4px; }
                    .panel { background-color: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 1.5rem; margin-top: 1.5rem; }
                    ul { padding-left: 1.5rem; }
                </style>
            </head>
            <body>
                <h1>👋 Welcome to AlertMate</h1>
                <p>
                    Your multi-agent dispatch service is up and running. Use the interactive docs or the chat endpoint below to test routing
                    decisions without leaving your browser.
                </p>
                <div class="panel">
                    <h2>Try it out</h2>
                    <ul>
                        <li>Interactive API docs: <a href="/docs">Swagger UI</a></li>
                        <li>Minimal JSON: <a href="/openapi.json">OpenAPI schema</a></li>
                        <li>Chat endpoint: send a <code>POST</code> to <code>/api/v1/chat</code> with a JSON body like <code>{"message": "There's a fire at the library"}</code>.</li>
                    </ul>
                </div>
                <p>Need help? Check the README for full setup and troubleshooting tips.</p>
            </body>
        </html>
        """


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info",
    )
