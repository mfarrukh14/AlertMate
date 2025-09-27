"""Database setup and session management for AlertMate."""

from __future__ import annotations

import contextlib
from typing import Generator

from sqlalchemy import create_engine, inspect
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
    _apply_sqlite_migrations()


def _apply_sqlite_migrations() -> None:
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("users")}
    statements = []
    if "password_salt" not in columns:
        statements.append("ALTER TABLE users ADD COLUMN password_salt VARCHAR(64)")
    if "password_hash" not in columns:
        statements.append("ALTER TABLE users ADD COLUMN password_hash VARCHAR(256)")
    if "lat" not in columns:
        statements.append("ALTER TABLE users ADD COLUMN lat FLOAT")
    if "lon" not in columns:
        statements.append("ALTER TABLE users ADD COLUMN lon FLOAT")
    if "last_login_at" not in columns:
        statements.append("ALTER TABLE users ADD COLUMN last_login_at DATETIME")
    if "email" not in columns:
        statements.append("ALTER TABLE users ADD COLUMN email VARCHAR(120)")

    if statements:
        with engine.begin() as connection:
            for statement in statements:
                connection.exec_driver_sql(statement)
            connection.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)"
            )


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
