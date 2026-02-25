"""
Module: sensors.py
Purpose:
    Sensor data read endpoints.
    Latest reading per pit, historical data with pagination,
    aggregate stats for dashboard charts.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_staff_or_above, require_workshop_access
from src.config.database import get_db
from src.models.device import Device
from src.models.pit import Pit
from src.models.sensor_data import SensorData
from src.models.user import User
from src.schemas.common import build_paginated
from src.schemas.sensor_data import LatestSensorSummary, SensorReadingResponse, SensorStatsResponse
from src.utils.constants import UserRole
from src.utils.helpers import (
    evaluate_humidity_status,
    evaluate_iaq_status,
    evaluate_pm25_status,
    evaluate_temperature_status,
)
from src.utils.logger import get_logger

router = APIRouter(tags=["sensors"])
logger = get_logger(__name__)

# Default alert thresholds if no AlertConfig exists yet
_DEFAULT_TEMP_MIN = 15.0
_DEFAULT_TEMP_MAX = 35.0
_DEFAULT_HUMIDITY_MAX = 70.0
_DEFAULT_PM25_WARNING = 12.0
_DEFAULT_PM25_CRITICAL = 35.4
_DEFAULT_IAQ_WARNING = 100.0
_DEFAULT_IAQ_CRITICAL = 150.0


# ─── Latest reading for all pits in a workshop ────────────────────────────────
@router.get("/workshops/{workshop_id}/sensors/latest", response_model=list)
async def latest_readings_for_workshop(
    workshop_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_workshop_access()),
):
    """
    Latest sensor reading per pit for dashboard.
    Returns array of LatestSensorSummary, one per pit.
    """
    # Get all pits for this workshop
    pits_result = await db.execute(
        select(Pit).where(Pit.workshop_id == workshop_id).order_by(Pit.pit_number)
    )
    pits = pits_result.scalars().all()

    # Fetch alert config for thresholds
    thresholds = await _get_thresholds(db, workshop_id)
    summaries = []
    for pit in pits:
        summary = await _build_latest_summary(db, pit, thresholds)
        summaries.append(summary)
    return summaries


# ─── Latest reading for a single pit ─────────────────────────────────────────
@router.get("/pits/{pit_id}/sensors/latest")
async def latest_reading_for_pit(
    pit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_staff_or_above),
):
    """Latest sensor reading for one pit."""
    pit = await db.get(Pit, pit_id)
    if pit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pit not found")
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != pit.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    thresholds = await _get_thresholds(db, pit.workshop_id)
    return await _build_latest_summary(db, pit, thresholds)


# ─── Historical readings for a pit ────────────────────────────────────────────
@router.get("/pits/{pit_id}/sensors/history", response_model=dict)
async def sensor_history(
    pit_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    from_dt: Optional[datetime] = Query(default=None, description="ISO 8601 start (UTC)"),
    to_dt: Optional[datetime] = Query(default=None, description="ISO 8601 end (UTC)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_staff_or_above),
):
    """Paginated historical sensor readings for a pit."""
    pit = await db.get(Pit, pit_id)
    if pit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pit not found")
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != pit.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    query = select(SensorData).where(SensorData.pit_id == pit_id)
    if from_dt:
        query = query.where(SensorData.created_at >= from_dt)
    if to_dt:
        query = query.where(SensorData.created_at <= to_dt)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    rows_result = await db.execute(
        query.order_by(SensorData.created_at.desc()).offset(offset).limit(page_size)
    )
    rows = rows_result.scalars().all()
    items = [SensorReadingResponse.model_validate(r).model_dump() for r in rows]
    return build_paginated(items=items, total=total, page=page, page_size=page_size)


# ─── Aggregate stats for a pit ────────────────────────────────────────────────
@router.get("/pits/{pit_id}/sensors/stats")
async def sensor_stats(
    pit_id: int,
    hours: int = Query(default=24, ge=1, le=720, description="Lookback window in hours"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_staff_or_above),
):
    """Aggregate min/max/avg stats for a pit over the last N hours."""
    pit = await db.get(Pit, pit_id)
    if pit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pit not found")
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != pit.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    from datetime import timedelta
    since = datetime.now(tz=timezone.utc) - timedelta(hours=hours)

    agg = await db.execute(
        select(
            func.count(SensorData.id).label("reading_count"),
            func.avg(SensorData.temperature).label("temp_avg"),
            func.min(SensorData.temperature).label("temp_min"),
            func.max(SensorData.temperature).label("temp_max"),
            func.avg(SensorData.humidity).label("humidity_avg"),
            func.min(SensorData.humidity).label("humidity_min"),
            func.max(SensorData.humidity).label("humidity_max"),
            func.avg(SensorData.pm25).label("pm25_avg"),
            func.max(SensorData.pm25).label("pm25_max"),
            func.avg(SensorData.pm10).label("pm10_avg"),
            func.max(SensorData.pm10).label("pm10_max"),
            func.avg(SensorData.iaq).label("iaq_avg"),
            func.max(SensorData.iaq).label("iaq_max"),
        ).where(
            SensorData.pit_id == pit_id,
            SensorData.created_at >= since,
            SensorData.is_valid.is_(True),
        )
    )
    row = agg.one()

    def _round(v, n=2):
        return round(float(v), n) if v is not None else None

    return {
        "pit_id": pit_id,
        "device_id": pit.device.device_id if pit.device else None,
        "period_start": since,
        "period_end": datetime.now(tz=timezone.utc),
        "reading_count": row.reading_count,
        "temp_avg": _round(row.temp_avg),
        "temp_min": _round(row.temp_min),
        "temp_max": _round(row.temp_max),
        "humidity_avg": _round(row.humidity_avg),
        "humidity_min": _round(row.humidity_min),
        "humidity_max": _round(row.humidity_max),
        "pm25_avg": _round(row.pm25_avg),
        "pm25_max": _round(row.pm25_max),
        "pm10_avg": _round(row.pm10_avg),
        "pm10_max": _round(row.pm10_max),
        "iaq_avg": _round(row.iaq_avg),
        "iaq_max": _round(row.iaq_max),
    }


# ─── Internal helpers ─────────────────────────────────────────────────────────
async def _get_thresholds(db: AsyncSession, workshop_id: int) -> dict:
    from src.models.alert import AlertConfig
    result = await db.execute(
        select(AlertConfig).where(AlertConfig.workshop_id == workshop_id)
    )
    cfg = result.scalar_one_or_none()
    if cfg:
        return {
            "temp_min": cfg.temp_min,
            "temp_max": cfg.temp_max,
            "humidity_max": cfg.humidity_max,
            "pm25_warning": cfg.pm25_warning,
            "pm25_critical": cfg.pm25_critical,
            "iaq_warning": cfg.iaq_warning,
            "iaq_critical": cfg.iaq_critical,
        }
    return {
        "temp_min": _DEFAULT_TEMP_MIN,
        "temp_max": _DEFAULT_TEMP_MAX,
        "humidity_max": _DEFAULT_HUMIDITY_MAX,
        "pm25_warning": _DEFAULT_PM25_WARNING,
        "pm25_critical": _DEFAULT_PM25_CRITICAL,
        "iaq_warning": _DEFAULT_IAQ_WARNING,
        "iaq_critical": _DEFAULT_IAQ_CRITICAL,
    }


async def _build_latest_summary(db: AsyncSession, pit: Pit, thresholds: dict) -> dict:
    result = await db.execute(
        select(SensorData)
        .where(SensorData.pit_id == pit.id, SensorData.is_valid.is_(True))
        .order_by(SensorData.created_at.desc())
        .limit(1)
    )
    reading = result.scalar_one_or_none()
    device = pit.device

    if reading is None:
        return {
            "pit_id": pit.id,
            "device_id": device.device_id if device else None,
            "is_device_online": device.is_online if device else False,
            "temperature": None,
            "humidity": None,
            "pm25": None,
            "pm10": None,
            "iaq": None,
            "pressure": None,
            "gas_resistance": None,
            "temp_status": "unknown",
            "humidity_status": "unknown",
            "pm25_status": "unknown",
            "pm10_status": "unknown",
            "iaq_status": "unknown",
            "last_reading_at": None,
        }

    return {
        "pit_id": pit.id,
        "device_id": device.device_id if device else None,
        "is_device_online": device.is_online if device else False,
        "temperature": reading.temperature,
        "humidity": reading.humidity,
        "pm25": reading.pm25,
        "pm10": reading.pm10,
        "iaq": reading.iaq,
        "pressure": reading.pressure,
        "gas_resistance": reading.gas_resistance,
        "temp_status": evaluate_temperature_status(
            reading.temperature, thresholds["temp_min"], thresholds["temp_max"]
        ).value,
        "humidity_status": evaluate_humidity_status(
            reading.humidity, thresholds["humidity_max"]
        ).value,
        "pm25_status": evaluate_pm25_status(
            reading.pm25, thresholds["pm25_warning"], thresholds["pm25_critical"]
        ).value,
        "pm10_status": evaluate_pm25_status(   # same logic, different thresholds
            reading.pm10,
            thresholds.get("pm10_warning", 54.0),
            thresholds.get("pm10_critical", 154.0),
        ).value,
        "iaq_status": evaluate_iaq_status(
            reading.iaq, thresholds["iaq_warning"], thresholds["iaq_critical"]
        ).value,
        "last_reading_at": reading.created_at,
    }
