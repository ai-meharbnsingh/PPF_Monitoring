"""
Module: alerts.py
Purpose:
    Alert listing, acknowledgement, and AlertConfig management routes.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    get_owner_or_admin,
    require_workshop_access,
)
from src.config.database import get_db
from src.models.alert import Alert, AlertConfig
from src.models.user import User
from src.schemas.alert import (
    AlertAcknowledgeRequest,
    AlertConfigResponse,
    AlertConfigUpdate,
    AlertResponse,
)
from src.schemas.common import SuccessResponse, build_paginated
from src.utils.constants import UserRole
from src.utils.logger import get_logger

router = APIRouter(tags=["alerts"])
logger = get_logger(__name__)


# ─── List alerts for a workshop ───────────────────────────────────────────────
@router.get("/workshops/{workshop_id}/alerts", response_model=dict)
async def list_alerts(
    workshop_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    unacknowledged_only: bool = Query(default=False),
    pit_id: Optional[int] = Query(default=None),
    from_dt: Optional[datetime] = Query(default=None),
    to_dt: Optional[datetime] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_workshop_access()),
):
    """List alerts for a workshop, newest first. Filterable by pit, time, ack status."""
    from sqlalchemy import func
    base_q = select(Alert).where(Alert.workshop_id == workshop_id)
    if unacknowledged_only:
        base_q = base_q.where(Alert.is_acknowledged.is_(False))
    if pit_id is not None:
        base_q = base_q.where(Alert.pit_id == pit_id)
    if from_dt:
        base_q = base_q.where(Alert.created_at >= from_dt)
    if to_dt:
        base_q = base_q.where(Alert.created_at <= to_dt)

    count_result = await db.execute(select(func.count()).select_from(base_q.subquery()))
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        base_q.order_by(Alert.created_at.desc()).offset(offset).limit(page_size)
    )
    alerts = result.scalars().all()
    items = [AlertResponse.model_validate(a).model_dump() for a in alerts]
    return build_paginated(items=items, total=total, page=page, page_size=page_size)


# ─── Get single alert ─────────────────────────────────────────────────────────
@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_workshop_access()),
):
    """Get a single alert detail."""
    alert = await db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != alert.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return AlertResponse.model_validate(alert)


# ─── Acknowledge an alert ─────────────────────────────────────────────────────
@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    payload: AlertAcknowledgeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_workshop_access()),
):
    """Mark an alert as acknowledged."""
    alert = await db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != alert.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if alert.is_acknowledged:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Alert already acknowledged"
        )

    alert.is_acknowledged = True
    alert.acknowledged_by_user_id = current_user.id
    alert.acknowledged_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(alert)
    logger.info(f"Alert acknowledged: id={alert_id} by user_id={current_user.id}")
    return AlertResponse.model_validate(alert)


# ─── Bulk acknowledge ─────────────────────────────────────────────────────────
@router.post("/workshops/{workshop_id}/alerts/acknowledge-all", response_model=SuccessResponse)
async def acknowledge_all_alerts(
    workshop_id: int,
    pit_id: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """Acknowledge all unacknowledged alerts for a workshop (optionally scoped to a pit)."""
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    query = select(Alert).where(
        Alert.workshop_id == workshop_id,
        Alert.is_acknowledged.is_(False),
    )
    if pit_id is not None:
        query = query.where(Alert.pit_id == pit_id)

    result = await db.execute(query)
    alerts = result.scalars().all()
    now = datetime.now(tz=timezone.utc)
    for a in alerts:
        a.is_acknowledged = True
        a.acknowledged_by_user_id = current_user.id
        a.acknowledged_at = now

    await db.commit()
    logger.info(
        f"Bulk acknowledge: workshop_id={workshop_id} count={len(alerts)} "
        f"by user_id={current_user.id}"
    )
    return SuccessResponse(message=f"{len(alerts)} alert(s) acknowledged")


# ─── Alert config: get ────────────────────────────────────────────────────────
@router.get("/workshops/{workshop_id}/alert-config", response_model=AlertConfigResponse)
async def get_alert_config(
    workshop_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_workshop_access()),
):
    """Get per-workshop alert threshold configuration."""
    result = await db.execute(
        select(AlertConfig).where(AlertConfig.workshop_id == workshop_id)
    )
    cfg = result.scalar_one_or_none()
    if cfg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert config not found. Create the workshop first.",
        )
    return AlertConfigResponse.model_validate(cfg)


# ─── Alert config: update ─────────────────────────────────────────────────────
@router.patch("/workshops/{workshop_id}/alert-config", response_model=AlertConfigResponse)
async def update_alert_config(
    workshop_id: int,
    payload: AlertConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """Update alert thresholds. owner or super_admin."""
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    result = await db.execute(
        select(AlertConfig).where(AlertConfig.workshop_id == workshop_id)
    )
    cfg = result.scalar_one_or_none()
    if cfg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert config not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cfg, field, value)

    await db.commit()
    await db.refresh(cfg)
    logger.info(f"AlertConfig updated: workshop_id={workshop_id}")
    return AlertConfigResponse.model_validate(cfg)
