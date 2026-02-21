"""
Module: subscriptions.py
Purpose:
    Subscription management routes (super_admin focused).
    Create/update subscriptions, record payments, view license status.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_owner_or_admin, get_super_admin, require_workshop_access
from src.config.database import get_db
from src.models.subscription import Subscription
from src.models.user import User
from src.schemas.common import build_paginated
from src.schemas.subscription import (
    RecordPayment,
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionSummary,
    SubscriptionUpdate,
)
from src.utils.constants import SubscriptionPlan, SubscriptionStatus, UserRole
from src.utils.helpers import generate_license_key
from src.utils.logger import get_logger

router = APIRouter(tags=["subscriptions"])
logger = get_logger(__name__)


# ─── List subscriptions for a workshop ────────────────────────────────────────
@router.get("/workshops/{workshop_id}/subscriptions", response_model=dict)
async def list_subscriptions(
    workshop_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_workshop_access()),
):
    """List all subscriptions/licenses for a workshop."""
    from sqlalchemy import func
    base_q = select(Subscription).where(Subscription.workshop_id == workshop_id)
    count_result = await db.execute(select(func.count()).select_from(base_q.subquery()))
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        base_q.order_by(Subscription.created_at.desc()).offset(offset).limit(page_size)
    )
    subs = result.scalars().all()
    items = [SubscriptionSummary.model_validate(s).model_dump() for s in subs]
    return build_paginated(items=items, total=total, page=page, page_size=page_size)


# ─── Create subscription (super_admin) ────────────────────────────────────────
@router.post(
    "/workshops/{workshop_id}/subscriptions",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription(
    workshop_id: int,
    payload: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    """Create a new subscription for a device. super_admin only."""
    from src.config.settings import get_settings
    settings = get_settings()

    now = datetime.now(tz=timezone.utc)
    trial_expires = now + timedelta(days=settings.TRIAL_DAYS)

    # Unique license key
    key = generate_license_key()
    while True:
        existing = await db.execute(select(Subscription).where(Subscription.license_key == key))
        if existing.scalar_one_or_none() is None:
            break
        key = generate_license_key()

    fee = payload.monthly_fee
    if fee is None:
        from src.utils.constants import PLAN_MONTHLY_FEES_INR
        fee = PLAN_MONTHLY_FEES_INR.get(payload.plan, 0)

    sub = Subscription(
        workshop_id=workshop_id,
        device_id=payload.device_id,
        license_key=key,
        plan=payload.plan.value,
        status=SubscriptionStatus.ACTIVE.value,
        monthly_fee=fee,
        currency=payload.currency,
        starts_at=now,
        trial_expires_at=trial_expires,
        grace_period_days=payload.grace_period_days,
        notes=payload.notes,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    logger.info(
        f"Subscription created: id={sub.id} device_id='{payload.device_id}' "
        f"workshop_id={workshop_id} plan={payload.plan.value}"
    )
    return SubscriptionResponse.model_validate(sub)


# ─── Get single subscription ──────────────────────────────────────────────────
@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """Get subscription detail."""
    sub = await db.get(Subscription, subscription_id)
    if sub is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != sub.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return SubscriptionResponse.model_validate(sub)


# ─── Update subscription (super_admin) ────────────────────────────────────────
@router.patch("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    payload: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    """Update subscription plan/status/expiry. super_admin only."""
    sub = await db.get(Subscription, subscription_id)
    if sub is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if hasattr(value, "value"):
            setattr(sub, field, value.value)
        else:
            setattr(sub, field, value)

    await db.commit()
    await db.refresh(sub)
    logger.info(f"Subscription updated: id={subscription_id}")
    return SubscriptionResponse.model_validate(sub)


# ─── Record payment ───────────────────────────────────────────────────────────
@router.post("/subscriptions/{subscription_id}/record-payment", response_model=SubscriptionResponse)
async def record_payment(
    subscription_id: int,
    payload: RecordPayment,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    """Record a payment and extend subscription expiry. super_admin only."""
    sub = await db.get(Subscription, subscription_id)
    if sub is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    now = datetime.now(tz=timezone.utc)
    base_date = sub.expires_at or now
    if base_date < now:
        base_date = now  # expired — restart from today

    sub.expires_at = base_date + timedelta(days=30 * payload.extend_months)
    sub.last_payment_date = now
    sub.next_payment_date = sub.expires_at - timedelta(days=sub.grace_period_days)
    sub.payment_method = payload.payment_method
    sub.payment_reference = payload.payment_reference
    sub.status = SubscriptionStatus.ACTIVE.value

    # Re-enable the linked device if it was suspended
    if sub.device_id:
        from src.models.device import Device
        from src.utils.constants import DeviceStatus
        device = await db.execute(
            select(Device).where(Device.device_id == sub.device_id)
        )
        device = device.scalar_one_or_none()
        if device and device.status == DeviceStatus.SUSPENDED.value:
            device.status = DeviceStatus.ACTIVE.value
            logger.info(f"Device re-enabled after payment: device_id='{sub.device_id}'")

    await db.commit()
    await db.refresh(sub)
    logger.info(
        f"Payment recorded: subscription_id={subscription_id} "
        f"amount={payload.amount} {payload.currency} "
        f"new_expiry={sub.expires_at}"
    )
    return SubscriptionResponse.model_validate(sub)
