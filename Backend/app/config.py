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

# Google Cloud Platform API Keys
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GOOGLE_GEOCODING_API_KEY = os.getenv("GOOGLE_GEOCODING_API_KEY")

# Service Discovery Configuration
SERVICE_DISCOVERY_CACHE_TTL = int(os.getenv("SERVICE_DISCOVERY_CACHE_TTL", "3600"))  # 1 hour
MAX_SEARCH_RADIUS_KM = int(os.getenv("MAX_SEARCH_RADIUS_KM", "50"))
DEFAULT_SEARCH_RADIUS_KM = int(os.getenv("DEFAULT_SEARCH_RADIUS_KM", "25"))

# Emergency Services Configuration
EMERGENCY_SERVICES_ENABLED = os.getenv("EMERGENCY_SERVICES_ENABLED", "true").lower() == "true"
FALLBACK_TO_HARDCODED = os.getenv("FALLBACK_TO_HARDCODED", "true").lower() == "true"