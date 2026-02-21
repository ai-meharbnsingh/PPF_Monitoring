"""
Module: subscription.py
Purpose:
    Subscription ORM model — device licensing and payment tracking.
    Powers the kill-switch mechanism.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base
from src.models.base import TimestampMixin

if TYPE_CHECKING:
    from src.models.workshop import Workshop
    from src.models.device import Device


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workshop_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workshops.id"), nullable=False
    )
    device_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("devices.device_id"), nullable=True
    )
    license_key: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(20), nullable=False, default="basic")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    monthly_fee: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    grace_period_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    last_payment_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_payment_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────
    workshop: Mapped["Workshop"] = relationship("Workshop", back_populates="subscriptions")
    device: Mapped[Optional["Device"]] = relationship(
        "Device",
        back_populates="subscription",
        foreign_keys=[device_id],
        primaryjoin="Subscription.device_id == Device.device_id"
    )

    def __repr__(self) -> str:
        return (
            f"<Subscription device_id='{self.device_id}' "
            f"plan={self.plan} status={self.status}>"
        )
