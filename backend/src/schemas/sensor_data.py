"""
Module: sensor_data.py
Purpose:
    Pydantic schemas for sensor data endpoints.
    Supports DHT22+PMS5003 (primary hardware) AND BME680 (alternative)
    via optional nullable fields — mirrors the sensor_data ORM model.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ─── Response ─────────────────────────────────────────────────────────────────
class SensorReadingResponse(BaseModel):
    """
    One sensor reading row.
    Fields not applicable to the current sensor config will be None.

    DHT22 fields:    temperature, humidity
    PMS5003 fields:  pm1, pm25, pm10, particles_*
    BME680 fields:   temperature, humidity, pressure, gas_resistance, iaq, iaq_accuracy
    """

    id: int
    device_id: str
    pit_id: int
    workshop_id: int

    # Sensor type context
    primary_sensor_type: Optional[str]   # 'DHT22' | 'BME680'
    air_quality_sensor_type: Optional[str]  # 'PMS5003' | 'BME680' | None

    # ── DHT22 / BME680 shared ─────────────────────────────────────────────
    temperature: Optional[float] = Field(None, description="°C")
    humidity: Optional[float] = Field(None, description="% RH")

    # ── BME680 only ───────────────────────────────────────────────────────
    pressure: Optional[float] = Field(None, description="hPa")
    gas_resistance: Optional[float] = Field(None, description="Ohms")
    iaq: Optional[float] = Field(None, description="IAQ index 0–500")
    iaq_accuracy: Optional[int] = Field(None, description="BSEC accuracy 0–3")

    # ── PMS5003 ───────────────────────────────────────────────────────────
    pm1: Optional[float] = Field(None, description="PM1.0 μg/m³")
    pm25: Optional[float] = Field(None, description="PM2.5 μg/m³")
    pm10: Optional[float] = Field(None, description="PM10 μg/m³")

    # Particle counts
    particles_03um: Optional[int] = None
    particles_05um: Optional[int] = None
    particles_10um: Optional[int] = None
    particles_25um: Optional[int] = None
    particles_50um: Optional[int] = None
    particles_100um: Optional[int] = None

    # Quality flag
    is_valid: bool
    validation_notes: Optional[str]

    # Timestamps
    device_timestamp: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Latest reading summary (dashboard) ──────────────────────────────────────
class LatestSensorSummary(BaseModel):
    """Condensed snapshot for pit dashboard cards."""

    pit_id: int
    device_id: str
    is_device_online: bool

    # Environment
    temperature: Optional[float]
    humidity: Optional[float]
    pm25: Optional[float]
    pm10: Optional[float]
    iaq: Optional[float]

    # Status labels (good / warning / critical / unknown)
    temp_status: str
    humidity_status: str
    pm25_status: str
    pm10_status: str
    iaq_status: str

    last_reading_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ─── History stats ────────────────────────────────────────────────────────────
class SensorStatsResponse(BaseModel):
    """Aggregate stats for a sensor over a time range."""

    pit_id: int
    device_id: str
    period_start: datetime
    period_end: datetime
    reading_count: int

    temp_avg: Optional[float]
    temp_min: Optional[float]
    temp_max: Optional[float]

    humidity_avg: Optional[float]
    humidity_min: Optional[float]
    humidity_max: Optional[float]

    pm25_avg: Optional[float]
    pm25_max: Optional[float]

    pm10_avg: Optional[float]
    pm10_max: Optional[float]

    iaq_avg: Optional[float]
    iaq_max: Optional[float]
