"""
Module: job.py
Purpose:
    Job and JobStatusHistory ORM models.
    Job represents one car work order. StatusHistory is an immutable audit trail.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    ARRAY, DateTime, ForeignKey, Integer, Numeric, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base
from src.models.base import TimestampMixin

if TYPE_CHECKING:
    from src.models.workshop import Workshop
    from src.models.pit import Pit
    from src.models.user import User


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workshop_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workshops.id"), nullable=False
    )
    pit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pits.id"), nullable=False
    )
    customer_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    # Car info
    car_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    car_plate: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    car_color: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    car_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Work details
    work_type: Mapped[str] = mapped_column(String(50), nullable=False)
    work_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(30), default="waiting", nullable=False)

    # Timestamps
    scheduled_start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    estimated_end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Staff (stored as array of user IDs)
    # Note: Using Text as JSON string for SQLite compat; use ARRAY(Integer) in PostgreSQL migration
    assigned_staff_ids_str: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, name="assigned_staff_ids"
    )

    # Customer access token
    customer_view_token: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )
    customer_view_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 6-digit tracking code for customer access
    tracking_code: Mapped[Optional[str]] = mapped_column(
        String(6), unique=True, nullable=True, index=True
    )

    # Notes
    owner_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    staff_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Pricing
    quoted_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)

    # Who created
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────
    workshop: Mapped["Workshop"] = relationship("Workshop", back_populates="jobs")
    pit: Mapped["Pit"] = relationship("Pit", back_populates="jobs")
    customer: Mapped[Optional["User"]] = relationship(
        "User", back_populates="customer_jobs", foreign_keys=[customer_user_id]
    )
    status_history: Mapped[List["JobStatusHistory"]] = relationship(
        "JobStatusHistory",
        back_populates="job",
        order_by="JobStatusHistory.created_at.asc()"
    )

    def __repr__(self) -> str:
        return (
            f"<Job id={self.id} pit_id={self.pit_id} "
            f"work_type='{self.work_type}' status={self.status}>"
        )


class JobStatusHistory(Base):
    """Immutable audit trail for job status transitions."""
    __tablename__ = "job_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id"), nullable=False
    )
    previous_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────
    job: Mapped["Job"] = relationship("Job", back_populates="status_history")

    def __repr__(self) -> str:
        return (
            f"<JobStatusHistory job_id={self.job_id} "
            f"{self.previous_status} → {self.new_status}>"
        )
