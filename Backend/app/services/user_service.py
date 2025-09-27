"""User service helpers for registration and lookup."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User
from app.models.user import UserRegistrationRequest
from app.services.auth import hash_password, verify_password


class UserConflictError(Exception):
    """Raised when attempting to register a user with conflicting unique fields."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        super().__init__(message)


class UserNotFoundError(Exception):
    """Raised when a requested user cannot be found."""


def _ensure_unique(
    session: Session,
    *,
    field: str,
    value: Optional[str],
    exclude_id: Optional[int],
) -> None:
    if not value:
        return
    column = getattr(User, field)
    stmt = select(User).where(column == value)
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    if session.execute(stmt).scalar_one_or_none() is not None:
        raise UserConflictError(field, f"{field} already registered")


def get_user_by_user_id(session: Session, user_id: str) -> User:
    user = session.execute(select(User).where(User.user_id == user_id)).scalar_one_or_none()
    if user is None:
        raise UserNotFoundError(f"user with id '{user_id}' not found")
    return user


def register_user(session: Session, payload: UserRegistrationRequest) -> tuple[User, bool]:
    explicit_user_id = payload.user_id
    existing_user = None
    if explicit_user_id:
        existing_user = session.execute(select(User).where(User.user_id == explicit_user_id)).scalar_one_or_none()

    exclude_id = existing_user.id if existing_user else None
    _ensure_unique(session, field="cnic", value=payload.cnic, exclude_id=exclude_id)
    _ensure_unique(session, field="email", value=payload.email, exclude_id=exclude_id)

    data = payload.model_dump(exclude_none=True)
    data.pop("user_id", None)
    raw_password = data.pop("password")
    salt, password_hash = hash_password(raw_password)
    data["password_salt"] = salt
    data["password_hash"] = password_hash

    if existing_user:
        for key, value in data.items():
            setattr(existing_user, key, value)
        existing_user.last_login_at = datetime.utcnow()
        session.flush()
        session.refresh(existing_user)
        return existing_user, False

    if explicit_user_id:
        user = User(user_id=explicit_user_id, **data)
    else:
        user = User(**data)
    session.add(user)
    session.flush()
    session.refresh(user)
    return user, True


def authenticate_user(session: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    user = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user and verify_password(password, user.password_salt, user.password_hash):
        user.last_login_at = datetime.utcnow()
        session.flush()
        return user
    return None


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    """Get a user by their email address."""
    return session.execute(select(User).where(User.email == email)).scalar_one_or_none()
