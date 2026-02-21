"""
Module: sensor_data.py
Purpose:
    SensorData ORM model — time-series table for all sensor readings.
    Supports DHT22+PMS5003 (primary hardware) AND BME680 (alternative) via
    nullable columns. Sensor type fields indicate which sensor populated each row.

    DHT22 fields:   temperature, humidity
    PMS5003 fields: pm1, pm25, pm10, particles_*
    BME680 fields:  temperature, humidity, pressure, gas_resistance, iaq, iaq_accuracy

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base

if TYPE_CHECKING:
    from src.models.device import Device
    from src.models.pit import Pit
    from src.models.workshop import Workshop


class SensorData(Base):
    __tablename__ = "sensor_data"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    # ── Device / Location context ──────────────────────────────────────────
    device_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("devices.device_id"), nullable=False
    )
    pit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pits.id"), nullable=False
    )
    workshop_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workshops.id"), nullable=False
    )

    # ── Sensor type context ────────────────────────────────────────────────
    primary_sensor_type: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )  # 'DHT22' | 'BME680'
    air_quality_sensor_type: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )  # 'PMS5003' | 'BME680' | None

    # ── DHT22 / BME680 shared ─────────────────────────────────────────────
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)   # Celsius
    humidity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)      # %

    # ── BME680 only (NULL for DHT22) ──────────────────────────────────────
    pressure: Mapped[Optional[float]] = mapped_column(Float, nullable=True)      # hPa
    gas_resistance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Ohms
    iaq: Mapped[Optional[float]] = mapped_column(Float, nullable=True)           # IAQ 0-500
    iaq_accuracy: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # BSEC 0-3

    # ── PMS5003 (NULL for BME680-only setups) ─────────────────────────────
    pm1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)           # μg/m³
    pm25: Mapped[Optional[float]] = mapped_column(Float, nullable=True)          # μg/m³
    pm10: Mapped[Optional[float]] = mapped_column(Float, nullable=True)          # μg/m³

    # Particle counts (optional — PMS5003 advanced data)
    particles_03um: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    particles_05um: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    particles_10um: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    particles_25um: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    particles_50um: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    particles_100um: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ── Data quality ──────────────────────────────────────────────────────
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    validation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────
    device_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # Timestamp from ESP32 clock
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )  # Server ingestion time

    # ── Relationships ──────────────────────────────────────────────────────
    device: Mapped["Device"] = relationship("Device", back_populates="sensor_readings")
    pit: Mapped["Pit"] = relationship("Pit", back_populates="sensor_readings")

    def __repr__(self) -> str:
        return (
            f"<SensorData pit_id={self.pit_id} "
            f"temp={self.temperature} humidity={self.humidity} "
            f"pm25={self.pm25} at={self.created_at}>"
        )
