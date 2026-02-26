"""
Module: pit_alert_config.py
Purpose:
    Per-pit alert threshold overrides.
    NULL fields inherit from the workshop-level AlertConfig.

Author: PPF Monitoring Team
Created: 2026-02-26
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base
from src.models.base import TimestampMixin

if TYPE_CHECKING:
    from src.models.pit import Pit


class PitAlertConfig(Base, TimestampMixin):
    """Optional per-pit alert threshold overrides.

    Every field is nullable. When evaluating alerts, a non-null value
    here takes precedence over the workshop-level AlertConfig default.
    """

    __tablename__ = "pit_alert_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pits.id"), unique=True, nullable=False
    )

    # Temperature thresholds (°C)
    temp_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temp_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Humidity threshold (%)
    humidity_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # PM2.5 thresholds (μg/m³)
    pm25_warning: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pm25_critical: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # PM10 thresholds (μg/m³)
    pm10_warning: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pm10_critical: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # BME680 IAQ thresholds
    iaq_warning: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    iaq_critical: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Offline detection (seconds)
    device_offline_threshold_seconds: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────
    pit: Mapped["Pit"] = relationship("Pit", back_populates="alert_config")

    def __repr__(self) -> str:
        return f"<PitAlertConfig pit_id={self.pit_id}>"
