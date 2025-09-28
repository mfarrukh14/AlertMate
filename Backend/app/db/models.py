"""SQLAlchemy ORM models for AlertMate."""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, Column
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.dispatch import ServiceType


class ConversationRole(str, enum.Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class AgentTaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid4()))
    name = Column(String(120))
    blood_group = Column(String(8), nullable=True)
    address = Column(String(255), nullable=True)
    cnic = Column(String(32), unique=True, nullable=True)
    phone_number = Column(String(32), nullable=True)
    emergency_contact_name = Column(String(120), nullable=True)
    emergency_contact_phone = Column(String(32), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    email = Column(String(120), unique=True)
    password_salt = Column(String(64))
    password_hash = Column(String(256))
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    city = Column(String(80), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship(
        "ConversationMessage",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    events = relationship(
        "ServiceEvent",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    role = Column(Enum(ConversationRole))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="messages")


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String(64), index=True)
    service = Column(Enum(ServiceType))
    priority = Column(Integer, default=3)
    status = Column(Enum(AgentTaskStatus), default=AgentTaskStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    payload = Column(JSON, nullable=True)


class ServiceEventType(str, enum.Enum):
    APPOINTMENT = "appointment"
    AMBULANCE = "ambulance"
    DISPATCH = "dispatch"
    EMERGENCY = "emergency"
    GENERAL = "general"


class ServiceEvent(Base):
    __tablename__ = "service_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    trace_id = Column(String(64), index=True)
    service = Column(Enum(ServiceType))
    event_type = Column(Enum(ServiceEventType))
    title = Column(String(160))
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="events")


class DispatchEvent(Base):
    """Tracks when emergency services are dispatched."""
    __tablename__ = "dispatch_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    trace_id = Column(String(64), index=True)
    service = Column(Enum(ServiceType))
    subservice = Column(String(100))
    action_taken = Column(String(255), nullable=True)
    priority = Column(Integer, default=3)
    user_location = Column(String(255))
    user_lat = Column(Float, nullable=True)
    user_lon = Column(Float, nullable=True)
    status = Column(String(50), default="dispatched")  # dispatched, in_progress, completed, cancelled
    event_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


class ServiceLocation(Base):
    """Reference data for hospitals, police stations, disaster centers, etc."""
    __tablename__ = "service_locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    service_type = Column(Enum(ServiceType), index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    city = Column(String(80), index=True)
    address = Column(Text, nullable=True)
    phone = Column(String(32), nullable=True)
    is_active = Column(Integer, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

