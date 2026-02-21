"""
Unit tests: helpers.py
Tests pure utility functions — no DB needed.
"""

import pytest

from src.utils.helpers import (
    compute_job_progress,
    evaluate_humidity_status,
    evaluate_iaq_status,
    evaluate_pm25_status,
    evaluate_temperature_status,
    generate_customer_username,
    generate_device_id,
    generate_license_key,
    generate_temporary_password,
    generate_workshop_slug,
    mask_license_key,
)
from src.utils.constants import SensorStatus


class TestLicenseKey:
    def test_format(self):
        key = generate_license_key()
        parts = key.split("-")
        assert parts[0] == "LIC"
        assert len(parts) == 4
        for seg in parts[1:]:
            assert len(seg) == 4

    def test_uniqueness(self):
        keys = {generate_license_key() for _ in range(100)}
        assert len(keys) >= 95  # allow tiny collision probability


class TestDeviceId:
    def test_format(self):
        device_id = generate_device_id("A1:B2:C3:D4:E5:F6")
        assert device_id == "ESP32-A1B2C3D4E5F6"

    def test_handles_dashes(self):
        device_id = generate_device_id("A1-B2-C3-D4-E5-F6")
        assert device_id == "ESP32-A1B2C3D4E5F6"


class TestSlugs:
    def test_basic_slug(self):
        slug = generate_workshop_slug("Rays PPF Delhi")
        assert slug == "rays-ppf-delhi"

    def test_special_chars_removed(self):
        slug = generate_workshop_slug("Raj's Workshop & Co.")
        assert "@" not in slug
        assert "&" not in slug


class TestCustomerUsername:
    def test_has_random_suffix(self):
        u1 = generate_customer_username("Rajesh Kumar")
        u2 = generate_customer_username("Rajesh Kumar")
        assert u1 != u2  # different random suffix

    def test_no_spaces(self):
        username = generate_customer_username("Some Name")
        assert " " not in username


class TestTempPassword:
    def test_meets_policy(self):
        for _ in range(20):
            pwd = generate_temporary_password()
            assert any(c.isupper() for c in pwd)
            assert any(c.isdigit() for c in pwd)
            assert len(pwd) >= 8


class TestMaskLicenseKey:
    def test_masks_segments(self):
        masked = mask_license_key("LIC-4F8D-9K2L-3P7Q")
        assert masked == "LIC-4F8D-****-****"

    def test_short_key_returns_stars(self):
        assert mask_license_key("short") == "***"


class TestSensorStatusEvaluation:
    def test_pm25_good(self):
        assert evaluate_pm25_status(5.0, 12.0, 35.4) == SensorStatus.GOOD

    def test_pm25_warning(self):
        assert evaluate_pm25_status(15.0, 12.0, 35.4) == SensorStatus.WARNING

    def test_pm25_critical(self):
        assert evaluate_pm25_status(40.0, 12.0, 35.4) == SensorStatus.CRITICAL

    def test_pm25_none_is_unknown(self):
        assert evaluate_pm25_status(None, 12.0, 35.4) == SensorStatus.UNKNOWN

    def test_temp_good(self):
        assert evaluate_temperature_status(25.0, 15.0, 35.0) == SensorStatus.GOOD

    def test_temp_below_min(self):
        assert evaluate_temperature_status(10.0, 15.0, 35.0) == SensorStatus.WARNING

    def test_temp_above_max(self):
        assert evaluate_temperature_status(40.0, 15.0, 35.0) == SensorStatus.WARNING

    def test_humidity_good(self):
        assert evaluate_humidity_status(50.0, 70.0) == SensorStatus.GOOD

    def test_humidity_too_high(self):
        assert evaluate_humidity_status(80.0, 70.0) == SensorStatus.WARNING

    def test_iaq_critical(self):
        assert evaluate_iaq_status(160.0, 100.0, 150.0) == SensorStatus.CRITICAL


class TestJobProgress:
    def test_no_start_time(self):
        progress, remaining = compute_job_progress(None, None)
        assert progress == 0
        assert remaining == 0

    def test_completed_job(self):
        from datetime import datetime, timedelta, timezone
        start = datetime.now(tz=timezone.utc) - timedelta(hours=4)
        end = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        progress, remaining = compute_job_progress(start, end)
        assert progress == 100
        assert remaining == 0
