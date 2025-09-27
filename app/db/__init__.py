"""Database setup and session management for AlertMate."""

from __future__ import annotations

import contextlib
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import DATABASE_URL

url = make_url(DATABASE_URL) if isinstance(DATABASE_URL, str) else DATABASE_URL

connect_args = {"check_same_thread": False} if url.get_backend_name() == "sqlite" else {}

engine = create_engine(url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency to provide a scoped database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Create database tables if they do not exist."""
    # Import models to ensure they are registered with SQLAlchemy metadata.
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


@contextlib.contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope for scripts and background jobs."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:  # pragma: no cover - defensive
        session.rollback()
        raise
    finally:
        session.close()
