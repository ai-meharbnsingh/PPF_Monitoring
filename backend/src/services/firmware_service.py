"""
Module: firmware_service.py
Purpose:
    Business logic for firmware upload, retrieval, and OTA trigger dispatch.
    Handles file storage, SHA-256 checksums, and MQTT command publishing.

Author: PPF Monitoring Team
Created: 2026-02-25
"""

import hashlib
import os
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.firmware_release import FirmwareRelease
from src.services.mqtt_service import publish_device_command
from src.utils.constants import DeviceCommand
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Storage directory for firmware binaries (Docker volume or local path)
FIRMWARE_DIR = os.environ.get("FIRMWARE_UPLOAD_DIR", "/app/firmware_uploads")


async def upload_firmware(
    db: AsyncSession,
    file: UploadFile,
    version: str,
    release_notes: Optional[str],
    user_id: int,
) -> FirmwareRelease:
    """
    Save an uploaded firmware .bin file and create a database record.

    Args:
        db: Database session
        file: Uploaded file (multipart)
        version: Semantic version string (e.g. "1.1.0")
        release_notes: Optional human-readable notes
        user_id: ID of the uploading user

    Returns:
        FirmwareRelease ORM instance
    """
    # Ensure upload directory exists
    os.makedirs(FIRMWARE_DIR, exist_ok=True)

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Compute SHA-256 checksum
    checksum = hashlib.sha256(content).hexdigest()

    # Save to disk: firmware_uploads/v1.1.0_firmware.bin
    safe_filename = f"v{version}_{file.filename or 'firmware.bin'}"
    file_path = os.path.join(FIRMWARE_DIR, safe_filename)
    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(f"Firmware saved: {file_path} ({file_size} bytes, sha256={checksum[:12]}…)")

    # Create DB record
    release = FirmwareRelease(
        version=version,
        filename=safe_filename,
        file_path=file_path,
        file_size=file_size,
        checksum_sha256=checksum,
        release_notes=release_notes,
        created_by=user_id,
    )
    db.add(release)
    await db.flush()
    await db.refresh(release)

    return release


async def get_latest_release(db: AsyncSession) -> Optional[FirmwareRelease]:
    """Get the most recently uploaded firmware release."""
    result = await db.execute(
        select(FirmwareRelease).order_by(FirmwareRelease.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def get_release_by_version(
    db: AsyncSession, version: str
) -> Optional[FirmwareRelease]:
    """Get a specific firmware release by version string."""
    result = await db.execute(
        select(FirmwareRelease).where(FirmwareRelease.version == version)
    )
    return result.scalar_one_or_none()


async def list_releases(db: AsyncSession) -> List[FirmwareRelease]:
    """List all firmware releases, newest first."""
    result = await db.execute(
        select(FirmwareRelease).order_by(FirmwareRelease.created_at.desc())
    )
    return list(result.scalars().all())


def trigger_device_ota(
    workshop_id: int,
    device_id: str,
    firmware_url: str,
) -> bool:
    """
    Send an UPDATE_FIRMWARE command to a device via MQTT.

    Args:
        workshop_id: Workshop the device belongs to
        device_id: Target device ID (e.g. "ESP32-083AF2A9F084")
        firmware_url: Full URL to the firmware .bin download endpoint

    Returns:
        True if MQTT publish succeeded
    """
    return publish_device_command(
        workshop_id=workshop_id,
        device_id=device_id,
        command=DeviceCommand.UPDATE_FIRMWARE,
        reason="OTA update triggered via API",
        payload={"url": firmware_url},
    )
