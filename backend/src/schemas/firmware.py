"""
Module: firmware.py
Purpose:
    Pydantic schemas for firmware upload, listing, and OTA trigger endpoints.

Author: PPF Monitoring Team
Created: 2026-02-25
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ─── Response schemas ────────────────────────────────────────────────────────

class FirmwareReleaseOut(BaseModel):
    """Full firmware release info returned by list/detail endpoints."""
    id: int
    version: str
    filename: str
    file_size: int
    checksum_sha256: str
    release_notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FirmwareUploadResponse(BaseModel):
    """Response after successful firmware upload."""
    id: int
    version: str
    filename: str
    file_size: int
    checksum_sha256: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FirmwareLatestOut(BaseModel):
    """Lightweight response for ESP32 version check."""
    version: str
    file_size: int
    checksum_sha256: str
    download_url: str


# ─── Request schemas ─────────────────────────────────────────────────────────

class FirmwareTriggerRequest(BaseModel):
    """Request body for triggering OTA on a device."""
    version: Optional[str] = Field(
        None,
        description="Firmware version to push. Defaults to latest if omitted.",
    )
