"""FastAPI application entry point for AlertMate MVP."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, Optional, List

from fastapi import Depends, FastAPI, HTTPException, status, Request, Response, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
import uvicorn
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import ValidationError

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
from app.utils.network_utils import detect_network_quality, should_use_minimal_response, build_minimal_response, build_standard_response
from app.models.user import UserRegistrationRequest, UserResponse, LoginRequest, AuthenticatedUser
from app.services.user_service import (
    UserConflictError,
    UserNotFoundError,
    get_user_by_user_id,
    register_user,
    authenticate_user,
)
from app.services.auth import verify_password
from app.config import SESSION_SECRET_KEY, SESSION_COOKIE_NAME, SESSION_MAX_AGE
from app.utils.session import create_session_token, verify_session_token, get_session_expiry
from app.templates import get_login_signup_page, get_chat_page, get_admin_dashboard

configure_logging()
logger = logging.getLogger("alertmate.server")

app = FastAPI(
    title="AlertMate Dispatch Service",
    version="0.1.0",
    description="MVP FastAPI + LangGraph multi-agent router",
)

dispatch_router = DispatchRouter()
init_db()


def get_current_user(
    request: Request,
    session: Session = Depends(get_session)
) -> Optional[UserResponse]:
    """Get the current authenticated user from session cookie."""
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    logger.debug(f"Session token from cookie: {session_token is not None}")
    
    if not session_token:
        logger.debug("No session token found")
        return None
        
    payload = verify_session_token(session_token)
    logger.debug(f"Token verification result: {payload is not None}")
    
    if not payload:
        logger.debug("Token verification failed")
        return None
        
    try:
        user = get_user_by_user_id(session, payload["user_id"])
        logger.debug(f"User found: {user.user_id}")
        return UserResponse.model_validate(user)
    except UserNotFoundError:
        logger.debug("User not found in database")
        return None


def require_auth(current_user: Optional[UserResponse] = Depends(get_current_user)) -> UserResponse:
    """Require authentication, raise HTTP 401 if not authenticated."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return current_user


@app.exception_handler(AgentError)
async def agent_error_handler(_, exc: AgentError):
    logger.exception("AgentError: %s", exc)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(detail=str(exc)).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    logger.error("Validation error: %s", exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
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


def _build_chat_reply(front: FrontAgentOutput, service: ServiceAgentResponse, request: Optional[DispatchRequest] = None) -> str:
    """Build chat reply with network-aware optimization."""
    
    # Detect network quality and determine response mode
    if request:
        network_quality = detect_network_quality(request.network_quality, request.connection_type)
        use_minimal = should_use_minimal_response(network_quality, front.urgency)
        language = request.lang
        
        logger.info(
            "Building response",
            extra={
                "network_quality": network_quality.value,
                "connection_type": request.connection_type,
                "urgency": front.urgency,
                "use_minimal": use_minimal,
                "language": language
            }
        )
        
        if use_minimal:
            return build_minimal_response(front, service, language)
    
    # Default to standard response
    return build_standard_response(front, service)


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: UserResponse = Depends(require_auth)
) -> ChatResponse:
    # Override userid from auth context
    dispatch_request = request.to_dispatch_request()
    dispatch_request.userid = current_user.user_id
    
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

    reply = _build_chat_reply(front_output, service_response, dispatch_request)

    return ChatResponse(
        status="ok",
        trace_id=trace_id,
        reply=reply,
        front_agent=front_output,
        service_agent_response=service_response,
    )


# Authentication endpoints
@app.post("/api/v1/auth/signup", response_model=UserResponse)
def signup_endpoint(
    payload: UserRegistrationRequest,
    response: Response,
    session: Session = Depends(get_session),
) -> UserResponse:
    """Register a new user and create a session."""
    try:
        logger.info("Signup attempt", extra={"payload_data": payload.model_dump(exclude={"password"})})
        user, created = register_user(session, payload)
        session.commit()
        
        # Create session
        expires_at = get_session_expiry()
        session_token = create_session_token(user.user_id, expires_at)
        
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_token,
            max_age=SESSION_MAX_AGE,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
    except UserConflictError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValidationError as exc:
        session.rollback()
        logger.error("Validation error during signup", extra={"errors": exc.errors()})
        raise HTTPException(status_code=422, detail=f"Validation error: {exc.errors()}") from exc
    except Exception as exc:  # pragma: no cover - defensive
        session.rollback()
        logger.exception("Failed to register user", extra={"error": str(exc)})
        raise HTTPException(status_code=500, detail="internal server error") from exc

    user_response = UserResponse.model_validate(user)
    if created:
        json_response = JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=user_response.model_dump(mode="json"),
        )
        # Copy the session cookie to the JSONResponse
        json_response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_token,
            max_age=SESSION_MAX_AGE,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        return json_response
    return user_response


@app.post("/api/v1/auth/login")
def login_endpoint(
    payload: LoginRequest,
    response: Response,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Authenticate user and create session."""
    try:
        user = authenticate_user(session, payload.email, payload.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
            
        session.commit()
        
        # Create session
        expires_at = get_session_expiry()
        session_token = create_session_token(user.user_id, expires_at)
        
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_token,
            max_age=SESSION_MAX_AGE,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        return {
            "status": "success",
            "message": "Login successful",
            "user": UserResponse.model_validate(user).model_dump(mode="json")
        }
        
    except Exception as exc:  # pragma: no cover - defensive
        session.rollback()
        logger.exception("Login failed", extra={"email": payload.email, "error": str(exc)})
        raise HTTPException(status_code=500, detail="internal server error") from exc


@app.post("/api/v1/auth/logout")
def logout_endpoint(response: Response) -> Dict[str, str]:
    """Clear the user session."""
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return {"status": "success", "message": "Logout successful"}


@app.get("/api/v1/auth/me", response_model=UserResponse)
def get_current_user_endpoint(current_user: UserResponse = Depends(require_auth)) -> UserResponse:
    """Get the current authenticated user."""
    return current_user


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


# Frontend Routes
@app.get("/", response_class=HTMLResponse)
async def root_redirect(current_user: Optional[UserResponse] = Depends(get_current_user)) -> str:
    """Root route - redirect based on auth status."""
    if current_user:
        return RedirectResponse(url="/chat", status_code=302)
    return get_login_signup_page()


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(current_user: UserResponse = Depends(require_auth)) -> str:
    """Authenticated chat interface."""
    return get_chat_page()


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(current_user: UserResponse = Depends(require_auth)) -> str:
    """Admin dashboard - requires authentication."""
    # TODO: Add proper admin role checking
    return get_admin_dashboard()


# Admin API endpoints
@app.get("/api/v1/admin/stats")
async def get_admin_stats(current_user: UserResponse = Depends(require_auth)) -> Dict[str, Any]:
    """Get admin dashboard statistics."""
    # TODO: Implement real stats from database
    return {
        "active_emergencies": 12,
        "total_users": 834,
        "tasks_completed": 276,
        "average_response_time": 23.5
    }


@app.get("/api/v1/admin/queue")
async def get_admin_queue(current_user: UserResponse = Depends(require_auth)) -> List[Dict[str, Any]]:
    """Get active task queue for admin dashboard."""
    # TODO: Implement real queue data from database
    return [
        {
            "id": 1,
            "service": "medical",
            "priority": 3,
            "created_at": datetime.now().isoformat(),
            "user_location": "Karachi, PK"
        }
    ]


@app.get("/api/v1/admin/activity")
async def get_admin_activity(current_user: UserResponse = Depends(require_auth)) -> List[Dict[str, Any]]:
    """Get recent activity for admin dashboard."""
    # TODO: Implement real activity data from database
    return [
        {
            "type": "medical",
            "message": "Medical emergency resolved in Karachi",
            "timestamp": datetime.now().isoformat()
        }
    ]


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
