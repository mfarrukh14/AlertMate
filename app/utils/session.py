"""Session management utilities for user authentication."""

from __future__ import annotations

import json
import hashlib
import hmac
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.config import SESSION_SECRET_KEY


def create_session_token(user_id: str, expires_at: datetime) -> str:
    """Create a signed session token containing user ID and expiration."""
    payload = {
        "user_id": user_id,
        "expires_at": expires_at.isoformat(),
    }
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_b64 = payload_json.encode('utf-8').hex()
    
    signature = hmac.new(
        SESSION_SECRET_KEY.encode('utf-8'),
        payload_b64.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"{payload_b64}.{signature}"


def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a session token. Returns None if invalid/expired."""
    try:
        payload_b64, signature = token.split('.', 1)
        
        # Verify signature
        expected_signature = hmac.new(
            SESSION_SECRET_KEY.encode('utf-8'),
            payload_b64.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return None
            
        # Decode payload
        payload_json = bytes.fromhex(payload_b64).decode('utf-8')
        payload = json.loads(payload_json)
        
        # Check expiration
        expires_at = datetime.fromisoformat(payload['expires_at'])
        if datetime.utcnow() > expires_at:
            return None
            
        return payload
        
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


def get_session_expiry() -> datetime:
    """Get the expiration time for a new session."""
    return datetime.utcnow() + timedelta(days=7)  # 7 day sessions