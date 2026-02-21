"""
Module: helpers.py
Purpose:
    Utility/helper functions used across the application.
    Includes: license key generation, username generation, token generation,
    sensor status evaluation, slug creation.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

import random
import secrets
import string
from datetime import datetime, timezone
from typing import Optional

from slugify import slugify

from src.utils.constants import (
    LICENSE_KEY_PREFIX,
    AlertSeverity,
    SensorStatus,
)


def generate_license_key() -> str:
    """
    Generate a unique device license key in format: LIC-XXXX-YYYY-ZZZZ

    Returns:
        str: License key e.g., 'LIC-4F8D-9K2L-3P7Q'
    """
    chars = string.ascii_uppercase + string.digits
    segments = [
        "".join(random.choices(chars, k=4)),
        "".join(random.choices(chars, k=4)),
        "".join(random.choices(chars, k=4)),
    ]
    return f"{LICENSE_KEY_PREFIX}-{'-'.join(segments)}"


def generate_device_id(mac_address: str) -> str:
    """
    Generate device ID from MAC address.

    Args:
        mac_address: Hardware MAC, e.g., 'A1:B2:C3:D4:E5:F6'

    Returns:
        str: Device ID e.g., 'ESP32-A1B2C3D4E5F6'
    """
    clean_mac = mac_address.replace(":", "").replace("-", "").upper()
    return f"ESP32-{clean_mac}"


def generate_customer_username(name: str) -> str:
    """
    Generate a URL-safe username from a customer's name with a random suffix.

    Args:
        name: Customer full name e.g., 'Rajesh Kumar'

    Returns:
        str: e.g., 'raj_kumar_a3f2'
    """
    parts = name.lower().split()
    if len(parts) >= 2:
        base = f"{parts[0][:3]}_{parts[-1][:5]}"
    else:
        base = parts[0][:8]

    suffix = secrets.token_hex(2)
    return f"{slugify(base, separator='_')}_{suffix}"


def generate_temporary_password(length: int = 8) -> str:
    """
    Generate a readable temporary password.
    Format: 3 uppercase + 3 digits + @ + 2 lowercase
    Always meets minimum password policy requirements.

    Returns:
        str: e.g., 'PPF@9834Ka'
    """
    upper = "".join(random.choices(string.ascii_uppercase, k=3))
    digits = "".join(random.choices(string.digits, k=4))
    lower = "".join(random.choices(string.ascii_lowercase, k=2))
    return f"{upper}@{digits}{lower}"


def generate_workshop_slug(name: str) -> str:
    """
    Generate URL-safe slug from workshop name.

    Args:
        name: e.g., 'Rays PPF Delhi'

    Returns:
        str: e.g., 'rays-ppf-delhi'
    """
    return slugify(name, max_length=50, word_boundary=True)


def generate_stream_token() -> str:
    """Generate a secure random token for video stream authentication."""
    return secrets.token_urlsafe(32)


def generate_customer_view_token() -> str:
    """Generate a short-lived view token for customer portal access."""
    return f"tok_{secrets.token_urlsafe(16)}"


def utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def evaluate_pm25_status(pm25: Optional[float], warning: float, critical: float) -> SensorStatus:
    """
    Evaluate PM2.5 reading against thresholds.

    Args:
        pm25: PM2.5 reading in μg/m³
        warning: Warning threshold
        critical: Critical threshold

    Returns:
        SensorStatus enum value
    """
    if pm25 is None:
        return SensorStatus.UNKNOWN
    if pm25 >= critical:
        return SensorStatus.CRITICAL
    if pm25 >= warning:
        return SensorStatus.WARNING
    return SensorStatus.GOOD


def evaluate_temperature_status(
    temp: Optional[float], temp_min: float, temp_max: float
) -> SensorStatus:
    """Evaluate temperature reading against min/max thresholds."""
    if temp is None:
        return SensorStatus.UNKNOWN
    if temp < temp_min or temp > temp_max:
        return SensorStatus.WARNING
    return SensorStatus.GOOD


def evaluate_humidity_status(humidity: Optional[float], max_humidity: float) -> SensorStatus:
    """Evaluate humidity reading against max threshold."""
    if humidity is None:
        return SensorStatus.UNKNOWN
    if humidity > max_humidity:
        return SensorStatus.WARNING
    return SensorStatus.GOOD


def evaluate_iaq_status(iaq: Optional[float], warning: float, critical: float) -> SensorStatus:
    """Evaluate BME680 IAQ reading against thresholds."""
    if iaq is None:
        return SensorStatus.UNKNOWN
    if iaq >= critical:
        return SensorStatus.CRITICAL
    if iaq >= warning:
        return SensorStatus.WARNING
    return SensorStatus.GOOD


def compute_job_progress(
    start_time: Optional[datetime],
    estimated_end_time: Optional[datetime],
) -> tuple[int, int]:
    """
    Compute job progress percentage and time remaining in minutes.

    Args:
        start_time: When job actually started
        estimated_end_time: Estimated completion time

    Returns:
        Tuple of (progress_percent: int, time_remaining_minutes: int)
    """
    if not start_time or not estimated_end_time:
        return 0, 0

    now = utc_now()
    total_duration = (estimated_end_time - start_time).total_seconds()
    elapsed = (now - start_time).total_seconds()

    if total_duration <= 0:
        return 100, 0

    progress = min(100, max(0, int((elapsed / total_duration) * 100)))
    remaining_seconds = max(0, (estimated_end_time - now).total_seconds())
    remaining_minutes = int(remaining_seconds / 60)

    return progress, remaining_minutes


def mask_license_key(license_key: str) -> str:
    """
    Mask license key for logging (show first segment only).

    Args:
        license_key: e.g., 'LIC-4F8D-9K2L-3P7Q'

    Returns:
        str: e.g., 'LIC-4F8D-****-****'
    """
    parts = license_key.split("-")
    if len(parts) < 2:
        return "***"
    return f"{parts[0]}-{parts[1]}-****-****"
