"""Service layer for recording and retrieving simulated service events."""

from __future__ import annotations

from typing import Iterable, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ServiceEvent
from app.models.events import ServiceEventCreate


def record_service_event(session: Session, payload: ServiceEventCreate) -> ServiceEvent:
    event = ServiceEvent(**payload.model_dump())
    session.add(event)
    session.flush()
    session.refresh(event)
    return event


def list_service_events(session: Session, *, limit: int = 50) -> List[ServiceEvent]:
    stmt = select(ServiceEvent).order_by(ServiceEvent.created_at.desc()).limit(limit)
    return list(session.execute(stmt).scalars().all())


def events_by_service(session: Session) -> Iterable[tuple[str, int]]:
    stmt = (
        select(ServiceEvent.service, ServiceEvent.id)
        .order_by(ServiceEvent.service)
    )
    rows = session.execute(stmt).all()
    counts: dict[str, int] = {}
    for service, _ in rows:
        counts[service.value] = counts.get(service.value, 0) + 1
    return counts.items()
