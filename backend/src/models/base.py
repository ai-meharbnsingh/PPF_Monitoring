"""
Module: base.py
Purpose:
    SQLAlchemy ORM base model with common timestamp columns.
    All models inherit from TimestampMixin for created_at/updated_at.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from src.config.database import Base


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns to any model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
