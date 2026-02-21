"""
test_license_service.py
Unit tests for license_service.py

Tests every branch of validate_license():
  - Unknown device
  - License key mismatch
  - Device disabled / suspended
  - No subscription
  - Subscription expired / suspended
  - Subscription past expires_at date
  - All checks passed → valid

Author: PPF Monitoring Team
Created: 2026-02-22
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.license_service import LicenseValidationResult, validate_license
from src.models.device import Device
from src.models.subscription import Subscription
from src.utils.constants import DeviceStatus, SubscriptionStatus


# ─────────────────────────────────────────────────────────────────────────────
# Test fixtures / helpers
# ─────────────────────────────────────────────────────────────────────────────

DEVICE_ID   = "ESP32-AABBCCDDEEFF"
LICENSE_KEY = "LIC-GOOD-GOOD-GOOD"


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _make_device(
    device_id: str = DEVICE_ID,
    license_key: str = LICENSE_KEY,
    status: str = DeviceStatus.ACTIVE,
    workshop_id: int = 1,
    pit_id: int = 1,
) -> MagicMock:
    device = MagicMock(spec=Device)
    device.device_id   = device_id
    device.license_key = license_key
    device.status      = status
    device.workshop_id = workshop_id
    device.pit_id      = pit_id
    return device


def _make_subscription(
    status: str = SubscriptionStatus.ACTIVE,
    expires_at: datetime = None,
) -> MagicMock:
    sub = MagicMock(spec=Subscription)
    sub.status     = status
    sub.expires_at = expires_at
    return sub


def _session_with_device_and_sub(device, subscription):
    """
    Build a mock AsyncSession that returns `device` for the first execute()
    call and `subscription` for the second.
    """
    session = AsyncMock()

    device_result = MagicMock()
    device_result.scalar_one_or_none.return_value = device

    sub_result = MagicMock()
    sub_result.scalar_one_or_none.return_value = subscription

    session.execute = AsyncMock(side_effect=[device_result, sub_result])
    return session


def _session_no_device():
    """Mock session that returns None for device lookup."""
    session = AsyncMock()
    result  = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)
    return session


# ─────────────────────────────────────────────────────────────────────────────
# Test cases
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateLicense:

    # ── Unknown device ────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_unknown_device_is_invalid(self):
        session = _session_no_device()
        result  = await validate_license(session, DEVICE_ID, LICENSE_KEY)

        assert result.is_valid is False
        assert "unknown" in result.reason.lower() or "device" in result.reason.lower()
        assert result.device is None

    # ── License key mismatch ──────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_wrong_license_key_is_invalid(self):
        device  = _make_device(license_key="LIC-REAL-REAL-REAL")
        session = _session_with_device_and_sub(device, None)

        result = await validate_license(session, DEVICE_ID, "LIC-FAKE-FAKE-FAKE")

        assert result.is_valid is False
        assert "mismatch" in result.reason.lower() or "key" in result.reason.lower()

    # ── Device status ─────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_disabled_device_is_invalid(self):
        device  = _make_device(status=DeviceStatus.DISABLED)
        session = _session_with_device_and_sub(device, None)

        result = await validate_license(session, DEVICE_ID, LICENSE_KEY)

        assert result.is_valid is False
        assert "disabled" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_suspended_device_is_invalid(self):
        device  = _make_device(status=DeviceStatus.SUSPENDED)
        session = _session_with_device_and_sub(device, None)

        result = await validate_license(session, DEVICE_ID, LICENSE_KEY)

        assert result.is_valid is False
        assert "suspended" in result.reason.lower()

    # ── No subscription ───────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_no_subscription_is_invalid(self):
        device  = _make_device()
        session = _session_with_device_and_sub(device, subscription=None)

        result = await validate_license(session, DEVICE_ID, LICENSE_KEY)

        assert result.is_valid is False
        assert "subscription" in result.reason.lower()

    # ── Subscription status ───────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_expired_subscription_is_invalid(self):
        device  = _make_device()
        sub     = _make_subscription(status=SubscriptionStatus.EXPIRED)
        session = _session_with_device_and_sub(device, sub)

        result = await validate_license(session, DEVICE_ID, LICENSE_KEY)

        assert result.is_valid is False
        assert "expired" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_suspended_subscription_is_invalid(self):
        device  = _make_device()
        sub     = _make_subscription(status=SubscriptionStatus.SUSPENDED)
        session = _session_with_device_and_sub(device, sub)

        result = await validate_license(session, DEVICE_ID, LICENSE_KEY)

        assert result.is_valid is False
        assert "suspended" in result.reason.lower()

    # ── Expiry date ───────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_past_expiry_date_is_invalid(self):
        device      = _make_device()
        past_expiry = _now() - timedelta(days=1)
        sub         = _make_subscription(
            status=SubscriptionStatus.ACTIVE,
            expires_at=past_expiry,
        )
        session = _session_with_device_and_sub(device, sub)

        result = await validate_license(session, DEVICE_ID, LICENSE_KEY)

        assert result.is_valid is False
        assert "expired" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_future_expiry_date_is_valid(self):
        device        = _make_device()
        future_expiry = _now() + timedelta(days=30)
        sub           = _make_subscription(
            status=SubscriptionStatus.ACTIVE,
            expires_at=future_expiry,
        )
        session = _session_with_device_and_sub(device, sub)

        result = await validate_license(session, DEVICE_ID, LICENSE_KEY)

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_no_expiry_date_active_sub_is_valid(self):
        """Subscription with no expires_at (e.g. perpetual) → valid."""
        device  = _make_device()
        sub     = _make_subscription(status=SubscriptionStatus.ACTIVE, expires_at=None)
        session = _session_with_device_and_sub(device, sub)

        result = await validate_license(session, DEVICE_ID, LICENSE_KEY)

        assert result.is_valid is True

    # ── Happy path ────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_valid_license_returns_device_context(self):
        """All checks pass → result carries device, workshop_id, pit_id."""
        device  = _make_device(workshop_id=5, pit_id=3)
        sub     = _make_subscription(status=SubscriptionStatus.ACTIVE)
        session = _session_with_device_and_sub(device, sub)

        result = await validate_license(session, DEVICE_ID, LICENSE_KEY)

        assert result.is_valid    is True
        assert result.device      is device
        assert result.workshop_id == 5
        assert result.pit_id      == 3
        assert result.reason      == "Valid"

    # ── LicenseValidationResult ───────────────────────────────────────────────

    def test_result_object_is_valid_true(self):
        result = LicenseValidationResult(is_valid=True, reason="Valid")
        assert result.is_valid is True
        assert result.reason   == "Valid"
        assert result.device   is None

    def test_result_object_is_valid_false(self):
        result = LicenseValidationResult(is_valid=False, reason="Expired")
        assert result.is_valid is False

    def test_result_object_with_device(self):
        device = _make_device()
        result = LicenseValidationResult(
            is_valid=True, reason="Valid",
            device=device, workshop_id=1, pit_id=2
        )
        assert result.workshop_id == 1
        assert result.pit_id      == 2
