"""Admin dashboard services for fetching real statistics and dispatch data."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Any

from sqlalchemy import func, select, and_
from sqlalchemy.orm import Session

from app.db.models import User, AgentTask, ServiceEvent, AgentTaskStatus
from app.models.dispatch import ServiceType


def get_dashboard_stats(session: Session) -> Dict[str, Any]:
    """Get real dashboard statistics from database."""
    
    # Total users count
    total_users = session.execute(select(func.count(User.id))).scalar() or 0
    
    # Active emergencies (pending/in-progress tasks)
    active_emergencies = session.execute(
        select(func.count(AgentTask.id))
        .where(AgentTask.status.in_([AgentTaskStatus.PENDING, AgentTaskStatus.IN_PROGRESS]))
    ).scalar() or 0
    
    # Completed tasks (all time)
    completed_tasks = session.execute(
        select(func.count(AgentTask.id))
        .where(AgentTask.status == AgentTaskStatus.COMPLETED)
    ).scalar() or 0
    
    # Calculate average response time from completed tasks in the last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_completed_tasks = session.execute(
        select(AgentTask)
        .where(and_(
            AgentTask.status == AgentTaskStatus.COMPLETED,
            AgentTask.updated_at >= yesterday
        ))
    ).scalars().all()
    
    avg_response_time = 0.0
    if recent_completed_tasks:
        total_response_time = sum(
            (task.updated_at - task.created_at).total_seconds() 
            for task in recent_completed_tasks
        )
        avg_response_time = total_response_time / len(recent_completed_tasks)
    
    return {
        "total_users": total_users,
        "active_emergencies": active_emergencies,
        "completed_tasks": completed_tasks,
        "average_response_time": round(avg_response_time, 1)
    }


def get_active_queue(session: Session, limit: int = 20) -> List[Dict[str, Any]]:
    """Get active tasks in the queue."""
    tasks = session.execute(
        select(AgentTask)
        .where(AgentTask.status.in_([AgentTaskStatus.PENDING, AgentTaskStatus.IN_PROGRESS]))
        .order_by(AgentTask.priority.asc(), AgentTask.created_at.desc())
        .limit(limit)
    ).scalars().all()
    
    result = []
    for task in tasks:
        # Extract user location from payload if available
        user_location = "Unknown"
        if task.payload and "user_location" in task.payload:
            user_location = task.payload["user_location"]
        
        result.append({
            "id": task.id,
            "trace_id": task.trace_id,
            "service": task.service.value,
            "priority": task.priority,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "user_location": user_location,
            "payload": task.payload
        })
    
    return result


def get_recent_activity(session: Session, limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent system activity."""
    
    # Get recent service events
    events = session.execute(
        select(ServiceEvent)
        .order_by(ServiceEvent.created_at.desc())
        .limit(limit // 2)
    ).scalars().all()
    
    # Get recent completed tasks
    tasks = session.execute(
        select(AgentTask)
        .where(AgentTask.status == AgentTaskStatus.COMPLETED)
        .order_by(AgentTask.updated_at.desc())
        .limit(limit // 2)
    ).scalars().all()
    
    # Get recent user registrations
    users = session.execute(
        select(User)
        .order_by(User.created_at.desc())
        .limit(10)
    ).scalars().all()
    
    activities = []
    
    # Add service events
    for event in events:
        activities.append({
            "type": event.service.value,
            "message": f"{event.service.value.upper()} event: {event.title}",
            "timestamp": event.created_at.isoformat(),
            "details": event.details
        })
    
    # Add completed tasks
    for task in tasks:
        activities.append({
            "type": task.service.value,
            "message": f"{task.service.value.upper()} task completed (Priority {task.priority})",
            "timestamp": task.updated_at.isoformat(),
            "trace_id": task.trace_id
        })
    
    # Add new users
    for user in users:
        activities.append({
            "type": "user",
            "message": f"New user registered: {user.name}",
            "timestamp": user.created_at.isoformat(),
            "location": f"{user.city}" if user.city else "Unknown location"
        })
    
    # Sort all activities by timestamp
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return activities[:limit]


def get_service_distribution(session: Session, hours: int = 24) -> Dict[str, int]:
    """Get service distribution for the last N hours."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Count tasks by service type
    service_counts = session.execute(
        select(AgentTask.service, func.count(AgentTask.id))
        .where(AgentTask.created_at >= since)
        .group_by(AgentTask.service)
    ).all()
    
    # Convert to dictionary with service names
    distribution = {}
    for service, count in service_counts:
        distribution[service.value] = count
    
    # Ensure all service types are represented
    for service_type in ServiceType:
        if service_type.value not in distribution:
            distribution[service_type.value] = 0
    
    return distribution


def get_dispatch_locations(session: Session, hours: int = 24) -> List[Dict[str, Any]]:
    """Get dispatch locations with coordinates for map visualization."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Join tasks with users to get location data
    dispatches = session.execute(
        select(AgentTask, User)
        .join(User, AgentTask.user_id == User.user_id)
        .where(and_(
            AgentTask.created_at >= since,
            User.lat.isnot(None),
            User.lon.isnot(None),
            AgentTask.service_type != ServiceType.GENERAL
        ))
        .order_by(AgentTask.created_at.desc())
    ).all()
    
    locations = []
    for task, user in dispatches:
        locations.append({
            "id": task.id,
            "latitude": float(user.lat),
            "longitude": float(user.lon),
            "service": task.service_type.value,
            "priority": task.priority,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "user_name": user.name,
            "city": user.city or "Unknown",
            "trace_id": task.trace_id,
            "is_active": task.status in [AgentTaskStatus.PENDING, AgentTaskStatus.IN_PROGRESS]
        })
    
    return locations