"""
Module: routes/auth.py
Purpose:
    Authentication API endpoints: login, logout, me, change-password, refresh-token.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.config.database import get_db
from src.config.settings import get_settings
from src.models.audit_log import AuditLog
from src.models.user import User
from src.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from src.utils.helpers import utc_now
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
async def login(
    request: Request,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with username and password. Returns JWT access token.

    - Rate limited: 10 requests/minute per IP
    - Accounts lock after 5 failed attempts for 15 minutes
    """
    username = body.get("username", "").strip()
    password = body.get("password", "")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": "Username and password are required"},
        )

    # Find user
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    # Log failed attempt and raise (constant time to prevent enumeration)
    if not user:
        logger.warning(f"Login attempt for unknown username='{username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid username or password"},
        )

    # Check if account is locked
    if user.locked_until and user.locked_until > utc_now():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "ACCOUNT_LOCKED",
                "message": "Account temporarily locked due to too many failed attempts",
                "locked_until": user.locked_until.isoformat(),
            },
        )

    # Check if account is disabled
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "ACCOUNT_DISABLED", "message": "Account has been deactivated"},
        )

    # Verify password
    if not verify_password(password, user.password_hash):
        # Increment failed attempts
        user.login_attempt_count = (user.login_attempt_count or 0) + 1

        if user.login_attempt_count >= settings.MAX_LOGIN_ATTEMPTS:
            from datetime import timedelta
            user.locked_until = utc_now() + timedelta(minutes=settings.LOCKOUT_MINUTES)
            user.login_attempt_count = 0
            await db.commit()
            logger.warning(
                f"Account locked for username='{username}' "
                f"after {settings.MAX_LOGIN_ATTEMPTS} failed attempts"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "ACCOUNT_LOCKED",
                    "message": f"Account locked for {settings.LOCKOUT_MINUTES} minutes",
                    "locked_until": user.locked_until.isoformat(),
                },
            )

        await db.commit()
        logger.warning(
            f"Failed login for username='{username}' "
            f"attempt {user.login_attempt_count}/{settings.MAX_LOGIN_ATTEMPTS}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid username or password"},
        )

    # Success — reset counters
    user.login_attempt_count = 0
    user.locked_until = None
    user.last_login = utc_now()

    # Create token
    token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role,
        workshop_id=user.workshop_id,
    )

    # Audit log
    audit = AuditLog(
        workshop_id=user.workshop_id,
        user_id=user.id,
        action="user.login",
        resource_type="user",
        resource_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        created_at=utc_now(),
    )
    db.add(audit)
    await db.commit()

    logger.info(f"Successful login: username='{username}' role={user.role}")

    workshop_name = user.workshop.name if user.workshop else None

    return {
        "success": True,
        "data": {
            "access_token": token,
            "token_type": "Bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "workshop_id": user.workshop_id,
                "workshop_name": workshop_name,
                "first_name": user.first_name,
                "is_temporary_password": user.is_temporary_password,
            },
        },
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user.
    Note: JWT tokens are stateless — client must discard the token.
    Server-side blocklist can be added in Phase 2 if required.
    """
    logger.info(f"User logged out: username='{current_user.username}'")
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Return current user's profile information."""
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
            "workshop_id": current_user.workshop_id,
            "workshop_name": current_user.workshop.name if current_user.workshop else None,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "email": current_user.email,
            "phone": current_user.phone,
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
            "is_temporary_password": current_user.is_temporary_password,
        },
    }


@router.post("/change-password")
async def change_password(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change the current user's password."""
    current_password = body.get("current_password", "")
    new_password = body.get("new_password", "")

    if not current_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": "Both passwords are required"},
        )

    # Verify current password
    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_CURRENT_PASSWORD", "message": "Current password is incorrect"},
        )

    # Validate new password strength
    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PASSWORD_TOO_WEAK", "message": error_msg},
        )

    # Update password
    current_user.password_hash = hash_password(new_password)
    current_user.is_temporary_password = False
    await db.commit()

    logger.info(f"Password changed for username='{current_user.username}'")
    return {"success": True, "message": "Password changed successfully"}


@router.post("/refresh-token")
async def refresh_token(body: dict):
    """Refresh a JWT token before it expires."""
    token = body.get("access_token", "")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": "access_token is required"},
        )

    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_INVALID", "message": str(e)},
        )

    new_token = create_access_token(
        user_id=int(payload["sub"]),
        username=payload["username"],
        role=payload["role"],
        workshop_id=payload.get("workshop_id"),
    )

    return {
        "success": True,
        "data": {
            "access_token": new_token,
            "token_type": "Bearer",
        },
    }
