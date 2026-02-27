"""
Module: device.py
Purpose:
    Device ORM model — represents one Olimex ESP32-GATEWAY unit.
    Stores sensor configuration (DHT22+PMS5003 or BME680) and licensing.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base
from src.models.base import TimestampMixin

if TYPE_CHECKING:
    from src.models.pit import Pit
    from src.models.workshop import Workshop
    from src.models.sensor_data import SensorData
    from src.models.device_command import DeviceCommand
    from src.models.subscription import Subscription


class SensorType(Base):
    """Reference table for supported sensor hardware types."""
    __tablename__ = "sensor_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    protocol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # JSONB stored as Text for SQLite compat in dev; use JSONB type in production migration
    capabilities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<SensorType code='{self.code}' name='{self.name}'>"


class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pit_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("pits.id"), nullable=True
    )
    workshop_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("workshops.id"), nullable=True
    )
    # Unique device identity
    device_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    license_key: Mapped[Optional[str]] = mapped_column(String(30), unique=True, nullable=True)
    firmware_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Sensor configuration
    # primary_sensor: DHT22 (temp+humidity) or BME680 (temp+humidity+pressure+iaq)
    primary_sensor_type_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sensor_types.id"), nullable=True
    )
    # air_quality_sensor: PMS5003 (pm25/pm10) or NULL (BME680 handles own AQI)
    air_quality_sensor_type_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sensor_types.id"), nullable=True
    )

    # Network info
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)

    # Status & online tracking
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_mqtt_message: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Config
    report_interval_seconds: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────
    pit: Mapped[Optional["Pit"]] = relationship("Pit", back_populates="device")
    workshop: Mapped[Optional["Workshop"]] = relationship("Workshop", back_populates="devices")
    primary_sensor_type: Mapped[Optional[SensorType]] = relationship(
        "SensorType", foreign_keys=[primary_sensor_type_id], lazy="selectin"
    )
    air_quality_sensor_type: Mapped[Optional[SensorType]] = relationship(
        "SensorType", foreign_keys=[air_quality_sensor_type_id], lazy="selectin"
    )
    sensor_readings: Mapped[List["SensorData"]] = relationship(
        "SensorData", back_populates="device"
    )
    commands: Mapped[List["DeviceCommand"]] = relationship(
        "DeviceCommand", back_populates="device", order_by="DeviceCommand.created_at.desc()"
    )
    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription", back_populates="device", uselist=False,
        foreign_keys="Subscription.device_id",
        primaryjoin="Device.device_id == foreign(Subscription.device_id)"
    )

    @property
    def primary_sensor_code(self) -> Optional[str]:
        return self.primary_sensor_type.code if self.primary_sensor_type else None

    @property
    def air_quality_sensor_code(self) -> Optional[str]:
        return self.air_quality_sensor_type.code if self.air_quality_sensor_type else None

    def __repr__(self) -> str:
        return f"<Device device_id='{self.device_id}' status={self.status} online={self.is_online}>"
