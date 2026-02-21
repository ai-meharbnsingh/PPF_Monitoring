"""
Module: subscription.py
Purpose:
    Pydantic schemas for subscription management endpoints.
    SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.utils.constants import SubscriptionPlan, SubscriptionStatus


# ─── Requests ─────────────────────────────────────────────────────────────────
class SubscriptionCreate(BaseModel):
    """POST /workshops/{workshop_id}/subscriptions  (super_admin only)"""

    device_id: str = Field(..., max_length=50, description="ESP32 device_id to license")
    plan: SubscriptionPlan = SubscriptionPlan.BASIC
    monthly_fee: Optional[float] = Field(None, ge=0)
    currency: str = Field(default="INR", max_length=3)
    grace_period_days: int = Field(default=7, ge=0, le=90)
    notes: Optional[str] = Field(None, max_length=500)


class SubscriptionUpdate(BaseModel):
    """PATCH /subscriptions/{subscription_id}  (super_admin only)"""

    plan: Optional[SubscriptionPlan] = None
    status: Optional[SubscriptionStatus] = None
    monthly_fee: Optional[float] = Field(None, ge=0)
    expires_at: Optional[datetime] = None
    grace_period_days: Optional[int] = Field(None, ge=0, le=90)
    payment_method: Optional[str] = Field(None, max_length=50)
    payment_reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)


class RecordPayment(BaseModel):
    """POST /subscriptions/{id}/record-payment  (super_admin only)"""

    amount: float = Field(..., gt=0)
    currency: str = Field(default="INR", max_length=3)
    payment_method: str = Field(..., max_length=50)
    payment_reference: Optional[str] = Field(None, max_length=100)
    extend_months: int = Field(default=1, ge=1, le=24)


# ─── Responses ────────────────────────────────────────────────────────────────
class SubscriptionSummary(BaseModel):
    """Lightweight subscription row for list responses."""

    id: int
    workshop_id: int
    device_id: Optional[str]
    license_key: str
    plan: str
    status: str
    expires_at: Optional[datetime]

    model_config = {"from_attributes": True}


class SubscriptionResponse(BaseModel):
    """Full subscription detail."""

    id: int
    workshop_id: int
    device_id: Optional[str]
    license_key: str
    plan: str
    status: str
    monthly_fee: Optional[float]
    currency: str

    starts_at: Optional[datetime]
    expires_at: Optional[datetime]
    trial_expires_at: Optional[datetime]
    grace_period_days: int

    last_payment_date: Optional[datetime]
    next_payment_date: Optional[datetime]
    payment_method: Optional[str]
    payment_reference: Optional[str]
    notes: Optional[str]

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
