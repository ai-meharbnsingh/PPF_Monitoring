"""
Module: sensor_service.py
Purpose:
    Sensor data processing and storage.
    Parses incoming MQTT JSON payloads, validates readings, stores to DB,
    and evaluates alert conditions against workshop thresholds.
    Supports DHT22+PMS5003 (primary) and BME680 (alternative).

Author: PPF Monitoring Team
Created: 2026-02-21
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.alert import Alert, AlertConfig
from src.models.device import Device
from src.models.pit_alert_config import PitAlertConfig
from src.models.sensor_data import SensorData
from src.utils.constants import AlertSeverity, AlertType, SensorStatus
from src.utils.helpers import (
    evaluate_humidity_status,
    evaluate_iaq_status,
    evaluate_pm25_status,
    evaluate_temperature_status,
    utc_now,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _resolve_threshold(pit_cfg, ws_cfg, field: str, default):
    """Return pit override if set, else workshop config, else hardcoded default."""
    if pit_cfg is not None:
        val = getattr(pit_cfg, field, None)
        if val is not None:
            return val
    if ws_cfg is not None:
        val = getattr(ws_cfg, field, None)
        if val is not None:
            return val
    return default


def parse_sensor_payload(raw_payload: str) -> Optional[dict]:
    """
    Parse incoming MQTT JSON payload from ESP32.

    Expected format (DHT22 + PMS5003):
    {
        "device_id": "ESP32-A1B2C3D4E5F6",
        "license_key": "LIC-XXXX-YYYY-ZZZZ",
        "sensor_type": "DHT22+PMS5003",
        "temperature": 24.5,
        "humidity": 58.2,
        "pm1": 8.2,
        "pm25": 14.6,
        "pm10": 22.1,
        "timestamp": "2026-02-21T10:30:00Z"
    }

    Expected format (BME680):
    {
        "device_id": "ESP32-A1B2C3D4E5F6",
        "license_key": "LIC-XXXX-YYYY-ZZZZ",
        "sensor_type": "BME680",
        "temperature": 24.5,
        "humidity": 58.2,
        "pressure": 1013.2,
        "gas_resistance": 95000,
        "iaq": 82.4,
        "iaq_accuracy": 3,
        "timestamp": "2026-02-21T10:30:00Z"
    }

    Args:
        raw_payload: Raw MQTT message bytes decoded to string

    Returns:
        dict if valid, None if parsing fails
    """
    try:
        data = json.loads(raw_payload)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse sensor JSON payload: {e} | Raw: {raw_payload[:200]}")
        return None

    required_keys = {"device_id", "license_key"}
    if not required_keys.issubset(data.keys()):
        logger.warning(f"Sensor payload missing required keys. Got: {list(data.keys())}")
        return None

    return data


async def store_sensor_reading(
    db: AsyncSession,
    payload: dict,
    device: Device,
    workshop_id: int,
    pit_id: int,
) -> Optional[SensorData]:
    """
    Store a validated sensor reading to the database.

    Determines sensor type from device configuration and payload content.
    All non-applicable fields are stored as NULL.

    Args:
        db: Database session
        payload: Parsed MQTT payload dict
        device: Device ORM model instance
        workshop_id: Workshop ID (denormalized)
        pit_id: Pit ID

    Returns:
        SensorData instance if stored, None on error
    """
    try:
        now = utc_now()

        # Parse device timestamp if present
        device_ts = None
        if "timestamp" in payload:
            try:
                device_ts = datetime.fromisoformat(
                    payload["timestamp"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                logger.warning(f"Invalid device timestamp: {payload.get('timestamp')}")

        # Determine sensor types
        primary_type = device.primary_sensor_code   # 'DHT22' or 'BME680'
        aq_type = device.air_quality_sensor_code     # 'PMS5003' or None

        reading = SensorData(
            device_id=device.device_id,
            pit_id=pit_id,
            workshop_id=workshop_id,
            primary_sensor_type=primary_type,
            air_quality_sensor_type=aq_type,
            # Shared fields (DHT22 or BME680)
            temperature=_safe_float(payload.get("temperature")),
            humidity=_safe_float(payload.get("humidity")),
            # BME680-specific (None for DHT22)
            pressure=_safe_float(payload.get("pressure")),
            gas_resistance=_safe_float(payload.get("gas_resistance")),
            iaq=_safe_float(payload.get("iaq")),
            iaq_accuracy=_safe_int(payload.get("iaq_accuracy")),
            # PMS5003-specific (None for BME680-only)
            pm1=_safe_float(payload.get("pm1")),
            pm25=_safe_float(payload.get("pm25")),
            pm10=_safe_float(payload.get("pm10")),
            particles_03um=_safe_int(payload.get("particles_03um")),
            particles_05um=_safe_int(payload.get("particles_05um")),
            particles_10um=_safe_int(payload.get("particles_10um")),
            particles_25um=_safe_int(payload.get("particles_25um")),
            particles_50um=_safe_int(payload.get("particles_50um")),
            particles_100um=_safe_int(payload.get("particles_100um")),
            # Validity
            is_valid=True,
            device_timestamp=device_ts,
            created_at=now,
        )

        db.add(reading)
        await db.flush()  # get ID without commit

        logger.debug(
            f"Stored sensor reading pit_id={pit_id} "
            f"temp={reading.temperature} humidity={reading.humidity} "
            f"pm25={reading.pm25}"
        )
        return reading

    except Exception as e:
        logger.error(
            f"Failed to store sensor reading for device '{device.device_id}': {e}",
            exc_info=True
        )
        return None


async def evaluate_alerts(
    db: AsyncSession,
    reading: SensorData,
    workshop_id: int,
    pit_id: int,
) -> list[Alert]:
    """
    Check sensor reading against alert thresholds and create alerts.

    Resolution order for each threshold:
      1. Per-pit PitAlertConfig (if set and non-null)
      2. Per-workshop AlertConfig
      3. Hardcoded defaults

    Args:
        db: Database session
        reading: SensorData instance just stored
        workshop_id: Workshop to fetch alert config for
        pit_id: Pit that triggered the reading

    Returns:
        List of Alert objects created (empty if no violations)
    """
    triggered_alerts = []
    COOLDOWN_MINUTES = 5

    try:
        # Fetch workshop alert config
        config_result = await db.execute(
            select(AlertConfig).where(AlertConfig.workshop_id == workshop_id)
        )
        config = config_result.scalar_one_or_none()

        # Fetch per-pit alert config overrides
        pit_config_result = await db.execute(
            select(PitAlertConfig).where(PitAlertConfig.pit_id == pit_id)
        )
        pit_config = pit_config_result.scalar_one_or_none()

        # Resolve thresholds: pit override → workshop config → default
        temp_min = _resolve_threshold(pit_config, config, "temp_min", 15.0)
        temp_max = _resolve_threshold(pit_config, config, "temp_max", 35.0)
        humidity_max = _resolve_threshold(pit_config, config, "humidity_max", 70.0)
        pm25_warning = _resolve_threshold(pit_config, config, "pm25_warning", 12.0)
        pm25_critical = _resolve_threshold(pit_config, config, "pm25_critical", 35.4)
        pm10_warning = _resolve_threshold(pit_config, config, "pm10_warning", 54.0)
        pm10_critical = _resolve_threshold(pit_config, config, "pm10_critical", 154.0)
        iaq_warning = _resolve_threshold(pit_config, config, "iaq_warning", 100.0)
        iaq_critical = _resolve_threshold(pit_config, config, "iaq_critical", 150.0)

        now = utc_now()

        # ── Temperature ────────────────────────────────────────────────────
        if reading.temperature is not None:
            temp_status = evaluate_temperature_status(reading.temperature, temp_min, temp_max)
            if temp_status == SensorStatus.WARNING:
                alert_type = (
                    AlertType.TEMP_TOO_LOW
                    if reading.temperature < temp_min
                    else AlertType.TEMP_TOO_HIGH
                )
                if not await _alert_on_cooldown(db, reading.device_id, pit_id, alert_type, COOLDOWN_MINUTES):
                    threshold = temp_min if reading.temperature < temp_min else temp_max
                    alert = _create_alert(
                        workshop_id=workshop_id,
                        pit_id=pit_id,
                        device_id=reading.device_id,
                        alert_type=alert_type,
                        severity=AlertSeverity.WARNING,
                        message=(
                            f"Temperature {reading.temperature:.1f}°C is outside safe range "
                            f"({temp_min}°C — {temp_max}°C)"
                        ),
                        trigger_value=reading.temperature,
                        threshold_value=threshold,
                        now=now,
                    )
                    db.add(alert)
                    triggered_alerts.append(alert)

        # ── Humidity ───────────────────────────────────────────────────────
        if reading.humidity is not None:
            hum_status = evaluate_humidity_status(reading.humidity, humidity_max)
            if hum_status == SensorStatus.WARNING:
                if not await _alert_on_cooldown(db, reading.device_id, pit_id, AlertType.HUMIDITY_TOO_HIGH, COOLDOWN_MINUTES):
                    alert = _create_alert(
                        workshop_id=workshop_id,
                        pit_id=pit_id,
                        device_id=reading.device_id,
                        alert_type=AlertType.HUMIDITY_TOO_HIGH,
                        severity=AlertSeverity.WARNING,
                        message=(
                            f"Humidity {reading.humidity:.1f}% exceeded max threshold of {humidity_max}%"
                        ),
                        trigger_value=reading.humidity,
                        threshold_value=humidity_max,
                        now=now,
                    )
                    db.add(alert)
                    triggered_alerts.append(alert)

        # ── PM2.5 ──────────────────────────────────────────────────────────
        if reading.pm25 is not None:
            pm25_status = evaluate_pm25_status(reading.pm25, pm25_warning, pm25_critical)
            if pm25_status in (SensorStatus.WARNING, SensorStatus.CRITICAL):
                if not await _alert_on_cooldown(db, reading.device_id, pit_id, AlertType.HIGH_PM25, COOLDOWN_MINUTES):
                    severity = (
                        AlertSeverity.CRITICAL
                        if pm25_status == SensorStatus.CRITICAL
                        else AlertSeverity.WARNING
                    )
                    threshold = pm25_critical if pm25_status == SensorStatus.CRITICAL else pm25_warning
                    alert = _create_alert(
                        workshop_id=workshop_id,
                        pit_id=pit_id,
                        device_id=reading.device_id,
                        alert_type=AlertType.HIGH_PM25,
                        severity=severity,
                        message=(
                            f"PM2.5 level {reading.pm25:.1f} μg/m³ exceeded "
                            f"{'critical' if severity == AlertSeverity.CRITICAL else 'warning'} "
                            f"threshold of {threshold} μg/m³"
                        ),
                        trigger_value=reading.pm25,
                        threshold_value=threshold,
                        now=now,
                    )
                    db.add(alert)
                    triggered_alerts.append(alert)

        # ── BME680 IAQ ─────────────────────────────────────────────────────
        if reading.iaq is not None:
            iaq_status = evaluate_iaq_status(reading.iaq, iaq_warning, iaq_critical)
            if iaq_status in (SensorStatus.WARNING, SensorStatus.CRITICAL):
                if not await _alert_on_cooldown(db, reading.device_id, pit_id, AlertType.HIGH_IAQ, COOLDOWN_MINUTES):
                    severity = (
                        AlertSeverity.CRITICAL
                        if iaq_status == SensorStatus.CRITICAL
                        else AlertSeverity.WARNING
                    )
                    threshold = iaq_critical if iaq_status == SensorStatus.CRITICAL else iaq_warning
                    alert = _create_alert(
                        workshop_id=workshop_id,
                        pit_id=pit_id,
                        device_id=reading.device_id,
                        alert_type=AlertType.HIGH_IAQ,
                        severity=severity,
                        message=(
                            f"IAQ level {reading.iaq:.1f} exceeded "
                            f"{'critical' if severity == AlertSeverity.CRITICAL else 'warning'} "
                            f"threshold of {threshold}"
                        ),
                        trigger_value=reading.iaq,
                        threshold_value=threshold,
                        now=now,
                    )
                    db.add(alert)
                    triggered_alerts.append(alert)

        if triggered_alerts:
            logger.info(
                f"Generated {len(triggered_alerts)} alert(s) for pit_id={pit_id} "
                f"workshop_id={workshop_id}"
            )

    except Exception as e:
        logger.error(
            f"Alert evaluation failed for pit_id={pit_id}: {e}",
            exc_info=True
        )

    return triggered_alerts


async def _alert_on_cooldown(
    db: AsyncSession,
    device_id: str,
    pit_id: int,
    alert_type: str,
    cooldown_minutes: int,
) -> bool:
    """Check if an unacknowledged alert of the same type exists within cooldown window."""
    cutoff = utc_now() - timedelta(minutes=cooldown_minutes)
    result = await db.execute(
        select(Alert.id).where(
            and_(
                Alert.device_id == device_id,
                Alert.pit_id == pit_id,
                Alert.alert_type == alert_type,
                Alert.is_acknowledged == False,
                Alert.created_at >= cutoff,
            )
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


def _create_alert(
    workshop_id: int,
    pit_id: int,
    device_id: str,
    alert_type: str,
    severity: str,
    message: str,
    trigger_value: float,
    threshold_value: float,
    now: datetime,
) -> Alert:
    """Create an Alert ORM instance (not yet committed)."""
    return Alert(
        workshop_id=workshop_id,
        pit_id=pit_id,
        device_id=device_id,
        alert_type=alert_type,
        severity=severity,
        message=message,
        trigger_value=trigger_value,
        threshold_value=threshold_value,
        is_acknowledged=False,
        sms_sent=False,
        email_sent=False,
        created_at=now,
    )


def _safe_float(value) -> Optional[float]:
    """Safely convert a value to float, returning None on failure."""
    if value is None:
        return None
    try:
        result = float(value)
        # Sanity check: reject obviously corrupted values
        if result != result:  # NaN check
            return None
        return result
    except (TypeError, ValueError):
        return None


def _safe_int(value) -> Optional[int]:
    """Safely convert a value to int, returning None on failure."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
