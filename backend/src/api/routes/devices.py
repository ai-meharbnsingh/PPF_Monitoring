"""
Module: devices.py
Purpose:
    Device registration, management, and command dispatch API routes.
    owner/super_admin: register, update, command.
    staff: read, send commands.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    get_current_user,
    get_owner_or_admin,
    get_staff_or_above,
    require_workshop_access,
)
from src.config.database import get_db
from src.models.user import User
from src.schemas.common import build_paginated
from src.schemas.device import (
    DeviceCommandRequest,
    DeviceCommandResponse,
    DeviceRegister,
    DeviceResponse,
    DeviceSummary,
    DeviceUpdate,
)
from src.services import device_service
from src.utils.logger import get_logger

router = APIRouter(tags=["devices"])
logger = get_logger(__name__)


# ─── List devices for a workshop ──────────────────────────────────────────────
@router.get("/workshops/{workshop_id}/devices", response_model=dict)
async def list_devices(
    workshop_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_workshop_access()),
):
    """List all registered devices for a workshop."""
    devices, total = await device_service.list_devices_for_workshop(
        db, workshop_id=workshop_id, page=page, page_size=page_size
    )
    items = [DeviceSummary.model_validate(d).model_dump() for d in devices]
    return build_paginated(items=items, total=total, page=page, page_size=page_size)


# ─── Register new device ──────────────────────────────────────────────────────
@router.post(
    "/workshops/{workshop_id}/devices",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_device(
    workshop_id: int,
    payload: DeviceRegister,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """Register a new ESP32 gateway device. owner or super_admin."""
    from src.utils.constants import UserRole
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    try:
        device = await device_service.register_device(db, workshop_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return DeviceResponse.model_validate(device)


# ─── Get single device ────────────────────────────────────────────────────────
@router.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_staff_or_above),
):
    """Get device detail. Access scoped by workshop membership."""
    device = await device_service.get_device_by_device_id(db, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    # Scope check
    from src.utils.constants import UserRole
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != device.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return DeviceResponse.model_validate(device)


# ─── Update device ────────────────────────────────────────────────────────────
@router.patch("/devices/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    payload: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """Update device config. owner or super_admin."""
    device = await device_service.get_device_by_device_id(db, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    from src.utils.constants import UserRole
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != device.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    try:
        updated = await device_service.update_device(db, device, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return DeviceResponse.model_validate(updated)


# ─── Send command to device ───────────────────────────────────────────────────
@router.post("/devices/{device_id}/command", response_model=DeviceCommandResponse)
async def send_command(
    device_id: str,
    payload: DeviceCommandRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_staff_or_above),
):
    """Send a command to a device via MQTT. staff, owner, or super_admin."""
    device = await device_service.get_device_by_device_id(db, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    from src.utils.constants import UserRole
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != device.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    try:
        cmd = await device_service.send_device_command(
            db, device, payload, issued_by_user_id=current_user.id
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to publish command to MQTT broker: {exc}",
        )
    return DeviceCommandResponse.model_validate(cmd)
