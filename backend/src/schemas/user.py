"""
Module: user.py
Purpose:
    Pydantic schemas for user management endpoints.
    UserCreate (owner/staff/customer), UserUpdate, UserResponse.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.utils.constants import UserRole


# ─── Requests ─────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    """
    POST /users — create owner / staff.
    Customer accounts are auto-created from JobCreate.customer_name.
    """

    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = Field(..., description="owner | staff (not super_admin or customer here)")
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    workshop_id: Optional[int] = Field(
        None,
        description="Required when super_admin creates an owner for a specific workshop",
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: UserRole) -> UserRole:
        if v in (UserRole.SUPER_ADMIN, UserRole.CUSTOMER):
            raise ValueError("Cannot directly create super_admin or customer users via this endpoint")
        return v

    @field_validator("username")
    @classmethod
    def lowercase_username(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """PATCH /users/{user_id}"""

    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class AdminResetPassword(BaseModel):
    """POST /users/{user_id}/reset-password (owner/admin only)"""

    new_password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=128,
        description="Leave empty to auto-generate a temporary password",
    )


# ─── Responses ────────────────────────────────────────────────────────────────
class UserSummary(BaseModel):
    """Lightweight user row for list responses."""

    id: int
    username: str
    full_name: str
    role: str
    email: Optional[str]
    phone: Optional[str]
    is_active: bool
    last_login: Optional[datetime]

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    """Full user detail."""

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
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerCreateResponse(BaseModel):
    """Returned when a customer account is auto-created during job creation."""

    user_id: int
    username: str
    temporary_password: str
    message: str = "Customer account created. Share credentials with the customer."
