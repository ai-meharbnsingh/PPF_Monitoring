"""
Module: firmware.py
Purpose:
    Firmware management API routes for OTA updates.
    Upload .bin files, list releases, download binaries, and trigger device OTA.

    - POST   /firmware/upload              — Upload a new firmware binary (owner+)
    - GET    /firmware/releases            — List all firmware releases (staff+)
    - GET    /firmware/latest              — Get latest version info (public for ESP32)
    - GET    /firmware/download/{version}  — Download .bin file (public for ESP32)
    - POST   /firmware/trigger-ota/{device_id} — Push OTA to a device (owner+)

Author: PPF Monitoring Team
Created: 2026-02-25
"""

import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_owner_or_admin, get_staff_or_above
from src.config.database import get_db
from src.config.settings import get_settings
from src.models.user import User
from src.schemas.firmware import (
    FirmwareLatestOut,
    FirmwareReleaseOut,
    FirmwareTriggerRequest,
    FirmwareUploadResponse,
)
from src.services import firmware_service
from src.services.device_service import get_device_by_device_id
from src.utils.logger import get_logger

router = APIRouter(tags=["firmware"])
logger = get_logger(__name__)
settings = get_settings()


# ─── Upload firmware binary ──────────────────────────────────────────────────
@router.post(
    "/firmware/upload",
    response_model=FirmwareUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_firmware(
    version: str = Form(..., description="Semantic version (e.g. 1.1.0)"),
    release_notes: str = Form(None, description="Optional release notes"),
    file: UploadFile = File(..., description="Firmware .bin file"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """Upload a new firmware binary. Requires owner or super_admin role."""
    # Validate file extension
    if file.filename and not file.filename.endswith(".bin"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Firmware file must be a .bin file",
        )

    # Check version doesn't already exist
    existing = await firmware_service.get_release_by_version(db, version)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Firmware version {version} already exists",
        )

    release = await firmware_service.upload_firmware(
        db=db,
        file=file,
        version=version,
        release_notes=release_notes,
        user_id=current_user.id,
    )
    return FirmwareUploadResponse.model_validate(release)


# ─── List all releases ───────────────────────────────────────────────────────
@router.get("/firmware/releases", response_model=list[FirmwareReleaseOut])
async def list_releases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_staff_or_above),
):
    """List all firmware releases, newest first. Requires staff+ role."""
    releases = await firmware_service.list_releases(db)
    return [FirmwareReleaseOut.model_validate(r) for r in releases]


# ─── Get latest version (for ESP32 polling) ─────────────────────────────────
@router.get("/firmware/latest", response_model=FirmwareLatestOut)
async def get_latest(
    db: AsyncSession = Depends(get_db),
):
    """Get the latest firmware version info. Public endpoint for ESP32 devices."""
    release = await firmware_service.get_latest_release(db)
    if not release:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No firmware releases found",
        )

    download_url = f"{settings.API_PREFIX}/firmware/download/{release.version}"
    return FirmwareLatestOut(
        version=release.version,
        file_size=release.file_size,
        checksum_sha256=release.checksum_sha256,
        download_url=download_url,
    )


# ─── Download firmware binary ────────────────────────────────────────────────
@router.get("/firmware/download/{version}")
async def download_firmware(
    version: str,
    db: AsyncSession = Depends(get_db),
):
    """Download a firmware .bin file by version. Public for ESP32 HTTPUpdate."""
    release = await firmware_service.get_release_by_version(db, version)
    if not release:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Firmware version {version} not found",
        )

    if not os.path.exists(release.file_path):
        logger.error(f"Firmware file missing from disk: {release.file_path}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Firmware file not found on server",
        )

    return FileResponse(
        path=release.file_path,
        filename=release.filename,
        media_type="application/octet-stream",
    )


# ─── Trigger OTA on a device ────────────────────────────────────────────────
@router.post("/firmware/trigger-ota/{device_id}")
async def trigger_ota(
    device_id: str,
    body: FirmwareTriggerRequest = FirmwareTriggerRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """
    Send UPDATE_FIRMWARE command to a device via MQTT.
    The device will pull the firmware from the download endpoint.
    Requires owner or super_admin role.
    """
    # Look up the device
    device = await get_device_by_device_id(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found",
        )

    # Resolve firmware version
    if body.version:
        release = await firmware_service.get_release_by_version(db, body.version)
    else:
        release = await firmware_service.get_latest_release(db)

    if not release:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No firmware release found",
        )

    # Build the download URL the ESP32 will use
    # Use the server's base URL so the ESP32 can reach it on the local network
    base_url = f"http://{settings.SERVER_HOST}:{settings.SERVER_PORT}{settings.API_PREFIX}"
    firmware_url = f"{base_url}/firmware/download/{release.version}"

    success = firmware_service.trigger_device_ota(
        workshop_id=device.workshop_id,
        device_id=device.device_id,
        firmware_url=firmware_url,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to publish OTA command via MQTT",
        )

    return {
        "status": "ok",
        "message": f"OTA command sent to {device_id}",
        "version": release.version,
        "firmware_url": firmware_url,
    }
