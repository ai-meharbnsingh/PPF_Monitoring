"""
Module: auth.py
Purpose:
    Pydantic schemas for authentication endpoints.
    Login, token refresh, profile, password change.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ─── Requests ─────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    """POST /auth/login"""

    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    """POST /auth/change-password"""

    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class TokenRefreshRequest(BaseModel):
    """POST /auth/refresh-token"""

    token: str = Field(..., min_length=10)


# ─── Responses ────────────────────────────────────────────────────────────────
class UserProfileResponse(BaseModel):
    """Embedded in LoginResponse and returned by GET /auth/me"""

    id: int
    username: str
    email: Optional[str]
    phone: Optional[str]
    role: str
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: str
    workshop_id: Optional[int]
    is_active: bool
    is_temporary_password: bool
    last_login: Optional[datetime]

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """POST /auth/login success response."""

    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user: UserProfileResponse
    success: bool = True


class TokenRefreshResponse(BaseModel):
    """POST /auth/refresh-token success response."""

    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    success: bool = True
