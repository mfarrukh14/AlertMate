"""Task queue helpers for coordinating agent workloads."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import AgentTask, AgentTaskStatus
from app.models.dispatch import ServiceType


def enqueue_task(
    session: Session,
    *,
    trace_id: str,
    service: ServiceType,
    priority: int,
    payload: Optional[dict] = None,
) -> AgentTask:
    """Store a new task for the given service, prioritised by urgency (1 is highest)."""
    task = AgentTask(
        trace_id=trace_id,
        service=service,
        priority=max(1, min(priority, 5)),
        payload=payload or {},
    )
    session.add(task)
    session.flush()
    return task


def list_pending_tasks(session: Session, service: ServiceType, limit: int = 20) -> List[AgentTask]:
    """Return pending tasks ordered by priority and creation time."""
    stmt: Select[AgentTask] = (
        select(AgentTask)
        .where(
            AgentTask.service == service,
            AgentTask.status == AgentTaskStatus.PENDING,
        )
        .order_by(AgentTask.priority.asc(), AgentTask.created_at.asc())
        .limit(limit)
    )
    return session.execute(stmt).scalars().all()


def update_task_status(
    session: Session,
    *,
    task_id: int,
    status: AgentTaskStatus,
) -> None:
    session.query(AgentTask).filter(AgentTask.id == task_id).update(
        {AgentTask.status: status}
    )
