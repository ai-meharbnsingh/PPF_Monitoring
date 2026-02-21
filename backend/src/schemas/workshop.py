"""
Module: workshop.py
Purpose:
    Pydantic schemas for workshop CRUD endpoints.
    WorkshopCreate, WorkshopUpdate, WorkshopResponse, WorkshopSummary.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ─── Requests ─────────────────────────────────────────────────────────────────
class WorkshopCreate(BaseModel):
    """POST /workshops  (super_admin only)"""

    name: str = Field(..., min_length=2, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    timezone: str = Field(default="Asia/Kolkata", max_length=50)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Workshop name cannot be blank")
        return v


class WorkshopUpdate(BaseModel):
    """PATCH /workshops/{workshop_id}"""

    name: Optional[str] = Field(None, min_length=2, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    timezone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


# ─── Responses ────────────────────────────────────────────────────────────────
class WorkshopSummary(BaseModel):
    """Lightweight row used in list responses."""

    id: int
    name: str
    slug: str
    city: Optional[str]
    state: Optional[str]
    total_pits: int
    subscription_plan: str
    subscription_status: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkshopResponse(BaseModel):
    """Full workshop detail."""

    id: int
    name: str
    slug: str
    owner_user_id: Optional[int]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    total_pits: int
    subscription_plan: str
    subscription_status: str
    subscription_expires_at: Optional[datetime]
    timezone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
