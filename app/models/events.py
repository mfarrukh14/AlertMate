"""Pydantic schemas for service events used in reporting and admin dashboards."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import ServiceEventType
from app.models.dispatch import ServiceType


class ServiceEventRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    trace_id: str
    service: ServiceType
    event_type: ServiceEventType
    title: str
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ServiceEventCreate(BaseModel):
    user_id: str
    trace_id: str
    service: ServiceType
    event_type: ServiceEventType
    title: str
    details: Dict[str, Any] = Field(default_factory=dict)
