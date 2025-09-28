"""Pydantic schemas for dispatch events used in reporting and admin dashboards."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.dispatch import ServiceType


class DispatchEventRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    trace_id: str
    service: ServiceType
    subservice: str
    action_taken: Optional[str] = None
    priority: int
    user_location: str
    user_lat: Optional[float] = None
    user_lon: Optional[float] = None
    status: str
    event_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class DispatchEventCreate(BaseModel):
    user_id: str
    trace_id: str
    service: ServiceType
    subservice: str
    action_taken: Optional[str] = None
    priority: int = 3
    user_location: str
    user_lat: Optional[float] = None
    user_lon: Optional[float] = None
    status: str = "dispatched"
    event_metadata: Optional[Dict[str, Any]] = None


class DispatchEventUpdate(BaseModel):
    status: Optional[str] = None
    action_taken: Optional[str] = None
    event_metadata: Optional[Dict[str, Any]] = None
