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
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_staff_or_above, require_workshop_access
from src.config.database import get_db
from src.config.settings import get_settings
from src.models.pit import Pit
from src.models.user import User
from src.schemas.stream import PitStreamStatus, StreamTokenResponse
from src.utils.constants import UserRole
from src.utils.helpers import generate_stream_token
from src.utils.logger import get_logger

router = APIRouter(tags=["streams"])
logger = get_logger(__name__)


# ─── Get stream token for a pit ───────────────────────────────────────────────
@router.post("/pits/{pit_id}/stream-token", response_model=StreamTokenResponse)
async def get_stream_token(
    pit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_staff_or_above),
):
    """
    Generate a short-lived token to access the pit's camera stream.
    Returns RTSP, WebRTC, and HLS URLs for the stream.
    """
    pit = await db.get(Pit, pit_id)
    if pit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pit not found")

    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != pit.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if not pit.camera_rtsp_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No camera configured for this pit",
        )

    settings = get_settings()
    token = generate_stream_token()
    expires_at = datetime.now(tz=timezone.utc) + timedelta(
        hours=settings.STREAM_TOKEN_EXPIRE_HOURS
    )

    # Stream path: workshop_{id}_pit_{number}
    stream_path = f"workshop_{pit.workshop_id}_pit_{pit.pit_number}"
    host = settings.MEDIAMTX_HOST

    logger.info(
        f"Stream token issued: pit_id={pit_id} "
        f"user_id={current_user.id} stream_path={stream_path}"
    )

    return StreamTokenResponse(
        pit_id=pit_id,
        stream_token=token,
        expires_at=expires_at,
        rtsp_url=f"rtsp://{host}:{settings.MEDIAMTX_RTSP_PORT}/{stream_path}?token={token}",
        webrtc_url=f"http://{host}:{settings.MEDIAMTX_WEBRTC_PORT}/{stream_path}?token={token}",
        hls_url=f"http://{host}:8888/{stream_path}/index.m3u8?token={token}",
    )


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
