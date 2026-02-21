"""
Module: stream.py
Purpose:
    Pydantic schemas for video stream endpoints.
    Stream token generation, stream info for pit cameras.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ─── Responses ────────────────────────────────────────────────────────────────
class StreamTokenResponse(BaseModel):
    """
    POST /pits/{pit_id}/stream-token
    Returns short-lived credentials for MediaMTX RTSP/WebRTC stream.
    """

    pit_id: int
    stream_token: str
    expires_at: datetime
    rtsp_url: str = Field(..., description="RTSP URL: rtsp://host:8554/{stream_path}")
    webrtc_url: str = Field(..., description="WebRTC URL: http://host:8889/{stream_path}")
    hls_url: str = Field(..., description="HLS URL: http://host:8888/{stream_path}")


class PitStreamStatus(BaseModel):
    """GET /pits/{pit_id}/stream-status — quick check without creating a token."""

    pit_id: int
    camera_is_online: bool
    camera_ip: Optional[str]
    camera_model: Optional[str]
    camera_last_seen: Optional[datetime]
    rtsp_path: Optional[str]

    model_config = {"from_attributes": True}
