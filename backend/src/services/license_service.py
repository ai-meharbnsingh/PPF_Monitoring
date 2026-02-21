"""
Module: license_service.py
Purpose:
    License key validation for ESP32 devices.
    Called by MQTT subscriber on every incoming sensor message.
    Invalid licenses result in DISABLE command being sent to device.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.device import Device
from src.models.subscription import Subscription
from src.utils.constants import DeviceStatus, SubscriptionStatus
from src.utils.helpers import mask_license_key, utc_now
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LicenseValidationResult:
    """Result object from license validation."""

    def __init__(
        self,
        is_valid: bool,
        reason: str = "",
        device: Optional[Device] = None,
        workshop_id: Optional[int] = None,
        pit_id: Optional[int] = None,
    ):
        self.is_valid = is_valid
        self.reason = reason
        self.device = device
        self.workshop_id = workshop_id
        self.pit_id = pit_id


async def validate_license(
    db: AsyncSession,
    device_id: str,
    license_key: str,
) -> LicenseValidationResult:
    """
    Validate a device's license key against the database.

    Called on every MQTT sensor message. Fails fast and explicit —
    no silent failures. Invalid results trigger kill-switch flow.

    Args:
        db: Database session
        device_id: ESP32 device identifier (MAC-based)
        license_key: License key sent by device

    Returns:
        LicenseValidationResult with is_valid flag and reason
    """
    masked_key = mask_license_key(license_key)

    # 1. Find device by device_id
    device_result = await db.execute(
        select(Device).where(Device.device_id == device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device:
        logger.warning(f"License validation FAILED: Unknown device_id='{device_id}'")
        return LicenseValidationResult(
            is_valid=False,
            reason="Unknown device",
        )

    # 2. Validate license key matches device record
    if device.license_key != license_key:
        logger.warning(
            f"License validation FAILED: Key mismatch for device_id='{device_id}' "
            f"sent='{masked_key}' expected='{mask_license_key(device.license_key)}'"
        )
        return LicenseValidationResult(
            is_valid=False,
            reason="License key mismatch",
            device=device,
        )

    # 3. Check device status
    if device.status == DeviceStatus.DISABLED:
        logger.info(f"License validation FAILED: Device disabled device_id='{device_id}'")
        return LicenseValidationResult(
            is_valid=False,
            reason="Device disabled",
            device=device,
        )

    if device.status == DeviceStatus.SUSPENDED:
        logger.info(f"License validation FAILED: Device suspended device_id='{device_id}'")
        return LicenseValidationResult(
            is_valid=False,
            reason="Subscription suspended",
            device=device,
        )

    # 4. Check subscription status
    sub_result = await db.execute(
        select(Subscription).where(Subscription.device_id == device_id)
    )
    subscription = sub_result.scalar_one_or_none()

    if not subscription:
        logger.warning(f"License validation FAILED: No subscription for device_id='{device_id}'")
        return LicenseValidationResult(
            is_valid=False,
            reason="No active subscription",
            device=device,
        )

    if subscription.status == SubscriptionStatus.EXPIRED:
        logger.info(f"License EXPIRED for device_id='{device_id}'")
        return LicenseValidationResult(
            is_valid=False,
            reason="Subscription expired",
            device=device,
        )

    if subscription.status == SubscriptionStatus.SUSPENDED:
        logger.info(f"License SUSPENDED for device_id='{device_id}'")
        return LicenseValidationResult(
            is_valid=False,
            reason="Subscription suspended — payment overdue",
            device=device,
        )

    # 5. Check expiry date
    if subscription.expires_at and subscription.expires_at < utc_now():
        logger.info(
            f"License EXPIRED (past expiry date) for device_id='{device_id}' "
            f"expired={subscription.expires_at.isoformat()}"
        )
        return LicenseValidationResult(
            is_valid=False,
            reason="License expired",
            device=device,
        )

    # All checks passed
    logger.debug(f"License VALID for device_id='{device_id}' key='{masked_key}'")
    return LicenseValidationResult(
        is_valid=True,
        reason="Valid",
        device=device,
        workshop_id=device.workshop_id,
        pit_id=device.pit_id,
    )
