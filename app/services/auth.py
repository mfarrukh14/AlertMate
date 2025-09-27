"""Authentication helpers for password hashing and verification."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Tuple

PBKDF2_ITERATIONS = 390_000


def hash_password(password: str) -> Tuple[str, str]:
    """Generate a random salt and hashed password using PBKDF2."""
    salt = secrets.token_hex(16)
    salt_bytes = bytes.fromhex(salt)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, PBKDF2_ITERATIONS)
    return salt, dk.hex()


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    """Verify a provided password using the stored salt and hash."""
    try:
        salt_bytes = bytes.fromhex(salt)
        expected = bytes.fromhex(password_hash)
    except ValueError:
        return False

    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, PBKDF2_ITERATIONS)
    return hmac.compare_digest(candidate, expected)
