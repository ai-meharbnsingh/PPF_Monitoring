"""
Camera Management API Routes
Handles camera discovery, registration, assignment, and management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload

from src.config.database import get_async_session
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
from src.services.auth import get_current_user, get_current_active_user
from src.models.user import User

router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.get("/discovered", response_model=List[CameraResponse])
async def get_discovered_cameras(
    workshop_id: int = Query(..., description="Workshop ID"),
    status: Optional[str] = Query(None, description="Filter by status: pending, online, offline"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
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
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
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
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
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
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
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
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """
    Trigger a camera discovery scan on the network.
    This will scan for cameras and add them to the discovered list.
    """
    # Verify access
    if current_user.workshop_id != workshop_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # TODO: Implement actual network scan
    # For now, return info about discovered cameras
    result = await session.execute(
        select(Camera).where(
            and_(
                Camera.workshop_id == workshop_id,
                Camera.is_assigned == False,
                Camera.status == "online"
            )
        )
    )
    available_cameras = result.scalars().all()
    
    return {
        "message": "Discovery triggered",
        "workshop_id": workshop_id,
        "available_cameras": len(available_cameras),
        "cameras": [c.to_dict() for c in available_cameras]
    }


@router.post("/{camera_id}/assign", response_model=CameraResponse)
async def assign_camera_to_pit(
    camera_id: int,
    assign_data: CameraAssignRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
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
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
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
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
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
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
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
    session: AsyncSession = Depends(get_async_session),
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
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
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
