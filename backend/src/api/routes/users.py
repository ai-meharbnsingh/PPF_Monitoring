"""
Module: users.py
Purpose:
    User management API routes.
    Create/read/update staff and owner accounts.
    Password reset by admin.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    get_current_user,
    get_owner_or_admin,
    require_workshop_access,
)
from src.config.database import get_db
from src.models.user import User
from src.schemas.common import SuccessResponse, build_paginated
from src.schemas.user import AdminResetPassword, UserCreate, UserResponse, UserSummary, UserUpdate
from src.services.auth_service import hash_password, validate_password_strength
from src.utils.constants import UserRole
from src.utils.helpers import generate_temporary_password
from src.utils.logger import get_logger

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger(__name__)


# ─── List users for a workshop ────────────────────────────────────────────────
@router.get("", response_model=dict)
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    workshop_id: int = Query(default=None, description="Filter by workshop (omit for super_admin to see all)"),
    role: str = Query(default=None, description="Filter by role"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """List users for a workshop. owner sees own workshop; super_admin sees any or all."""
    from sqlalchemy import func
    
    # Build base query
    if workshop_id is not None:
        # Specific workshop requested
        if (
            current_user.role != UserRole.SUPER_ADMIN.value
            and current_user.workshop_id != workshop_id
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        base_q = select(User).where(User.workshop_id == workshop_id)
    else:
        # No workshop specified - only super_admin can see all
        if current_user.role != UserRole.SUPER_ADMIN.value:
            # Regular users see their own workshop
            base_q = select(User).where(User.workshop_id == current_user.workshop_id)
        else:
            # Super admin sees all users
            base_q = select(User)
    
    if role:
        base_q = base_q.where(User.role == role)

    count_result = await db.execute(select(func.count()).select_from(base_q.subquery()))
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        base_q.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = result.scalars().all()
    items = [UserSummary.model_validate(u).model_dump() for u in users]
    return build_paginated(items=items, total=total, page=page, page_size=page_size)


# ─── Create user (owner or super_admin) ──────────────────────────────────────
@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """Create staff/owner user. super_admin can create owners; owner creates staff only."""
    # owner can only create staff for own workshop
    if current_user.role == UserRole.OWNER.value:
        if payload.role != UserRole.STAFF:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owners can only create staff accounts",
            )
        payload_workshop_id = current_user.workshop_id
    else:
        # super_admin
        payload_workshop_id = payload.workshop_id
        if payload_workshop_id is None and payload.role == UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="workshop_id is required when creating an owner",
            )

    # Check username uniqueness
    existing = await db.execute(select(User).where(User.username == payload.username))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{payload.username}' is already taken",
        )

    if payload.email:
        existing_email = await db.execute(select(User).where(User.email == payload.email))
        if existing_email.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{payload.email}' is already registered",
            )

    user = User(
        workshop_id=payload_workshop_id,
        username=payload.username,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=payload.role.value,
        first_name=payload.first_name,
        last_name=payload.last_name,
        is_active=True,
        is_temporary_password=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info(f"User created: username='{user.username}' role={user.role}")
    return UserResponse.model_validate(user)


# ─── Get single user ──────────────────────────────────────────────────────────
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user profile. Users can see themselves; owner sees own workshop users."""
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Allow self-view or workshop-scoped view
    if current_user.id != user_id:
        if current_user.role == UserRole.SUPER_ADMIN.value:
            pass  # can see all
        elif current_user.role in (UserRole.OWNER.value, UserRole.STAFF.value):
            if current_user.workshop_id != user.workshop_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return UserResponse.model_validate(user)


# ─── Update user ──────────────────────────────────────────────────────────────
@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user profile. Users can update self; owner can update own workshop users."""
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Permission check
    can_edit = (
        current_user.id == user_id
        or current_user.role == UserRole.SUPER_ADMIN.value
        or (
            current_user.role == UserRole.OWNER.value
            and current_user.workshop_id == user.workshop_id
        )
    )
    if not can_edit:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Only super_admin/owner can toggle is_active
    if payload.is_active is not None and current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot change your own active status",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    logger.info(f"User updated: id={user_id}")
    return UserResponse.model_validate(user)


# ─── Reset password (admin action) ───────────────────────────────────────────
@router.post("/{user_id}/reset-password", response_model=dict)
async def reset_user_password(
    user_id: int,
    payload: AdminResetPassword,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """Reset a user's password. owner can reset own staff; super_admin resets any."""
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != user.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    new_password = payload.new_password or generate_temporary_password()
    user.password_hash = hash_password(new_password)
    user.is_temporary_password = True
    await db.commit()

    logger.warning(f"Password reset: user_id={user_id} by user_id={current_user.id}")
    return {
        "user_id": user_id,
        "temporary_password": new_password if not payload.new_password else None,
        "message": "Password reset successfully. User must change password on next login.",
    }


# ─── Deactivate user ──────────────────────────────────────────────────────────
@router.delete("/{user_id}", response_model=SuccessResponse)
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """Deactivate a user account (soft-delete)."""
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account",
        )
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != user.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    user.is_active = False
    await db.commit()
    logger.warning(f"User deactivated: id={user_id} by user_id={current_user.id}")
    return SuccessResponse(message=f"User '{user.username}' deactivated")
