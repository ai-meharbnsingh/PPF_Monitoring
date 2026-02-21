"""
Module: workshops.py
Purpose:
    Workshop CRUD API routes.
    super_admin: full CRUD + list all workshops.
    owner: read/update own workshop only.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    get_owner_or_admin,
    get_super_admin,
    require_workshop_access,
)
from src.config.database import get_db
from src.models.user import User
from src.schemas.common import SuccessResponse, build_paginated
from src.schemas.workshop import WorkshopCreate, WorkshopResponse, WorkshopSummary, WorkshopUpdate
from src.services import workshop_service
from src.utils.logger import get_logger

router = APIRouter(prefix="/workshops", tags=["workshops"])
logger = get_logger(__name__)


# ─── List all workshops (super_admin only) ────────────────────────────────────
@router.get("", response_model=dict)
async def list_workshops(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    active_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    """List all workshops with pagination. super_admin only."""
    workshops, total = await workshop_service.list_workshops(
        db, page=page, page_size=page_size, active_only=active_only
    )
    items = [WorkshopSummary.model_validate(w).model_dump() for w in workshops]
    return build_paginated(items=items, total=total, page=page, page_size=page_size)


# ─── Create workshop (super_admin only) ───────────────────────────────────────
@router.post("", response_model=WorkshopResponse, status_code=status.HTTP_201_CREATED)
async def create_workshop(
    payload: WorkshopCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    """Create a new workshop. super_admin only."""
    workshop = await workshop_service.create_workshop(db, payload)
    return WorkshopResponse.model_validate(workshop)


# ─── Get single workshop ──────────────────────────────────────────────────────
@router.get("/{workshop_id}", response_model=WorkshopResponse)
async def get_workshop(
    workshop_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_workshop_access()),
):
    """Get workshop details. owner sees own; super_admin sees any."""
    workshop = await workshop_service.get_workshop_by_id(db, workshop_id)
    if workshop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workshop not found")
    return WorkshopResponse.model_validate(workshop)


# ─── Update workshop ──────────────────────────────────────────────────────────
@router.patch("/{workshop_id}", response_model=WorkshopResponse)
async def update_workshop(
    workshop_id: int,
    payload: WorkshopUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """Update workshop fields. owner updates own; super_admin updates any."""
    from src.utils.constants import UserRole
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != workshop_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own workshop",
        )
    workshop = await workshop_service.get_workshop_by_id(db, workshop_id)
    if workshop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workshop not found")
    updated = await workshop_service.update_workshop(db, workshop, payload)
    return WorkshopResponse.model_validate(updated)


# ─── Deactivate workshop (super_admin) ────────────────────────────────────────
@router.delete("/{workshop_id}", response_model=SuccessResponse)
async def deactivate_workshop(
    workshop_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    """Soft-delete a workshop. super_admin only."""
    workshop = await workshop_service.get_workshop_by_id(db, workshop_id)
    if workshop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workshop not found")
    await workshop_service.deactivate_workshop(db, workshop)
    return SuccessResponse(message=f"Workshop '{workshop.name}' deactivated")
