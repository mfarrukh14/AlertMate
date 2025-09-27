"""Application configuration for AlertMate MVP."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "alertmate.log"

DEFAULT_TIMEOUT_SECONDS = 10

load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'alertmate.db'}")
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "change-me-session-secret")
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "alertmate_session")
SESSION_MAX_AGE = int(os.getenv("SESSION_MAX_AGE", "604800"))  # 7 days in seconds
