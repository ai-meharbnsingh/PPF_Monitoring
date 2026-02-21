"""
Module: admin.py
Purpose:
    Super-admin only utility routes.
    Seed super_admin account, system info, audit logs.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_super_admin
from src.config.database import get_db
from src.config.settings import get_settings
from src.models.audit_log import AuditLog
from src.models.user import User
from src.schemas.common import SuccessResponse, build_paginated
from src.utils.constants import UserRole
from src.utils.logger import get_logger

router = APIRouter(prefix="/admin", tags=["admin"])
logger = get_logger(__name__)


# ─── Seed super admin (first-run only) ───────────────────────────────────────
@router.post("/seed-super-admin", response_model=SuccessResponse)
async def seed_super_admin(
    db: AsyncSession = Depends(get_db),
):
    """
    Create the super_admin account on first run.
    Credentials come from .env (SUPER_ADMIN_USERNAME / SUPER_ADMIN_PASSWORD).
    Returns 409 if the account already exists.
    No auth required — must be called once during setup.
    """
    settings = get_settings()

    existing = await db.execute(
        select(User).where(User.username == settings.SUPER_ADMIN_USERNAME)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"super_admin account '{settings.SUPER_ADMIN_USERNAME}' already exists",
        )

    from src.services.auth_service import hash_password

    admin = User(
        username=settings.SUPER_ADMIN_USERNAME,
        email=settings.SUPER_ADMIN_EMAIL,
        password_hash=hash_password(settings.SUPER_ADMIN_PASSWORD),
        role=UserRole.SUPER_ADMIN.value,
        is_active=True,
        is_temporary_password=False,
    )
    db.add(admin)
    await db.commit()
    logger.info(f"Super admin seeded: username='{settings.SUPER_ADMIN_USERNAME}'")
    return SuccessResponse(
        message=f"Super admin account '{settings.SUPER_ADMIN_USERNAME}' created successfully"
    )


# ─── System info (super_admin) ────────────────────────────────────────────────
@router.get("/system-info")
async def system_info(
    current_user: User = Depends(get_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """System metadata snapshot for admin dashboard."""
    settings = get_settings()

    from src.models.workshop import Workshop
    from src.models.device import Device
    from src.models.job import Job
    from sqlalchemy import func

    workshop_count = (await db.execute(select(func.count(Workshop.id)))).scalar_one()
    device_count = (await db.execute(select(func.count(Device.id)))).scalar_one()
    online_device_count = (
        await db.execute(select(func.count(Device.id)).where(Device.is_online.is_(True)))
    ).scalar_one()
    job_count = (await db.execute(select(func.count(Job.id)))).scalar_one()
    user_count = (await db.execute(select(func.count(User.id)))).scalar_one()

    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "workshop_count": workshop_count,
        "device_count": device_count,
        "online_device_count": online_device_count,
        "job_count": job_count,
        "user_count": user_count,
        "features": {
            "sms_enabled": settings.sms_enabled,
            "email_enabled": settings.email_enabled,
        },
    }


# ─── Audit logs (super_admin) ─────────────────────────────────────────────────
@router.get("/audit-logs", response_model=dict)
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    workshop_id: int = Query(default=None),
    action_prefix: str = Query(default=None, description="e.g. 'user.' or 'job.'"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    """Paginated audit log. super_admin only."""
    from sqlalchemy import func

    base_q = select(AuditLog)
    if workshop_id is not None:
        base_q = base_q.where(AuditLog.workshop_id == workshop_id)
    if action_prefix:
        base_q = base_q.where(AuditLog.action.like(f"{action_prefix}%"))

    count_result = await db.execute(select(func.count()).select_from(base_q.subquery()))
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        base_q.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
    )
    logs = result.scalars().all()
    items = [
        {
            "id": log.id,
            "workshop_id": log.workshop_id,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "ip_address": log.ip_address,
            "created_at": log.created_at,
        }
        for log in logs
    ]
    return build_paginated(items=items, total=total, page=page, page_size=page_size)
