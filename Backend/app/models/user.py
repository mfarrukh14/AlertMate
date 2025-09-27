"""Pydantic schemas for user registration and profiles."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


_BLOOD_GROUPS = {
    "a+",
    "a-",
    "b+",
    "b-",
    "ab+",
    "ab-",
    "o+",
    "o-",
}


class UserRegistrationRequest(BaseModel):
    user_id: Optional[str] = Field(
        default=None,
        description="Optional external identifier. If omitted, the system generates one.",
        min_length=3,
        max_length=64,
    )
    name: str = Field(..., min_length=2, max_length=120)
    blood_group: Optional[str] = Field(
        default=None,
        description="Blood group (e.g. A+, O-)",
        max_length=8,
    )
    address: Optional[str] = Field(default=None, max_length=255)
    cnic: Optional[str] = Field(
        default=None,
        description="13-digit national identity number, optionally formatted as 12345-1234567-1",
        max_length=20,
    )
    phone_number: Optional[str] = Field(default=None, max_length=32)
    emergency_contact_name: Optional[str] = Field(default=None, max_length=120)
    emergency_contact_phone: Optional[str] = Field(default=None, max_length=32)
    date_of_birth: Optional[date] = Field(default=None)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    city: Optional[str] = Field(default=None, max_length=80)

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = value.strip().lower()
        if normalized not in _BLOOD_GROUPS:
            raise ValueError("invalid blood group")
        return normalized.upper()

    @field_validator("cnic")
    @classmethod
    def normalize_cnic(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) != 13:
            raise ValueError("cnic must contain exactly 13 digits")
        return f"{digits[:5]}-{digits[5:12]}-{digits[12:]}"

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if value.strip() != value:
            raise ValueError("password cannot start or end with whitespace")
        if value.lower() == value or value.upper() == value:
            raise ValueError("password must include mixed case characters")
        if not any(ch.isdigit() for ch in value):
            raise ValueError("password must include at least one digit")
        return value


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    name: str
    blood_group: Optional[str]
    address: Optional[str]
    cnic: Optional[str]
    phone_number: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    date_of_birth: Optional[date]
    email: EmailStr
    city: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    last_login_at: Optional[datetime]
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class AuthenticatedUser(BaseModel):
    id: int
    user_id: str
    name: str
    email: EmailStr
    lat: Optional[float]
    lon: Optional[float]
