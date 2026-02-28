"""
Module: admin_devices.py
Purpose:
    Admin device provisioning and assignment management.
    Super admin can approve pending devices and assign to workshops.

Author: PPF Monitoring Team
Created: 2026-02-28
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_super_admin
from src.config.database import get_db
from src.models.device import Device
from src.models.pit import Pit
from src.models.user import User
from src.models.workshop import Workshop
from src.schemas.common import SuccessResponse, build_paginated
from src.schemas.device import DeviceResponse
from src.services.mqtt_service import publish_device_command
from src.utils.constants import DeviceStatus
from src.utils.helpers import generate_license_key, utc_now
from src.utils.logger import get_logger

router = APIRouter(prefix="/admin/devices", tags=["admin-devices"])
logger = get_logger(__name__)


# ─── List Pending Devices ─────────────────────────────────────────────────────
@router.get("/pending", response_model=dict)
async def list_pending_devices(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    """
    List all devices awaiting provisioning (status=pending or workshop_id=null).
    These are ESP32 devices that have announced themselves but not yet approved.
    """
    base_query = select(Device).where(
        (Device.status == DeviceStatus.PENDING.value) | 
        (Device.workshop_id.is_(None))
    )
    
    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()
    
    offset = (page - 1) * page_size
    result = await db.execute(
        base_query.order_by(Device.created_at.desc()).offset(offset).limit(page_size)
    )
    devices = result.scalars().all()
    
    items = []
    for d in devices:
        items.append({
            "device_id": d.device_id,
            "mac_address": d.mac_address,
            "firmware_version": d.firmware_version,
            "status": d.status,
            "primary_sensor_code": d.primary_sensor_code,
            "air_quality_sensor_code": d.air_quality_sensor_code,
            "is_online": d.is_online,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "ip_address": d.ip_address,
        })
    
    return build_paginated(items=items, total=total, page=page, page_size=page_size)


# ─── Approve and Assign Device to Workshop ────────────────────────────────────
class DeviceApproveRequest:
    workshop_id: int
    

@router.post("/{device_id}/approve", response_model=dict)
async def approve_device(
    device_id: str,
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    """
    Approve a pending device and assign it to a workshop.
    Auto-generates license key and sends provisioning config to device.
    """
    workshop_id = request.get("workshop_id")
    if not workshop_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="workshop_id is required"
        )
    
    # Verify workshop exists
    workshop = await db.get(Workshop, workshop_id)
    if not workshop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workshop {workshop_id} not found"
        )
    
    # Get device
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found"
        )
    
    # Generate unique license key
    license_key = generate_license_key()
    
    # Update device
    device.status = DeviceStatus.ACTIVE.value
    device.workshop_id = workshop_id
    device.license_key = license_key
    device.updated_at = utc_now()
    
    await db.commit()
    await db.refresh(device)
    
    # Send provisioning config to device via MQTT
    try:
        # Publish to provisioning topic - device is listening
        from src.services.mqtt_service import get_mqtt_client
        import json
        
        mqtt_client = get_mqtt_client()
        config_topic = f"provisioning/{device_id}/config"
        
        config_payload = {
            "license_key": license_key,
            "workshop_id": workshop_id,
            "pit_id": None,  # Owner will assign to pit later
            "mqtt_topic": f"workshop/{workshop_id}/pit/+/sensors",
            "command_topic": f"workshop/{workshop_id}/device/{device_id}/command",
            "approved_at": utc_now().isoformat(),
            "approved_by": current_user.username,
        }
        
        mqtt_client.publish(
            config_topic,
            json.dumps(config_payload),
            qos=1,
            retain=True,  # Retain so device gets it when it connects
        )
        
        logger.info(
            f"Device {device_id} approved and assigned to workshop {workshop_id}. "
            f"License: {license_key}"
        )
        
    except Exception as e:
        logger.error(f"Failed to send provisioning config to {device_id}: {e}")
        # Don't fail - device can poll for config
    
    return {
        "success": True,
        "message": f"Device {device_id} approved and assigned to workshop {workshop_id}",
        "device_id": device_id,
        "license_key": license_key,
        "workshop_id": workshop_id,
        "workshop_name": workshop.name,
    }


# ─── Reject Device ────────────────────────────────────────────────────────────
@router.post("/{device_id}/reject", response_model=SuccessResponse)
async def reject_device(
    device_id: str,
    request: dict = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    """
    Reject a pending device (set status to suspended).
    """
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found"
        )
    
    device.status = DeviceStatus.SUSPENDED.value
    device.updated_at = utc_now()
    
    await db.commit()
    
    reason = request.get("reason", "") if request else ""
    logger.info(f"Device {device_id} rejected by {current_user.username}. Reason: {reason}")
    
    return SuccessResponse(
        message=f"Device {device_id} has been rejected"
    )


# ─── List Device Assignments (All Workshops) ──────────────────────────────────
@router.get("/assignments", response_model=dict)
async def list_device_assignments(
    workshop_id: int = Query(default=None, description="Filter by workshop"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    """
    List all device assignments across all workshops.
    Shows Device → Workshop → Owner → Pit relationships.
    """
    # Build query with joins
    query = (
        select(
            Device,
            Workshop.name.label("workshop_name"),
            User.username.label("owner_username"),
            Pit.id.label("pit_id"),
            Pit.name.label("pit_name"),
        )
        .outerjoin(Workshop, Device.workshop_id == Workshop.id)
        .outerjoin(User, Workshop.owner_user_id == User.id)
        .outerjoin(Pit, Device.pit_id == Pit.id)
        .where(Device.workshop_id.isnot(None))  # Only assigned devices
    )
    
    if workshop_id:
        query = query.where(Device.workshop_id == workshop_id)
    
    # Count
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()
    
    # Execute
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Device.updated_at.desc()).offset(offset).limit(page_size)
    )
    rows = result.all()
    
    items = []
    for row in rows:
        device, ws_name, owner_name, pit_id, pit_name = row
        items.append({
            "device_id": device.device_id,
            "device_status": device.status,
            "is_online": device.is_online,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "workshop_id": device.workshop_id,
            "workshop_name": ws_name,
            "owner_username": owner_name,
            "pit_id": pit_id,
            "pit_name": pit_name,
            "license_key": device.license_key,
            "primary_sensor_code": device.primary_sensor_code,
            "air_quality_sensor_code": device.air_quality_sensor_code,
        })
    
    return build_paginated(items=items, total=total, page=page, page_size=page_size)


# ─── Admin Create Pit ─────────────────────────────────────────────────────────
@router.post("/workshops/{workshop_id}/pits", response_model=dict)
async def admin_create_pit(
    workshop_id: int,
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    """
    Admin can create a pit for any workshop (in addition to owner creating pits).
    """
    # Verify workshop exists
    workshop = await db.get(Workshop, workshop_id)
    if not workshop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workshop {workshop_id} not found"
        )
    
    from src.models.pit import Pit
    
    pit_number = request.get("pit_number")
    name = request.get("name")
    
    if not pit_number or not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="pit_number and name are required"
        )
    
    # Check if pit_number already exists in this workshop
    existing = await db.execute(
        select(Pit).where(
            Pit.workshop_id == workshop_id,
            Pit.pit_number == pit_number
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Pit number {pit_number} already exists in this workshop"
        )
    
    pit = Pit(
        workshop_id=workshop_id,
        pit_number=pit_number,
        name=name,
        description=request.get("description"),
        camera_ip=request.get("camera_ip"),
        camera_rtsp_url=request.get("camera_rtsp_url"),
        camera_model=request.get("camera_model"),
        status="active",
    )
    db.add(pit)
    await db.commit()
    await db.refresh(pit)
    
    # Update workshop pit count
    workshop.total_pits += 1
    await db.commit()
    
    logger.info(
        f"Admin created pit {pit.id} ({name}) for workshop {workshop_id}"
    )
    
    return {
        "id": pit.id,
        "workshop_id": workshop_id,
        "pit_number": pit_number,
        "name": name,
        "message": f"Pit '{name}' created successfully",
    }


# ─── Unassign Device from Workshop ────────────────────────────────────────────
@router.post("/{device_id}/unassign", response_model=SuccessResponse)
async def unassign_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    """
    Unassign a device from its workshop (set back to pending).
    Useful for re-assigning to different workshop.
    """
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found"
        )
    
    old_workshop_id = device.workshop_id
    device.workshop_id = None
    device.pit_id = None
    device.status = DeviceStatus.PENDING.value
    device.license_key = None  # Clear license key
    device.updated_at = utc_now()
    
    await db.commit()
    
    logger.info(
        f"Device {device_id} unassigned from workshop {old_workshop_id} by {current_user.username}"
    )
    
    return SuccessResponse(
        message=f"Device {device_id} has been unassigned and is now pending"
    )
