"""
Module: camera.py
Purpose:
    Camera ORM model — represents IP cameras (Hikvision, Raspberry Pi with MediaMTX).
    Separate from Pit to allow flexible camera assignment and management.

Author: PPF Monitoring Team
Created: 2026-03-03
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base
from src.models.base import TimestampMixin

if TYPE_CHECKING:
    from src.models.workshop import Workshop
    from src.models.pit import Pit


class Camera(Base, TimestampMixin):
    """
    Represents a camera device that can be assigned to a pit.
    Supports Hikvision IP cameras, Raspberry Pi with MediaMTX, ESP32-CAM, etc.
    """
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workshop_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workshops.id"), nullable=False
    )
    
    # Camera identification
    device_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Camera type and model
    camera_type: Mapped[str] = mapped_column(
        String(50), default="ip_camera", nullable=False
    )  # ip_camera, raspberry_pi, esp32_cam, hikvision, etc.
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Network configuration
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False)
    hostname: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)
    port: Mapped[int] = mapped_column(Integer, default=554, nullable=False)
    
    # Stream URLs (stored as JSON for flexibility)
    # Example: {"webrtc": "http://...", "hls": "http://...", "rtsp": "rtsp://..."}
    stream_urls: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # MediaMTX configuration (for Raspberry Pi cameras)
    mediamtx_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Camera credentials (consider encrypting in production)
    username: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    password: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Capabilities
    resolutions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    protocols: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    has_audio: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_ptz: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending, online, offline, error
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_assigned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Discovery info
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    discovered_via: Mapped[str] = mapped_column(
        String(20), default="manual", nullable=False
    )  # manual, mqtt, scan
    
    # Configuration
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # ── Relationships ──────────────────────────────────────────────────────
    workshop: Mapped["Workshop"] = relationship("Workshop", back_populates="cameras")
    
    # Assignment to pit (one-to-one)
    pit_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("pits.id"), nullable=True, unique=True
    )
    pit: Mapped[Optional["Pit"]] = relationship("Pit", back_populates="camera")

    def __repr__(self) -> str:
        return f"<Camera id={self.id} device_id='{self.device_id}' status={self.status}>"
    
    @property
    def display_name(self) -> str:
        """Get display name for UI"""
        if self.name:
            return f"{self.name} ({self.ip_address})"
        return f"Camera {self.device_id} ({self.ip_address})"
    
    @property
    def primary_stream_url(self) -> Optional[str]:
        """Get primary stream URL (WebRTC preferred)"""
        if self.stream_urls:
            if isinstance(self.stream_urls, dict):
                # Try WebRTC first, then HLS, then RTSP
                webrtc = self.stream_urls.get('webrtc', {})
                if isinstance(webrtc, dict) and webrtc.get('main'):
                    return webrtc['main']
                hls = self.stream_urls.get('hls', {})
                if isinstance(hls, dict) and hls.get('main'):
                    return hls['main']
                rtsp = self.stream_urls.get('rtsp', {})
                if isinstance(rtsp, dict) and rtsp.get('main'):
                    return rtsp['main']
                # Fallback to any available URL
                for protocol_urls in self.stream_urls.values():
                    if isinstance(protocol_urls, dict) and protocol_urls.get('main'):
                        return protocol_urls['main']
                    if isinstance(protocol_urls, str):
                        return protocol_urls
        return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'name': self.name,
            'description': self.description,
            'camera_type': self.camera_type,
            'model': self.model,
            'manufacturer': self.manufacturer,
            'ip_address': self.ip_address,
            'hostname': self.hostname,
            'port': self.port,
            'stream_urls': self.stream_urls,
            'status': self.status,
            'is_online': self.is_online,
            'is_assigned': self.is_assigned,
            'has_ptz': self.has_ptz,
            'has_audio': self.has_audio,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'discovered_at': self.discovered_at.isoformat() if self.discovered_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'workshop_id': self.workshop_id,
            'pit_id': self.pit_id,
            'pit_name': self.pit.display_name if self.pit else None,
            'primary_stream_url': self.primary_stream_url
        }
