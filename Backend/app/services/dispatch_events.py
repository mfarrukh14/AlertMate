"""Service layer for recording and retrieving dispatch events."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import Session

from app.db.models import DispatchEvent
from app.models.dispatch_events import DispatchEventCreate, DispatchEventUpdate
from app.models.dispatch import ServiceType


def record_dispatch_event(session: Session, payload: DispatchEventCreate) -> DispatchEvent:
    """Record a new dispatch event."""
    event = DispatchEvent(**payload.model_dump())
    session.add(event)
    session.flush()
    session.refresh(event)
    return event


def update_dispatch_event(session: Session, event_id: int, update_data: DispatchEventUpdate) -> Optional[DispatchEvent]:
    """Update an existing dispatch event."""
    event = session.get(DispatchEvent, event_id)
    if not event:
        return None
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(event, field, value)
    
    event.updated_at = datetime.utcnow()
    session.flush()
    session.refresh(event)
    return event


def get_dispatch_events(
    session: Session, 
    *, 
    limit: int = 50,
    offset: int = 0,
    service: Optional[ServiceType] = None,
    status: Optional[str] = None,
    hours: Optional[int] = None
) -> List[DispatchEvent]:
    """Get dispatch events with optional filtering."""
    stmt = select(DispatchEvent)
    
    if service:
        stmt = stmt.where(DispatchEvent.service == service)
    
    if status:
        stmt = stmt.where(DispatchEvent.status == status)
    
    if hours:
        since = datetime.utcnow() - timedelta(hours=hours)
        stmt = stmt.where(DispatchEvent.created_at >= since)
    
    stmt = stmt.order_by(desc(DispatchEvent.created_at)).offset(offset).limit(limit)
    return list(session.execute(stmt).scalars().all())


def get_dispatch_events_by_user(session: Session, user_id: str, limit: int = 20) -> List[DispatchEvent]:
    """Get dispatch events for a specific user."""
    stmt = (
        select(DispatchEvent)
        .where(DispatchEvent.user_id == user_id)
        .order_by(desc(DispatchEvent.created_at))
        .limit(limit)
    )
    return list(session.execute(stmt).scalars().all())


def get_dispatch_statistics(session: Session, hours: int = 24) -> dict:
    """Get dispatch statistics for the specified time period."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Total dispatches
    total_dispatches = session.execute(
        select(func.count(DispatchEvent.id))
        .where(DispatchEvent.created_at >= since)
    ).scalar() or 0
    
    # Dispatches by service type
    service_counts = session.execute(
        select(DispatchEvent.service, func.count(DispatchEvent.id))
        .where(DispatchEvent.created_at >= since)
        .group_by(DispatchEvent.service)
    ).all()
    
    service_distribution = {}
    for service, count in service_counts:
        service_distribution[service.value] = count
    
    # Dispatches by status
    status_counts = session.execute(
        select(DispatchEvent.status, func.count(DispatchEvent.id))
        .where(DispatchEvent.created_at >= since)
        .group_by(DispatchEvent.status)
    ).all()
    
    status_distribution = {}
    for status, count in status_counts:
        status_distribution[status] = count
    
    # Average response time (from dispatch to completion)
    completed_events = session.execute(
        select(DispatchEvent)
        .where(and_(
            DispatchEvent.created_at >= since,
            DispatchEvent.status == "completed"
        ))
    ).scalars().all()
    
    avg_response_time = 0.0
    if completed_events:
        total_time = sum(
            (event.updated_at - event.created_at).total_seconds() 
            for event in completed_events
        )
        avg_response_time = total_time / len(completed_events)
    
    return {
        "total_dispatches": total_dispatches,
        "service_distribution": service_distribution,
        "status_distribution": status_distribution,
        "average_response_time": round(avg_response_time, 1)
    }


def get_dispatch_events_for_graph(session: Session, hours: int = 24) -> List[dict]:
    """Get dispatch events formatted for graph display."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    events = session.execute(
        select(DispatchEvent)
        .where(DispatchEvent.created_at >= since)
        .order_by(DispatchEvent.created_at)
    ).scalars().all()
    
    result = []
    for event in events:
        result.append({
            "id": event.id,
            "trace_id": event.trace_id,
            "service": event.service.value,
            "subservice": event.subservice,
            "action_taken": event.action_taken,
            "priority": event.priority,
            "status": event.status,
            "user_location": event.user_location,
            "user_lat": event.user_lat,
            "user_lon": event.user_lon,
            "created_at": event.created_at.isoformat(),
            "updated_at": event.updated_at.isoformat(),
            "metadata": event.event_metadata or {}
        })
    
    return result
