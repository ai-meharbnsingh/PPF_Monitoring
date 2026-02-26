"""
Module: pit.py
Purpose:
    Pit ORM model — represents one physical work bay inside a workshop.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base
from src.models.base import TimestampMixin

if TYPE_CHECKING:
    from src.models.workshop import Workshop
    from src.models.device import Device
    from src.models.job import Job
    from src.models.sensor_data import SensorData
    from src.models.alert import Alert
    from src.models.pit_alert_config import PitAlertConfig


class Pit(Base, TimestampMixin):
    __tablename__ = "pits"
    __table_args__ = (
        UniqueConstraint("workshop_id", "pit_number", name="uq_pit_workshop_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workshop_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workshops.id"), nullable=False
    )
    pit_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)

    # Camera config
    camera_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    camera_rtsp_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    camera_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    camera_username: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    camera_is_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    camera_last_seen: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────
    workshop: Mapped["Workshop"] = relationship("Workshop", back_populates="pits")
    device: Mapped[Optional["Device"]] = relationship(
        "Device", back_populates="pit", uselist=False, lazy="selectin"
    )
    jobs: Mapped[List["Job"]] = relationship(
        "Job", back_populates="pit", order_by="Job.created_at.desc()"
    )
    sensor_readings: Mapped[List["SensorData"]] = relationship(
        "SensorData", back_populates="pit"
    )
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="pit")
    alert_config: Mapped[Optional["PitAlertConfig"]] = relationship(
        "PitAlertConfig", back_populates="pit", uselist=False, lazy="selectin"
    )

    @property
    def display_name(self) -> str:
        return self.name or f"Pit {self.pit_number}"

    def __repr__(self) -> str:
        return f"<Pit id={self.id} workshop_id={self.workshop_id} pit_number={self.pit_number}>"
