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
      1. Assigned Camera's RTSP stream_urls → extract path (e.g. 'cam1')
      2. Pit's camera_rtsp_url field → extract path
      3. Convention: workshop_{id}_pit_{number}
    """
    # 1. From assigned Camera model
    if pit.camera and pit.camera.stream_urls:
        urls = pit.camera.stream_urls
        for proto in ("rtsp", "hls", "webrtc"):
            group = urls.get(proto, {})
            if isinstance(group, dict):
                main = group.get("main", "")
                if main:
                    # Extract path segment from URL like rtsp://host:8554/cam1
                    parts = main.rstrip("/").rsplit("/", 1)
                    if len(parts) == 2 and parts[1]:
                        # Strip query params and .m3u8 suffix
                        path = parts[1].split("?")[0].replace("/index.m3u8", "")
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
    stream_path: str, token: str, settings, pit_id: int, expires_at
) -> StreamTokenResponse:
    """Build StreamTokenResponse using public URL (Funnel) or private host."""
    public_url = (settings.MEDIAMTX_PUBLIC_URL or "").rstrip("/")

    if public_url:
        # Tailscale Funnel: HTTPS on port 443 → Pi's HLS port.
        # WebRTC won't work through Funnel (UDP), so leave empty.
        return StreamTokenResponse(
            pit_id=pit_id,
            stream_token=token,
            expires_at=expires_at,
            rtsp_url="",
            webrtc_url="",
            hls_url=f"{public_url}/{stream_path}/index.m3u8",
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
    if not pit.camera and not pit.camera_rtsp_url:
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
        f"user_id={current_user.id} stream_path={stream_path}"
    )

    return _build_stream_urls(stream_path, token, settings, pit_id, expires_at)


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
    """
    if not tracking_code.isdigit() or len(tracking_code) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tracking code. Must be 6 digits.",
        )

    result = await db.execute(
        select(Job)
        .where(Job.tracking_code == tracking_code)
        .options(selectinload(Job.pit))
    )
    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracking code not found",
        )

    if job.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This job has been cancelled",
        )

    pit = job.pit
    if pit is None or not pit.camera_rtsp_url:
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
        f"Public stream token issued: tracking_code={tracking_code} pit_id={pit.id}"
    )

    return _build_stream_urls(stream_path, token, settings, pit.id, expires_at)
