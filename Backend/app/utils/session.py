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
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Verifying token: {token[:50]}...")
        payload_b64, signature = token.split('.', 1)
        logger.info(f"Payload part: {payload_b64[:20]}..., Signature: {signature[:20]}...")
        
        # Verify signature
        expected_signature = hmac.new(
            SESSION_SECRET_KEY.encode('utf-8'),
            payload_b64.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        logger.info(f"Expected signature: {expected_signature[:20]}...")
        logger.info(f"Provided signature: {signature[:20]}...")
        
        if not hmac.compare_digest(signature, expected_signature):
            logger.info("Signature verification failed")
            return None
            
        # Decode payload
        payload_json = bytes.fromhex(payload_b64).decode('utf-8')
        payload = json.loads(payload_json)
        logger.info(f"Decoded payload: {payload}")
        
        # Check expiration
        expires_at = datetime.fromisoformat(payload['expires_at'])
        now = datetime.utcnow()
        logger.info(f"Token expires at: {expires_at}, Current time: {now}")
        
        if now > expires_at:
            logger.info("Token expired")
            return None
            
        logger.info("Token verification successful")
        return payload
        
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        logger.info(f"Token verification failed with error: {e}")
        return None


def get_session_expiry() -> datetime:
    """Get the expiration time for a new session."""
    return datetime.utcnow() + timedelta(days=7)  # 7 day sessions