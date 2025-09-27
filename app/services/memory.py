"""Conversation memory helpers backed by the database."""

from __future__ import annotations

from typing import List, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ConversationMessage, ConversationRole, User


def ensure_user(session: Session, user_id: str) -> User:
    """Fetch a user by ID or raise if they do not exist."""
    user = session.execute(
        select(User).where(User.user_id == user_id)
    ).scalar_one_or_none()
    if user is None:
        raise ValueError("User session not found. Please sign in again.")
    return user


def get_recent_messages(session: Session, user_id: str, limit: int = 12) -> List[dict]:
    """Return the most recent messages for the user ordered oldest -> newest."""
    rows: Sequence[ConversationMessage] = (
        session.execute(
            select(ConversationMessage)
            .where(ConversationMessage.user_id == user_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [
        {
            "role": message.role.value,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
        }
        for message in reversed(rows)
    ]


def record_message(
    session: Session,
    user_id: str,
    role: ConversationRole,
    content: str,
    max_messages: int = 12,
) -> None:
    """Persist a conversation message and trim history to the configured window."""
    ensure_user(session, user_id)
    message = ConversationMessage(user_id=user_id, role=role, content=content)
    session.add(message)
    session.flush()

    ids_to_prune = (
        session.execute(
            select(ConversationMessage.id)
            .where(ConversationMessage.user_id == user_id)
            .order_by(ConversationMessage.created_at.desc())
            .offset(max_messages)
        )
        .scalars()
        .all()
    )
    if ids_to_prune:
        session.query(ConversationMessage).filter(ConversationMessage.id.in_(ids_to_prune)).delete(
            synchronize_session=False
        )

