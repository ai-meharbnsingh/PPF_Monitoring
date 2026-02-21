"""
test_sensor_service.py
Unit tests for sensor_service.py

Tests:
  - parse_sensor_payload()   — JSON parsing, field validation
  - store_sensor_reading()   — ORM insert, type routing, NULL handling
  - evaluate_alerts()        — threshold evaluation, alert creation

Author: PPF Monitoring Team
Created: 2026-02-22
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.sensor_service import (
    parse_sensor_payload,
    store_sensor_reading,
    evaluate_alerts,
    _safe_float,
    _safe_int,
)
from src.models.alert import AlertConfig
from src.models.sensor_data import SensorData
from src.utils.constants import AlertSeverity, AlertType, SensorStatus


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_device(
    device_id="ESP32-AABBCCDDEEFF",
    workshop_id=1,
    pit_id=1,
    primary_code="DHT22",
    aq_code="PMS5003",
):
    """Build a minimal mock Device object."""
    device = MagicMock()
    device.device_id             = device_id
    device.workshop_id           = workshop_id
    device.pit_id                = pit_id
    device.primary_sensor_code   = primary_code
    device.air_quality_sensor_code = aq_code
    return device


DHT22_PAYLOAD = json.dumps({
    "device_id":       "ESP32-AABBCCDDEEFF",
    "license_key":     "LIC-TEST-TEST-TEST",
    "sensor_type":     "DHT22+PMS5003",
    "temperature":     24.5,
    "humidity":        58.2,
    "pm1":             8.2,
    "pm25":            14.6,
    "pm10":            22.1,
    "particles_03um":  1200,
    "particles_05um":  800,
    "particles_10um":  400,
    "particles_25um":  150,
    "particles_50um":  50,
    "particles_100um": 10,
    "timestamp":       "2026-02-22T10:30:00Z",
})

BME680_PAYLOAD = json.dumps({
    "device_id":      "ESP32-AABBCCDDEEFF",
    "license_key":    "LIC-TEST-TEST-TEST",
    "sensor_type":    "BME680",
    "temperature":    25.0,
    "humidity":       55.0,
    "pressure":       1013.2,
    "gas_resistance": 95000.0,
    "iaq":            82.4,
    "iaq_accuracy":   3,
    "timestamp":      "2026-02-22T10:30:00Z",
})


# ─────────────────────────────────────────────────────────────────────────────
# parse_sensor_payload()
# ─────────────────────────────────────────────────────────────────────────────

class TestParseSensorPayload:

    def test_valid_dht22_pms5003_payload(self):
        result = parse_sensor_payload(DHT22_PAYLOAD)
        assert result is not None
        assert result["device_id"]   == "ESP32-AABBCCDDEEFF"
        assert result["license_key"] == "LIC-TEST-TEST-TEST"
        assert result["temperature"] == 24.5
        assert result["pm25"]        == 14.6
        assert result["particles_03um"] == 1200

    def test_valid_bme680_payload(self):
        result = parse_sensor_payload(BME680_PAYLOAD)
        assert result is not None
        assert result["sensor_type"] == "BME680"
        assert result["pressure"]    == 1013.2
        assert result["iaq"]         == 82.4
        assert result["iaq_accuracy"] == 3

    def test_invalid_json_returns_none(self):
        assert parse_sensor_payload("{not json}") is None

    def test_empty_string_returns_none(self):
        assert parse_sensor_payload("") is None

    def test_missing_device_id_returns_none(self):
        payload = json.dumps({"license_key": "LIC-XXXX"})
        assert parse_sensor_payload(payload) is None

    def test_missing_license_key_returns_none(self):
        payload = json.dumps({"device_id": "ESP32-AABBCCDDEEFF"})
        assert parse_sensor_payload(payload) is None

    def test_both_required_keys_present_accepts(self):
        payload = json.dumps({
            "device_id":   "ESP32-AABBCCDDEEFF",
            "license_key": "LIC-XXXX",
            # All other fields optional
        })
        result = parse_sensor_payload(payload)
        assert result is not None

    def test_extra_fields_are_preserved(self):
        payload = json.dumps({
            "device_id":   "ESP32-AABBCCDDEEFF",
            "license_key": "LIC-XXXX",
            "custom_field": "custom_value",
        })
        result = parse_sensor_payload(payload)
        assert result["custom_field"] == "custom_value"


# ─────────────────────────────────────────────────────────────────────────────
# store_sensor_reading()
# ─────────────────────────────────────────────────────────────────────────────

class TestStoreSensorReading:

    @pytest.mark.asyncio
    async def test_stores_dht22_pms5003_fields(self):
        """DHT22+PMS5003 payload — temperature, humidity and PM values stored."""
        payload = parse_sensor_payload(DHT22_PAYLOAD)
        device  = _make_device()

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add  = MagicMock()
        mock_session.flush = AsyncMock()

        result = await store_sensor_reading(
            db=mock_session,
            payload=payload,
            device=device,
            workshop_id=1,
            pit_id=1,
        )

        assert result is not None
        assert result.temperature == pytest.approx(24.5)
        assert result.humidity    == pytest.approx(58.2)
        assert result.pm25        == pytest.approx(14.6)
        assert result.pm10        == pytest.approx(22.1)
        assert result.particles_03um == 1200
        assert result.particles_100um == 10
        assert result.is_valid is True
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_stores_bme680_fields(self):
        """BME680 payload — pressure, gas, IAQ stored; PM fields are None."""
        payload = parse_sensor_payload(BME680_PAYLOAD)
        device  = _make_device(primary_code="BME680", aq_code=None)

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add  = MagicMock()
        mock_session.flush = AsyncMock()

        result = await store_sensor_reading(
            db=mock_session,
            payload=payload,
            device=device,
            workshop_id=1,
            pit_id=1,
        )

        assert result is not None
        assert result.pressure       == pytest.approx(1013.2)
        assert result.gas_resistance == pytest.approx(95000.0)
        assert result.iaq            == pytest.approx(82.4)
        assert result.iaq_accuracy   == 3
        # PM fields should be None for BME680-only setup
        assert result.pm25 is None
        assert result.pm10 is None

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self):
        """If session.flush raises, function returns None gracefully."""
        payload = parse_sensor_payload(DHT22_PAYLOAD)
        device  = _make_device()

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=Exception("DB error"))

        result = await store_sensor_reading(
            db=mock_session,
            payload=payload,
            device=device,
            workshop_id=1,
            pit_id=1,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_timestamp_is_handled(self):
        """Malformed device timestamp does not crash — stored as None."""
        data = json.loads(DHT22_PAYLOAD)
        data["timestamp"] = "not-a-timestamp"
        payload = data

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add  = MagicMock()
        mock_session.flush = AsyncMock()

        device = _make_device()
        result = await store_sensor_reading(
            db=mock_session, payload=payload, device=device,
            workshop_id=1, pit_id=1,
        )
        assert result is not None
        assert result.device_timestamp is None

    @pytest.mark.asyncio
    async def test_missing_pm_fields_stored_as_none(self):
        """Partial payload with only DHT22 fields — PM fields become None."""
        payload = {
            "device_id":   "ESP32-AABBCCDDEEFF",
            "license_key": "LIC-TEST-TEST-TEST",
            "temperature": 23.0,
            "humidity":    55.0,
        }
        device = _make_device()

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add  = MagicMock()
        mock_session.flush = AsyncMock()

        result = await store_sensor_reading(
            db=mock_session, payload=payload, device=device,
            workshop_id=1, pit_id=1,
        )
        assert result is not None
        assert result.pm25 is None
        assert result.pm10 is None


# ─────────────────────────────────────────────────────────────────────────────
# evaluate_alerts()
# ─────────────────────────────────────────────────────────────────────────────

def _make_reading(**kwargs):
    """Build a mock SensorData reading with custom field values."""
    defaults = dict(
        device_id="ESP32-AABBCCDDEEFF",
        temperature=None, humidity=None,
        pm25=None, pm10=None, iaq=None,
    )
    defaults.update(kwargs)
    reading = MagicMock(spec=SensorData)
    for k, v in defaults.items():
        setattr(reading, k, v)
    return reading


def _mock_session_no_config():
    """Mock session that returns no AlertConfig (use defaults)."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result  = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.add     = MagicMock()
    return mock_session


class TestEvaluateAlerts:

    @pytest.mark.asyncio
    async def test_no_alerts_for_normal_values(self):
        """Normal temp+humidity+pm25 → no alerts."""
        reading = _make_reading(temperature=24.0, humidity=50.0, pm25=10.0)
        alerts  = await evaluate_alerts(
            _mock_session_no_config(), reading, workshop_id=1, pit_id=1
        )
        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_high_pm25_warning_alert(self):
        """PM2.5 between warning (12) and critical (35.4) → WARNING alert."""
        reading = _make_reading(pm25=20.0)
        alerts  = await evaluate_alerts(
            _mock_session_no_config(), reading, workshop_id=1, pit_id=1
        )
        pm_alerts = [a for a in alerts if hasattr(a, 'alert_type') and a.alert_type == AlertType.HIGH_PM25]
        assert len(pm_alerts) == 1
        assert pm_alerts[0].severity == AlertSeverity.WARNING

    @pytest.mark.asyncio
    async def test_high_pm25_critical_alert(self):
        """PM2.5 above critical threshold (35.4) → CRITICAL alert."""
        reading = _make_reading(pm25=50.0)
        alerts  = await evaluate_alerts(
            _mock_session_no_config(), reading, workshop_id=1, pit_id=1
        )
        pm_alerts = [a for a in alerts if a.alert_type == AlertType.HIGH_PM25]
        assert len(pm_alerts) == 1
        assert pm_alerts[0].severity == AlertSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_temp_too_high_alert(self):
        """Temperature above max threshold (35°C default) → WARNING alert."""
        reading = _make_reading(temperature=38.0)
        alerts  = await evaluate_alerts(
            _mock_session_no_config(), reading, workshop_id=1, pit_id=1
        )
        temp_alerts = [a for a in alerts if a.alert_type in (
            AlertType.TEMP_TOO_HIGH, AlertType.TEMP_TOO_LOW
        )]
        assert len(temp_alerts) == 1

    @pytest.mark.asyncio
    async def test_temp_too_low_alert(self):
        """Temperature below min threshold (15°C default) → WARNING alert."""
        reading = _make_reading(temperature=10.0)
        alerts  = await evaluate_alerts(
            _mock_session_no_config(), reading, workshop_id=1, pit_id=1
        )
        temp_alerts = [a for a in alerts if a.alert_type in (
            AlertType.TEMP_TOO_HIGH, AlertType.TEMP_TOO_LOW
        )]
        assert len(temp_alerts) >= 1

    @pytest.mark.asyncio
    async def test_high_humidity_alert(self):
        """Humidity above 70% → alert."""
        reading = _make_reading(humidity=80.0)
        alerts  = await evaluate_alerts(
            _mock_session_no_config(), reading, workshop_id=1, pit_id=1
        )
        hum_alerts = [a for a in alerts if a.alert_type == AlertType.HUMIDITY_TOO_HIGH]
        assert len(hum_alerts) == 1

    @pytest.mark.asyncio
    async def test_iaq_warning_alert(self):
        """IAQ between 100 and 150 → WARNING alert (BME680 mode)."""
        reading = _make_reading(iaq=120.0)
        alerts  = await evaluate_alerts(
            _mock_session_no_config(), reading, workshop_id=1, pit_id=1
        )
        iaq_alerts = [a for a in alerts if a.alert_type == AlertType.HIGH_IAQ]
        assert len(iaq_alerts) == 1
        assert iaq_alerts[0].severity == AlertSeverity.WARNING

    @pytest.mark.asyncio
    async def test_no_crash_on_all_none_readings(self):
        """Reading with all-None sensor values → no alerts, no exception."""
        reading = _make_reading()
        alerts  = await evaluate_alerts(
            _mock_session_no_config(), reading, workshop_id=1, pit_id=1
        )
        assert isinstance(alerts, list)

    @pytest.mark.asyncio
    async def test_custom_threshold_from_config(self):
        """Custom AlertConfig thresholds override defaults."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_config  = MagicMock(spec=AlertConfig)
        mock_config.temp_min       = 10.0
        mock_config.temp_max       = 40.0  # raised max
        mock_config.humidity_max   = 70.0
        mock_config.pm25_warning   = 12.0
        mock_config.pm25_critical  = 35.4
        mock_config.pm10_warning   = 54.0
        mock_config.pm10_critical  = 154.0
        mock_config.iaq_warning    = 100.0
        mock_config.iaq_critical   = 150.0

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add     = MagicMock()

        # Temperature 38°C — would trigger with default max=35 but not with custom max=40
        reading = _make_reading(temperature=38.0)
        alerts  = await evaluate_alerts(mock_session, reading, workshop_id=1, pit_id=1)
        temp_alerts = [a for a in alerts if a.alert_type in (
            AlertType.TEMP_TOO_HIGH, AlertType.TEMP_TOO_LOW
        )]
        assert len(temp_alerts) == 0, "Should NOT alert — custom threshold is 40°C"


# ─────────────────────────────────────────────────────────────────────────────
# _safe_float() / _safe_int()
# ─────────────────────────────────────────────────────────────────────────────

class TestSafeConversions:

    def test_safe_float_none(self):
        assert _safe_float(None) is None

    def test_safe_float_valid(self):
        assert _safe_float(24.5) == pytest.approx(24.5)
        assert _safe_float("24.5") == pytest.approx(24.5)
        assert _safe_float(24) == pytest.approx(24.0)

    def test_safe_float_nan_returns_none(self):
        import math
        assert _safe_float(float("nan")) is None

    def test_safe_float_invalid_returns_none(self):
        assert _safe_float("not-a-number") is None
        assert _safe_float([1, 2]) is None

    def test_safe_int_none(self):
        assert _safe_int(None) is None

    def test_safe_int_valid(self):
        assert _safe_int(42)   == 42
        assert _safe_int("42") == 42
        assert _safe_int(3.9)  == 3

    def test_safe_int_invalid_returns_none(self):
        assert _safe_int("xyz") is None
