"""
Module: dependencies.py
Purpose:
    FastAPI dependency injection functions.
    Provides current_user, require_role, require_workshop_access, and DB session.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.models.user import User
from src.services.auth_service import decode_access_token
from src.utils.constants import UserRole
from src.utils.logger import get_logger

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)  # auto_error=False: we raise 401 manually (not 403)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency: decode JWT and return current User ORM instance.

    Raises:
        401 UNAUTHORIZED: If token is invalid, expired, or user doesn't exist
        401 ACCOUNT_DISABLED: If user account is deactivated
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "NOT_AUTHENTICATED", "message": "Authentication required"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_INVALID", "message": str(e)},
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_INVALID", "message": "Token missing user ID"},
        )

    result = await db.execute(select(User).where(User.id == int(user_id_str)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "User no longer exists"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "ACCOUNT_DISABLED", "message": "Account has been deactivated"},
        )

    return user


def require_roles(*allowed_roles: UserRole):
    """
    FastAPI dependency factory: ensure current user has one of the allowed roles.

    Usage in routes:
        @router.get("/admin-only")
        async def admin_route(user = Depends(require_roles(UserRole.SUPER_ADMIN))):
            ...

        @router.get("/owner-or-admin")
        async def owner_route(user = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.OWNER))):
            ...
    """
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in [r.value for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "INSUFFICIENT_PERMISSIONS",
                    "message": f"This action requires one of these roles: "
                               f"{[r.value for r in allowed_roles]}. "
                               f"Your role: {current_user.role}",
                },
            )
        return current_user

    return dependency


def require_workshop_access(workshop_id_param: str = "workshop_id"):
    """
    FastAPI dependency factory: ensure user can access the requested workshop.

    super_admin: can access all workshops
    owner/staff/customer: can only access their own workshop

    Args:
        workshop_id_param: Name of the path parameter that contains the workshop ID
    """
    async def dependency(
        workshop_id: int,
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user  # super_admin has universal access

        if current_user.workshop_id != workshop_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "WORKSHOP_ACCESS_DENIED",
                    "message": "You do not have access to this workshop",
                },
            )
        return current_user

    return dependency


async def get_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """Shortcut: require super_admin role."""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "INSUFFICIENT_PERMISSIONS",
                "message": "This action requires super_admin role",
            },
        )
    return current_user


async def get_owner_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Shortcut: require owner or super_admin role."""
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.OWNER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "INSUFFICIENT_PERMISSIONS",
                "message": "This action requires owner or super_admin role",
            },
        )
    return current_user


async def get_staff_or_above(current_user: User = Depends(get_current_user)) -> User:
    """Shortcut: require staff, owner, or super_admin role (excludes customer)."""
    if current_user.role not in (
        UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.STAFF
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "INSUFFICIENT_PERMISSIONS",
                "message": "Customers cannot access this resource",
            },
        )
    return current_user
