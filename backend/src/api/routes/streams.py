"""
Module: streams.py
Purpose:
    Video stream token generation and stream status endpoints.
    Integrates with MediaMTX for RTSP→WebRTC/HLS proxy.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.dependencies import get_current_user, get_staff_or_above, require_workshop_access
from src.config.database import get_db
from src.config.settings import get_settings
from src.models.camera import Camera
from src.models.job import Job
from src.models.pit import Pit
from src.models.sensor_data import SensorData
from src.models.user import User
from src.schemas.stream import PitStreamStatus, StreamTokenResponse
from src.utils.constants import UserRole
from src.utils.helpers import generate_stream_token
from src.utils.logger import get_logger

router = APIRouter(tags=["streams"])
logger = get_logger(__name__)


def _resolve_stream_path(pit: Pit) -> str:
    """Get the MediaMTX stream path for a pit.

    Priority:
      1. Assigned Camera's HLS/WebRTC stream_urls → extract path (e.g. 'cam1')
      2. Pit's camera_rtsp_url field → extract path
      3. Convention: workshop_{id}_pit_{number}
    """
    logger.debug(f"Resolving stream path for pit {pit.id}, camera: {pit.camera is not None}")
    
    # 1. From assigned Camera model (check HLS/WebRTC first as they contain MediaMTX path)
    if pit.camera and pit.camera.stream_urls:
        logger.debug(f"Camera stream_urls: {pit.camera.stream_urls}")
        urls = pit.camera.stream_urls
        # Check HLS and WebRTC first (they have MediaMTX paths like 'cam1')
        for proto in ("hls", "webrtc", "rtsp"):
            group = urls.get(proto, {})
            if isinstance(group, dict):
                main = group.get("main", "")
                if main:
                    # Extract path segment from URL
                    # Examples: 
                    #   rtsp://host:8554/cam1 → cam1
                    #   http://host:8888/cam1/index.m3u8 → cam1
                    #   https://host/cam1/whep → cam1
                    path = main
                    # Remove protocol
                    if "://" in path:
                        path = path.split("://", 1)[1]
                    # Remove host:port (everything before first /)
                    if "/" in path:
                        path = path.split("/", 1)[1]
                    else:
                        continue  # No path found
                    # Now path is like 'cam1', 'cam1/index.m3u8', or 'cam1/whep'
                    # Extract just the first segment (the stream name)
                    path = path.split("/")[0]
                    # Strip query params if any
                    path = path.split("?")[0]
                    if path:
                        return path

    # 2. From pit's legacy camera_rtsp_url (e.g. rtsp://host/cam1)
    if pit.camera_rtsp_url:
        parts = pit.camera_rtsp_url.rstrip("/").rsplit("/", 1)
        if len(parts) == 2 and parts[1]:
            return parts[1].split("?")[0]

    # 3. Convention fallback
    return f"workshop_{pit.workshop_id}_pit_{pit.pit_number}"


def _build_stream_urls(
    stream_path: str, token: str, settings, pit_id: int, expires_at, pit: Pit = None, is_demo: bool = False
) -> StreamTokenResponse:
    """Build StreamTokenResponse using public URL (Funnel) or private host."""
    
    # Demo pits return a special local video URL based on pit number
    if is_demo:
        # Map pit numbers to demo videos
        demo_videos = {
            1: "pit1.mp4",  # Pit One
            2: "pit2.mp4",  # Pit Two
            3: "pit3.mp4",  # Pit Three
        }
        # Get video file for this pit, fallback to default
        video_file = demo_videos.get(pit.pit_number if pit else None, "live-bay-preview.mp4")
        return StreamTokenResponse(
            pit_id=pit_id,
            stream_token=token,
            expires_at=expires_at,
            rtsp_url="",
            webrtc_url="",
            hls_url=f"demo:/videos/{video_file}",
        )
    
    public_url = (settings.MEDIAMTX_PUBLIC_URL or "").rstrip("/")

    if public_url:
        # Tailscale Funnel: HTTPS on port 443 → Pi's HLS port.
        # WebRTC won't work through Funnel (UDP), so leave empty.
        
        # Check if camera has funnel URL already in stream_urls
        if pit and pit.camera and pit.camera.stream_urls:
            hls_urls = pit.camera.stream_urls.get('hls', {})
            funnel_hls = hls_urls.get('main', '')
            # If camera already has HTTPS funnel URL, use it directly
            if funnel_hls and funnel_hls.startswith('https://') and 'ts.net' in funnel_hls:
                logger.info(f"Using camera's funnel HLS URL: {funnel_hls}")
                return StreamTokenResponse(
                    pit_id=pit_id,
                    stream_token=token,
                    expires_at=expires_at,
                    rtsp_url="",
                    webrtc_url="",
                    hls_url=funnel_hls,
                )
        
        # Otherwise construct from public_url + stream_path
        hls_url = f"{public_url}/{stream_path}/index.m3u8"
        logger.info(f"Using constructed funnel HLS URL: {hls_url}")
        return StreamTokenResponse(
            pit_id=pit_id,
            stream_token=token,
            expires_at=expires_at,
            rtsp_url="",
            webrtc_url="",
            hls_url=hls_url,
        )

    host = settings.MEDIAMTX_HOST
    return StreamTokenResponse(
        pit_id=pit_id,
        stream_token=token,
        expires_at=expires_at,
        rtsp_url=f"rtsp://{host}:{settings.MEDIAMTX_RTSP_PORT}/{stream_path}",
        webrtc_url=f"http://{host}:{settings.MEDIAMTX_WEBRTC_PORT}/{stream_path}",
        hls_url=f"http://{host}:8888/{stream_path}/index.m3u8",
    )


# ─── Get stream token for a pit ───────────────────────────────────────────────
@router.post("/pits/{pit_id}/stream-token", response_model=StreamTokenResponse)
async def get_stream_token(
    pit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_staff_or_above),
):
    """
    Generate a short-lived token to access the pit's camera stream.
    Returns WebRTC and HLS URLs. When MEDIAMTX_PUBLIC_URL is set
    (Tailscale Funnel), only HLS is returned (WebRTC UDP can't traverse the tunnel).
    """
    pit = await db.get(Pit, pit_id)
    if pit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pit not found")

    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != pit.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Check camera availability: assigned Camera OR legacy camera_rtsp_url
    # Special case: Demo pits (camera_model contains 'Demo') show local video
    is_demo_pit = pit.camera_model and "demo" in pit.camera_model.lower()
    
    if not pit.camera and not pit.camera_rtsp_url and not is_demo_pit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No camera configured for this pit",
        )

    settings = get_settings()
    token = generate_stream_token()
    expires_at = datetime.now(tz=timezone.utc) + timedelta(
        hours=settings.STREAM_TOKEN_EXPIRE_HOURS
    )

    stream_path = _resolve_stream_path(pit)

    logger.info(
        f"Stream token issued: pit_id={pit_id} "
        f"user_id={current_user.id} stream_path={stream_path} is_demo={is_demo_pit}"
    )

    return _build_stream_urls(stream_path, token, settings, pit_id, expires_at, pit, is_demo_pit)


# ─── Stream status for a pit ──────────────────────────────────────────────────
@router.get("/pits/{pit_id}/stream-status", response_model=PitStreamStatus)
async def stream_status(
    pit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_staff_or_above),
):
    """Check whether a pit's camera is online and get stream path info."""
    pit = await db.get(Pit, pit_id)
    if pit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pit not found")

    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != pit.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    rtsp_path = None
    if pit.camera_rtsp_url:
        rtsp_path = f"workshop_{pit.workshop_id}_pit_{pit.pit_number}"

    return PitStreamStatus(
        pit_id=pit_id,
        camera_is_online=pit.camera_is_online,
        camera_ip=pit.camera_ip,
        camera_model=pit.camera_model,
        camera_last_seen=pit.camera_last_seen,
        rtsp_path=rtsp_path,
    )


# ─── Public stream token via 6-digit tracking code (no auth) ─────────────────
@router.get("/track/code/{tracking_code}/stream-token", response_model=StreamTokenResponse)
async def public_stream_token_by_code(
    tracking_code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint — no auth required.
    Customer provides their 6-digit tracking code to get a stream token
    for watching the live camera feed of their car's bay.
    
    Checks both Job tracking codes and Pit tracking codes.
    """
    if not tracking_code.isdigit() or len(tracking_code) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tracking code. Must be 6 digits.",
        )

    # First, try to find a job with this tracking code
    result = await db.execute(
        select(Job)
        .where(Job.tracking_code == tracking_code)
        .options(
            selectinload(Job.pit).selectinload(Pit.camera)
        )
    )
    job = result.scalar_one_or_none()
    
    pit = None
    
    if job is not None:
        # Job found - check if cancelled
        if job.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This job has been cancelled",
            )
        pit = job.pit
    else:
        # No job found - try pit tracking code
        pit_result = await db.execute(
            select(Pit)
            .where(Pit.tracking_code == tracking_code)
            .options(selectinload(Pit.camera))
        )
        pit = pit_result.scalar_one_or_none()
        
        if pit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracking code not found",
            )
    # Check for camera via new Camera model OR legacy camera_rtsp_url
    # Demo pits (camera_model contains 'Demo') are also valid
    is_demo_pit = pit.camera_model and "demo" in pit.camera_model.lower()
    has_camera = (pit.camera is not None) or bool(pit.camera_rtsp_url) or is_demo_pit
    if pit is None or not has_camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No camera configured for this bay",
        )

    settings = get_settings()
    token = generate_stream_token()
    expires_at = datetime.now(tz=timezone.utc) + timedelta(
        hours=settings.STREAM_TOKEN_EXPIRE_HOURS
    )

    stream_path = _resolve_stream_path(pit)
    
    logger.info(
        f"Stream path resolved: tracking_code={tracking_code} "
        f"pit_id={pit.id} stream_path={stream_path} "
        f"has_camera={pit.camera is not None} "
        f"camera_id={pit.camera.id if pit.camera else None} "
        f"public_url={settings.MEDIAMTX_PUBLIC_URL}"
    )

    return _build_stream_urls(stream_path, token, settings, pit.id, expires_at, pit, is_demo_pit)


# ─── Public pit lookup via 6-digit tracking code (no auth) ────────────────────
@router.get("/track/pit/{tracking_code}")
async def get_pit_by_tracking_code(
    tracking_code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint — no auth required.
    Customer provides their 6-digit tracking code to get pit information
    including stream token and sensor data.
    """
    if not tracking_code.isdigit() or len(tracking_code) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tracking code. Must be 6 digits.",
        )

    # Find pit by tracking code
    result = await db.execute(
        select(Pit)
        .where(Pit.tracking_code == tracking_code)
        .options(selectinload(Pit.camera))
    )
    pit = result.scalar_one_or_none()

    if pit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracking code not found",
        )

    # Check if pit has camera
    has_camera = (pit.camera is not None) or bool(pit.camera_rtsp_url)
    is_demo = pit.camera_model and "demo" in pit.camera_model.lower()
    
    if not has_camera and not is_demo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No camera configured for this pit",
        )

    # Generate stream token
    settings = get_settings()
    token = generate_stream_token()
    expires_at = datetime.now(tz=timezone.utc) + timedelta(
        hours=settings.STREAM_TOKEN_EXPIRE_HOURS
    )

    stream_path = _resolve_stream_path(pit)
    stream_urls = _build_stream_urls(stream_path, token, settings, pit.id, expires_at, pit, is_demo)

    # Get latest sensor data
    sensor_result = await db.execute(
        select(SensorData)
        .where(SensorData.pit_id == pit.id)
        .order_by(SensorData.created_at.desc())
        .limit(1)
    )
    latest_sensor = sensor_result.scalar_one_or_none()

    return {
        "pit_id": pit.id,
        "pit_name": pit.name,
        "pit_number": pit.pit_number,
        "workshop_id": pit.workshop_id,
        "tracking_code": tracking_code,
        "camera_is_online": pit.camera_is_online,
        "camera_model": pit.camera_model,
        "stream": {
            "token": stream_urls.stream_token,
            "expires_at": stream_urls.expires_at.isoformat(),
            "hls_url": stream_urls.hls_url,
            "webrtc_url": stream_urls.webrtc_url,
        },
        "latest_sensor": {
            "temperature": latest_sensor.temperature if latest_sensor else None,
            "humidity": latest_sensor.humidity if latest_sensor else None,
            "pm25": latest_sensor.pm25 if latest_sensor else None,
            "pm10": latest_sensor.pm10 if latest_sensor else None,
            "iaq": latest_sensor.iaq if latest_sensor else None,
            "timestamp": latest_sensor.created_at.isoformat() if latest_sensor else None,
        } if latest_sensor else None,
    }
