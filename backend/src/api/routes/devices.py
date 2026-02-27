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
    DeviceApproveRequest,
    DeviceAssignRequest,
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


# ─── List pending devices (super_admin / owner) ─────────────────────────────
@router.get("/devices/pending", response_model=list[DeviceResponse])
async def list_pending_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """List all devices with status='pending'. super_admin or owner."""
    from sqlalchemy import select
    from src.models.device import Device
    from src.utils.constants import UserRole

    query = select(Device).where(Device.status == "pending")
    if current_user.role != UserRole.SUPER_ADMIN.value:
        # Owners see pending devices not yet assigned or assigned to their workshop
        query = query.where(
            (Device.workshop_id == None)  # noqa: E711
            | (Device.workshop_id == current_user.workshop_id)
        )
    result = await db.execute(query)
    devices = result.scalars().all()
    return [DeviceResponse.model_validate(d) for d in devices]


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


# ─── Approve pending device ──────────────────────────────────────────────────
@router.post("/devices/{device_id}/approve", response_model=DeviceResponse)
async def approve_device(
    device_id: str,
    payload: DeviceApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """
    Approve a pending device: generate license key, assign to workshop,
    create subscription, and publish provisioning config via MQTT.
    """
    from sqlalchemy import select
    from src.models.device import Device
    from src.models.subscription import Subscription
    from src.services.device_service import _unique_license_key
    from src.services.mqtt_service import publish_provisioning_config
    from src.utils.constants import (
        DeviceStatus,
        SubscriptionPlan,
        SubscriptionStatus,
        UserRole,
    )

    # Look up device
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    if device.status != DeviceStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device is not pending (current status: {device.status})",
        )

    # Access check: owner can only approve for their own workshop
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != payload.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Generate unique license key
    license_key = await _unique_license_key(db)

    # Update device
    device.license_key = license_key
    device.workshop_id = payload.workshop_id
    device.status = DeviceStatus.ACTIVE.value
    await db.flush()

    # Create subscription (trial, active, same pattern as register_device)
    subscription = Subscription(
        workshop_id=payload.workshop_id,
        device_id=device.device_id,
        license_key=license_key,
        plan=SubscriptionPlan.TRIAL.value,
        status=SubscriptionStatus.ACTIVE.value,
        grace_period_days=7,
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(device)

    # Publish provisioning config to device via MQTT
    publish_provisioning_config(
        device_id=device.device_id,
        license_key=license_key,
        workshop_id=payload.workshop_id,
    )

    logger.info(
        f"Device approved: device_id='{device.device_id}' "
        f"workshop_id={payload.workshop_id} license='{license_key}'"
    )
    return DeviceResponse.model_validate(device)


# ─── Assign device to pit ────────────────────────────────────────────────────
@router.put("/devices/{device_id}/assign", response_model=DeviceResponse)
async def assign_device(
    device_id: str,
    payload: DeviceAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """Assign an active device to a specific workshop pit."""
    from src.services.mqtt_service import publish_device_command
    from src.utils.constants import DeviceStatus, UserRole

    device = await device_service.get_device_by_device_id(db, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    if device.status != DeviceStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device must be active to assign (current status: {device.status})",
        )

    # Access check
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != payload.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Update device record
    device.workshop_id = payload.workshop_id
    device.pit_id = payload.pit_id
    await db.commit()
    await db.refresh(device)

    # Publish ASSIGN command to device via MQTT
    publish_device_command(
        workshop_id=payload.workshop_id,
        device_id=device.device_id,
        command="ASSIGN",
        reason="Pit assignment from dashboard",
        payload={"workshop_id": payload.workshop_id, "pit_id": payload.pit_id},
    )

    logger.info(
        f"Device assigned: device_id='{device.device_id}' "
        f"workshop_id={payload.workshop_id} pit_id={payload.pit_id}"
    )
    return DeviceResponse.model_validate(device)
