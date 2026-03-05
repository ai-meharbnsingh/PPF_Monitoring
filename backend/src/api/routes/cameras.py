"""
Camera Management API Routes
Handles camera discovery, registration, assignment, and management.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload

from src.config.database import get_db
from src.models.camera import Camera
from src.models.pit import Pit
from src.models.workshop import Workshop
from src.schemas.camera import (
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    CameraListResponse,
    CameraAssignRequest,
    CameraDiscoveryRequest,
)
from src.api.dependencies import get_current_user
from src.models.user import User
from src.services.camera_discovery import discover_mediamtx_cameras
from src.services.hikvision_discovery import discover_hikvision_cameras

router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.get("/discovered", response_model=List[CameraResponse])
async def get_discovered_cameras(
    workshop_id: int = Query(..., description="Workshop ID"),
    status: Optional[str] = Query(None, description="Filter by status: pending, online, offline"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all discovered/registered cameras for a workshop.
    Returns cameras that are not yet assigned to any pit.
    """
    # Verify user has access to this workshop
    if current_user.workshop_id != workshop_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this workshop"
        )
    
    query = select(Camera).where(
        and_(
            Camera.workshop_id == workshop_id,
            Camera.is_assigned == False
        )
    )
    
    if status:
        query = query.where(Camera.status == status)
    
    query = query.order_by(Camera.discovered_at.desc())
    result = await session.execute(query)
    cameras = result.scalars().all()
    
    return [camera.to_dict() for camera in cameras]


@router.get("/workshop/{workshop_id}", response_model=List[CameraResponse])
async def get_workshop_cameras(
    workshop_id: int,
    include_assigned: bool = Query(True, description="Include assigned cameras"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all cameras for a workshop."""
    # Verify access
    if current_user.workshop_id != workshop_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this workshop"
        )
    
    query = select(Camera).where(Camera.workshop_id == workshop_id)
    
    if not include_assigned:
        query = query.where(Camera.is_assigned == False)
    
    query = query.options(selectinload(Camera.pit))
    query = query.order_by(Camera.created_at.desc())
    
    result = await session.execute(query)
    cameras = result.scalars().all()
    
    return [camera.to_dict() for camera in cameras]


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific camera by ID."""
    query = select(Camera).where(Camera.id == camera_id).options(selectinload(Camera.pit))
    result = await session.execute(query)
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    # Verify access
    if current_user.workshop_id != camera.workshop_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this camera"
        )
    
    return camera.to_dict()


@router.post("/register", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def register_camera(
    camera_data: CameraDiscoveryRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Register a new camera (manual registration or from MQTT discovery).
    """
    # Check if camera already exists
    existing = await session.execute(
        select(Camera).where(Camera.device_id == camera_data.device_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Camera with device_id '{camera_data.device_id}' already exists"
        )
    
    # Verify workshop access
    if current_user.workshop_id != camera_data.workshop_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to register cameras for this workshop"
        )
    
    # Create camera
    camera = Camera(
        workshop_id=camera_data.workshop_id,
        device_id=camera_data.device_id,
        name=camera_data.name or f"Camera {camera_data.device_id}",
        description=camera_data.description,
        camera_type=camera_data.camera_type,
        model=camera_data.model,
        manufacturer=camera_data.manufacturer,
        ip_address=camera_data.ip_address,
        hostname=camera_data.hostname,
        stream_urls=camera_data.stream_urls,
        mediamtx_config=camera_data.mediamtx_config,
        capabilities=camera_data.capabilities,
        protocols=camera_data.protocols,
        resolutions=camera_data.resolutions,
        has_audio=camera_data.has_audio,
        has_ptz=camera_data.has_ptz,
        status="online" if camera_data.is_online else "pending",
        is_online=camera_data.is_online,
        discovered_via=camera_data.discovered_via or "manual",
        firmware_version=camera_data.firmware_version,
    )
    
    session.add(camera)
    await session.commit()
    await session.refresh(camera)
    
    return camera.to_dict()


@router.post("/discover", response_model=dict)
async def trigger_camera_discovery(
    workshop_id: int = Query(..., description="Workshop ID to scan"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger a camera discovery scan on the network.
    Queries MediaMTX instances associated with workshop cameras for active streams.
    Any new streams found are auto-registered as pending cameras.
    """
    # Verify access
    if current_user.workshop_id != workshop_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    # Collect unique MediaMTX hosts from existing cameras in this workshop
    existing_result = await session.execute(
        select(Camera).where(Camera.workshop_id == workshop_id)
    )
    existing_cameras = existing_result.scalars().all()
    existing_device_ids = {c.device_id for c in existing_cameras}

    # Gather MediaMTX hosts to probe from camera configs
    mtx_hosts: dict[str, dict] = {}
    for cam in existing_cameras:
        cfg = cam.mediamtx_config
        if cfg and isinstance(cfg, dict) and cfg.get("host"):
            host = cfg["host"]
            mtx_hosts[host] = cfg.get("ports", {})
        elif cam.ip_address:
            mtx_hosts.setdefault(cam.ip_address, {})

    # Query each MediaMTX host for active paths
    new_cameras = []
    for host, ports in mtx_hosts.items():
        discovered = await discover_mediamtx_cameras(host, ports)
        for cam_data in discovered:
            if cam_data["device_id"] not in existing_device_ids:
                camera = Camera(
                    workshop_id=workshop_id,
                    device_id=cam_data["device_id"],
                    name=cam_data["name"],
                    ip_address=cam_data["ip_address"],
                    camera_type=cam_data["camera_type"],
                    stream_urls=cam_data["stream_urls"],
                    is_online=cam_data["is_online"],
                    status="online" if cam_data["is_online"] else "pending",
                    discovered_via="scan",
                )
                session.add(camera)
                new_cameras.append(camera)
                existing_device_ids.add(cam_data["device_id"])

    if new_cameras:
        await session.commit()
        for cam in new_cameras:
            await session.refresh(cam)

    # Return all unassigned cameras (existing + new)
    result = await session.execute(
        select(Camera).where(
            and_(
                Camera.workshop_id == workshop_id,
                Camera.is_assigned == False,
            )
        )
    )
    available_cameras = result.scalars().all()

    return {
        "message": f"Discovery complete. Found {len(new_cameras)} new camera(s).",
        "workshop_id": workshop_id,
        "new_cameras": len(new_cameras),
        "available_cameras": len(available_cameras),
        "cameras": [c.to_dict() for c in available_cameras],
    }


@router.post("/discover/hikvision", response_model=dict)
async def discover_hikvision_cameras_endpoint(
    workshop_id: int = Query(..., description="Workshop ID to register cameras to"),
    subnet: Optional[str] = Query(None, description="Subnet to scan (e.g., 192.168.1.0/24). Auto-detected if not provided."),
    auto_scan: bool = Query(True, description="Auto-detect and scan local subnet"),
    register: bool = Query(False, description="Auto-register discovered cameras to workshop"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Discover Hikvision cameras on the network.
    
    Uses multiple discovery methods:
    1. ONVIF WS-Discovery (standard IP camera discovery)
    2. Active network scanning (if subnet provided or auto_scan enabled)
    
    Discovered cameras can be optionally auto-registered to the workshop.
    """
    # Verify access
    if current_user.workshop_id != workshop_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to discover cameras for this workshop"
        )
    
    # Run Hikvision discovery
    discovered = await discover_hikvision_cameras(
        subnet=subnet,
        auto_detect_subnet=auto_scan
    )
    
    registered_count = 0
    existing_count = 0
    
    if register and discovered:
        # Get existing device IDs for this workshop
        result = await session.execute(
            select(Camera.device_id).where(Camera.workshop_id == workshop_id)
        )
        existing_device_ids = {row[0] for row in result.all()}
        
        # Register new cameras
        for cam_data in discovered:
            if cam_data["device_id"] not in existing_device_ids:
                camera = Camera(
                    workshop_id=workshop_id,
                    device_id=cam_data["device_id"],
                    name=cam_data["name"],
                    description=cam_data.get("description"),
                    camera_type="hikvision",
                    model=cam_data.get("model"),
                    manufacturer=cam_data.get("manufacturer", "Hikvision"),
                    ip_address=cam_data["ip_address"],
                    mac_address=cam_data.get("mac_address"),
                    port=cam_data.get("port", 554),
                    stream_urls=cam_data.get("stream_urls"),
                    has_ptz=cam_data.get("has_ptz", False),
                    has_audio=cam_data.get("has_audio", False),
                    is_online=cam_data.get("is_online", True),
                    status="online" if cam_data.get("is_online") else "pending",
                    discovered_via=cam_data.get("discovered_via", "scan"),
                    firmware_version=cam_data.get("firmware_version"),
                )
                session.add(camera)
                existing_device_ids.add(cam_data["device_id"])
                registered_count += 1
            else:
                existing_count += 1
        
        if registered_count > 0:
            await session.commit()
    
    return {
        "message": f"Hikvision discovery complete",
        "workshop_id": workshop_id,
        "cameras_found": len(discovered),
        "cameras_registered": registered_count,
        "cameras_existing": existing_count,
        "cameras": discovered,
        "subnet_used": subnet,
    }


@router.post("/{camera_id}/assign", response_model=CameraResponse)
async def assign_camera_to_pit(
    camera_id: int,
    assign_data: CameraAssignRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Assign a camera to a pit.
    A camera can only be assigned to one pit at a time.
    """
    # Get camera
    result = await session.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    # Verify access
    if current_user.workshop_id != camera.workshop_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Get pit
    result = await session.execute(
        select(Pit).where(Pit.id == assign_data.pit_id)
    )
    pit = result.scalar_one_or_none()
    
    if not pit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pit not found"
        )
    
    if pit.workshop_id != camera.workshop_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Camera and pit must belong to the same workshop"
        )
    
    # Check if pit already has a camera
    if pit.camera and pit.camera.id != camera_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Pit {pit.display_name} already has a camera assigned"
        )
    
    # Update camera
    camera.pit_id = assign_data.pit_id
    camera.is_assigned = True
    camera.name = assign_data.custom_name or camera.name
    
    await session.commit()
    await session.refresh(camera)
    
    return camera.to_dict()


@router.post("/{camera_id}/unassign", response_model=CameraResponse)
async def unassign_camera(
    camera_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unassign a camera from its pit."""
    result = await session.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    # Verify access
    if current_user.workshop_id != camera.workshop_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    camera.pit_id = None
    camera.is_assigned = False
    
    await session.commit()
    await session.refresh(camera)
    
    return camera.to_dict()


@router.patch("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: int,
    camera_data: CameraUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update camera details."""
    result = await session.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    # Verify access
    if current_user.workshop_id != camera.workshop_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Update fields
    update_data = camera_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(camera, field, value)
    
    await session.commit()
    await session.refresh(camera)
    
    return camera.to_dict()


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a camera."""
    result = await session.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    # Verify access
    if current_user.workshop_id != camera.workshop_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    await session.delete(camera)
    await session.commit()
    
    return None


@router.post("/{camera_id}/heartbeat", response_model=dict)
async def camera_heartbeat(
    camera_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    Receive heartbeat from camera (called by MQTT subscriber).
    Updates last_seen timestamp.
    """
    await session.execute(
        update(Camera)
        .where(Camera.id == camera_id)
        .values(
            last_seen=datetime.utcnow(),
            is_online=True,
            status="online"
        )
    )
    await session.commit()
    
    return {"status": "ok"}


@router.get("/pit/{pit_id}", response_model=Optional[CameraResponse])
async def get_camera_by_pit(
    pit_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the camera assigned to a specific pit."""
    # Verify pit access
    result = await session.execute(
        select(Pit).where(Pit.id == pit_id)
    )
    pit = result.scalar_one_or_none()
    
    if not pit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pit not found"
        )
    
    if current_user.workshop_id != pit.workshop_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    if not pit.camera:
        return None
    
    return pit.camera.to_dict()
