"""
Module: alert.py
Purpose:
    Alert and AlertConfig ORM models.
    Alert: triggered system notifications.
    AlertConfig: per-workshop customizable thresholds.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base
from src.models.base import TimestampMixin

if TYPE_CHECKING:
    from src.models.workshop import Workshop
    from src.models.pit import Pit
    from src.models.user import User


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workshop_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workshops.id"), nullable=False
    )
    pit_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("pits.id"), nullable=True
    )
    device_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("devices.device_id"), nullable=True
    )
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    threshold_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sms_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────
    workshop: Mapped["Workshop"] = relationship("Workshop", back_populates="alerts")
    pit: Mapped[Optional["Pit"]] = relationship("Pit", back_populates="alerts")

    def __repr__(self) -> str:
        return (
            f"<Alert id={self.id} type={self.alert_type} "
            f"severity={self.severity} ack={self.is_acknowledged}>"
        )


class AlertConfig(Base, TimestampMixin):
    """Per-workshop alert threshold configuration."""
    __tablename__ = "alert_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workshop_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workshops.id"), unique=True, nullable=False
    )

    # Temperature thresholds (°C)
    temp_min: Mapped[float] = mapped_column(Float, default=15.0, nullable=False)
    temp_max: Mapped[float] = mapped_column(Float, default=35.0, nullable=False)

    # Humidity threshold (%)
    humidity_max: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)

    # PM2.5 thresholds (μg/m³) — WHO 2021
    pm25_warning: Mapped[float] = mapped_column(Float, default=12.0, nullable=False)
    pm25_critical: Mapped[float] = mapped_column(Float, default=35.4, nullable=False)

    # PM10 thresholds (μg/m³)
    pm10_warning: Mapped[float] = mapped_column(Float, default=54.0, nullable=False)
    pm10_critical: Mapped[float] = mapped_column(Float, default=154.0, nullable=False)

    # BME680 IAQ thresholds
    iaq_warning: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    iaq_critical: Mapped[float] = mapped_column(Float, default=150.0, nullable=False)

    # Offline detection
    device_offline_threshold_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    camera_offline_threshold_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    # Notification channels
    notify_via_sms: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_via_email: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notify_via_webhook: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    webhook_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────
    workshop: Mapped["Workshop"] = relationship("Workshop", back_populates="alert_config")

    def __repr__(self) -> str:
        return f"<AlertConfig workshop_id={self.workshop_id}>"
