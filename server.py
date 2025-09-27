"""FastAPI application entry point for AlertMate MVP."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from app.agents.base import AgentError
from app.agents.router import DispatchRouter
from app.models.dispatch import (
    ChatRequest,
    ChatResponse,
    DispatchRequest,
    DispatchResponse,
    ErrorResponse,
    FrontAgentOutput,
    ServiceAgentResponse,
)
from app.utils.logging_utils import configure_logging

configure_logging()
logger = logging.getLogger("alertmate.server")

app = FastAPI(
    title="AlertMate Dispatch Service",
    version="0.1.0",
    description="MVP FastAPI + LangGraph multi-agent router",
)

dispatch_router = DispatchRouter()


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
