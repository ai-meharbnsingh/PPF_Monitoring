"""
Module: firmware_release.py
Purpose:
    SQLAlchemy ORM model for firmware release records.
    Tracks uploaded firmware binaries with version, checksum, and metadata.

Author: PPF Monitoring Team
Created: 2026-02-25
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base
from src.models.base import TimestampMixin


class FirmwareRelease(Base, TimestampMixin):
    """Firmware binary release record — one row per uploaded .bin file."""

    __tablename__ = "firmware_releases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    release_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Who uploaded this firmware
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationship
    uploader: Mapped[Optional["User"]] = relationship(  # noqa: F821
        "User", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<FirmwareRelease v{self.version} ({self.filename})>"
