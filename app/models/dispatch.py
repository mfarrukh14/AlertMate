"""Pydantic schemas for the dispatch API."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ServiceType(str, Enum):
    MEDICAL = "medical"
    POLICE = "police"
    DISASTER = "disaster"
    GENERAL = "general"


class DispatchRequest(BaseModel):
    userid: str = Field(..., min_length=1)
    user_location: str = Field(..., min_length=1)
    lang: str = Field(..., min_length=2, max_length=5)
    lat: float
    lon: float
    user_query: str = Field(..., min_length=5)
    timestamp: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp supplied by the client if available.",
    )

    @field_validator("lang")
    def normalize_lang(cls, value: str) -> str:
        return value.lower()


class FrontAgentOutput(BaseModel):
    keywords: List[str]
    urgency: int = Field(..., ge=1, le=3)
    selected_service: ServiceType
    explain: str = Field(..., min_length=5)
    follow_up_required: bool = False
    follow_up_reason: Optional[str] = None

    @field_validator("keywords")
    def validate_keywords(cls, value: List[str]) -> List[str]:
        if not (3 <= len(value) <= 8):
            raise ValueError("keywords must contain between 3 and 8 items")
        return value


class ServiceAgentResponse(BaseModel):
    service: ServiceType
    subservice: str
    action_taken: Optional[str]
    follow_up_required: bool
    follow_up_question: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DispatchResponse(BaseModel):
    status: str
    trace_id: str
    front_agent: FrontAgentOutput
    service_agent_response: ServiceAgentResponse


class ErrorResponse(BaseModel):
    status: str = "error"
    detail: str
    trace_id: Optional[str] = None


class ChatRequest(BaseModel):
    userid: str = Field(default="guest", min_length=1)
    user_location: Optional[str] = None
    lang: str = Field(default="en", min_length=2, max_length=5)
    lat: Optional[float] = None
    lon: Optional[float] = None
    user_query: str = Field(..., min_length=1)
    timestamp: Optional[str] = None

    def to_dispatch_request(self) -> DispatchRequest:
        lat = self.lat if self.lat is not None else 0.0
        lon = self.lon if self.lon is not None else 0.0
        user_location = self.user_location or "unspecified"
        query = self.user_query.strip()
        if len(query) < 5:
            repeated = (query + " ") * 3
            query = repeated.strip()

        return DispatchRequest(
            userid=self.userid,
            user_location=user_location,
            lang=self.lang,
            lat=lat,
            lon=lon,
            user_query=query,
            timestamp=self.timestamp,
        )


class ChatResponse(BaseModel):
    status: str
    trace_id: str
    reply: str
    front_agent: FrontAgentOutput
    service_agent_response: ServiceAgentResponse
