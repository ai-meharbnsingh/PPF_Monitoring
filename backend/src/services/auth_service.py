"""
Module: auth_service.py
Purpose:
    JWT token creation/validation and password hashing/verification.
    All authentication logic lives here — no auth code in routes.

Dependencies:
    External:
        - passlib[bcrypt] >= 1.7 (password hashing)
        - python-jose[cryptography] >= 3.3 (JWT)
    Internal:
        - src.config.settings (JWT config)
        - src.utils.constants (UserRole)

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from src.config.settings import get_settings
from src.utils.constants import UserRole
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# ─── Password hashing context ─────────────────────────────────────────────────
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.BCRYPT_ROUNDS)


def hash_password(plain_password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        plain_password: Raw password string

    Returns:
        str: bcrypt hash string
    """
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its bcrypt hash.

    Args:
        plain_password: Raw password to verify
        hashed_password: Stored bcrypt hash

    Returns:
        bool: True if password matches
    """
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: int,
    username: str,
    role: str,
    workshop_id: Optional[int] = None,
) -> str:
    """
    Create a signed JWT access token.

    Token expiry is role-dependent:
    - customer: CUSTOMER_TOKEN_EXPIRE_HOURS
    - owner: OWNER_TOKEN_EXPIRE_HOURS
    - super_admin / staff: ACCESS_TOKEN_EXPIRE_HOURS

    Args:
        user_id: Database user ID
        username: User's login username
        role: User role (from UserRole enum)
        workshop_id: Workshop association (None for super_admin)

    Returns:
        str: Signed JWT token string
    """
    if role == UserRole.CUSTOMER:
        expire_hours = settings.CUSTOMER_TOKEN_EXPIRE_HOURS
    elif role == UserRole.OWNER:
        expire_hours = settings.OWNER_TOKEN_EXPIRE_HOURS
    else:
        expire_hours = settings.ACCESS_TOKEN_EXPIRE_HOURS

    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=expire_hours)

    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "workshop_id": workshop_id,
        "iat": now,
        "exp": expire,
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    logger.debug(f"Created token for user_id={user_id} role={role} expires={expire.isoformat()}")
    return token


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        dict: Token payload with keys: sub, username, role, workshop_id

    Raises:
        ValueError: If token is expired or invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except ExpiredSignatureError:
        logger.warning("JWT token expired")
        raise ValueError("Token has expired")
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise ValueError("Invalid token")


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets minimum requirements.

    Requirements (from settings):
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 digit

    Args:
        password: Plain text password to validate

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    min_len = settings.PASSWORD_MIN_LENGTH

    if len(password) < min_len:
        return False, f"Password must be at least {min_len} characters"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least 1 uppercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least 1 digit"

    return True, ""
