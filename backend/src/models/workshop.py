"""
Module: workshop.py
Purpose:
    Workshop ORM model — represents a PPF business location (top-level tenant).

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
    from src.models.user import User
    from src.models.pit import Pit
    from src.models.device import Device
    from src.models.subscription import Subscription
    from src.models.alert import Alert, AlertConfig
    from src.models.job import Job


class Workshop(Base, TimestampMixin):
    __tablename__ = "workshops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    owner_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", use_alter=True, name="fk_workshop_owner"),
        nullable=True
    )
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    total_pits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    subscription_plan: Mapped[str] = mapped_column(String(20), default="trial", nullable=False)
    subscription_status: Mapped[str] = mapped_column(String(20), default="trial", nullable=False)
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────
    pits: Mapped[List["Pit"]] = relationship("Pit", back_populates="workshop", lazy="selectin")
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="workshop",
        foreign_keys="User.workshop_id",
        lazy="selectin"
    )
    devices: Mapped[List["Device"]] = relationship("Device", back_populates="workshop")
    subscriptions: Mapped[List["Subscription"]] = relationship("Subscription", back_populates="workshop")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="workshop")
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="workshop")
    alert_config: Mapped[Optional["AlertConfig"]] = relationship(
        "AlertConfig", back_populates="workshop", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Workshop id={self.id} name='{self.name}' status={self.subscription_status}>"
