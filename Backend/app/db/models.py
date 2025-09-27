"""SQLAlchemy ORM models for AlertMate."""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(120))
    blood_group: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cnic: Mapped[Optional[str]] = mapped_column(String(32), unique=True, nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    email: Mapped[str] = mapped_column(String(120), unique=True)
    password_salt: Mapped[str] = mapped_column(String(64))
    password_hash: Mapped[str] = mapped_column(String(256))
    lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    events: Mapped[list["ServiceEvent"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    role: Mapped[ConversationRole] = mapped_column(Enum(ConversationRole))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    user: Mapped[User] = relationship(back_populates="messages")


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trace_id: Mapped[str] = mapped_column(String(64), index=True)
    service: Mapped[ServiceType] = mapped_column(Enum(ServiceType))
    priority: Mapped[int] = mapped_column(Integer, default=3)
    status: Mapped[AgentTaskStatus] = mapped_column(Enum(AgentTaskStatus), default=AgentTaskStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class ServiceEventType(str, enum.Enum):
    APPOINTMENT = "appointment"
    AMBULANCE = "ambulance"
    GENERAL = "general"


class ServiceEvent(Base):
    __tablename__ = "service_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    trace_id: Mapped[str] = mapped_column(String(64), index=True)
    service: Mapped[ServiceType] = mapped_column(Enum(ServiceType))
    event_type: Mapped[ServiceEventType] = mapped_column(Enum(ServiceEventType))
    title: Mapped[str] = mapped_column(String(160))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    user: Mapped[User] = relationship(back_populates="events")

