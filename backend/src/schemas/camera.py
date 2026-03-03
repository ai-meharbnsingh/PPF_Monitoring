"""
Camera Pydantic Schemas
"""

from typing import Optional, Dict, List, Any
from datetime import datetime
from pydantic import BaseModel, Field


class CameraCapabilities(BaseModel):
    resolutions: Optional[List[str]] = None
    protocols: Optional[List[str]] = None
    has_audio: bool = False
    has_ptz: bool = False


class StreamUrls(BaseModel):
    webrtc: Optional[Dict[str, str]] = None
    hls: Optional[Dict[str, str]] = None
    rtsp: Optional[Dict[str, str]] = None
    rtmp: Optional[Dict[str, str]] = None


class MediaMTXConfig(BaseModel):
    host: str
    ports: Dict[str, int]
    paths: List[str]


class CameraBase(BaseModel):
    """Base camera schema"""
    device_id: str = Field(..., description="Unique device identifier")
    name: str = Field(..., description="Camera display name")
    description: Optional[str] = None
    camera_type: str = Field(default="ip_camera", description="Type: ip_camera, raspberry_pi, esp32_cam")
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    ip_address: str = Field(..., description="Camera IP address")
    hostname: Optional[str] = None
    port: int = Field(default=554, description="RTSP port")
    stream_urls: Optional[StreamUrls] = None
    mediamtx_config: Optional[MediaMTXConfig] = None
    capabilities: Optional[CameraCapabilities] = None
    protocols: Optional[List[str]] = None
    resolutions: Optional[List[str]] = None
    has_audio: bool = False
    has_ptz: bool = False
    status: str = Field(default="pending", description="pending, online, offline, error")
    is_online: bool = False
    firmware_version: Optional[str] = None


class CameraCreate(CameraBase):
    """Schema for creating a camera"""
    workshop_id: int
    discovered_via: str = "manual"


class CameraDiscoveryRequest(BaseModel):
    """Schema for camera discovery/registration (from MQTT or manual)"""
    device_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    camera_type: str = "ip_camera"
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    ip_address: str
    hostname: Optional[str] = None
    port: int = 554
    stream_urls: Optional[Dict[str, Any]] = None
    mediamtx_config: Optional[Dict[str, Any]] = None
    capabilities: Optional[Dict[str, Any]] = None
    protocols: Optional[List[str]] = None
    resolutions: Optional[List[str]] = None
    has_audio: bool = False
    has_ptz: bool = False
    is_online: bool = False
    workshop_id: int
    discovered_via: Optional[str] = "manual"
    firmware_version: Optional[str] = None


class CameraUpdate(BaseModel):
    """Schema for updating camera details"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    is_online: Optional[bool] = None
    stream_urls: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None


class CameraAssignRequest(BaseModel):
    """Schema for assigning camera to pit"""
    pit_id: int
    custom_name: Optional[str] = None


class CameraResponse(BaseModel):
    """Schema for camera API responses"""
    id: int
    device_id: str
    name: str
    description: Optional[str]
    camera_type: str
    model: Optional[str]
    manufacturer: Optional[str]
    ip_address: str
    hostname: Optional[str]
    port: int
    stream_urls: Optional[Dict[str, Any]]
    status: str
    is_online: bool
    is_assigned: bool
    has_ptz: bool
    has_audio: bool
    last_seen: Optional[str]
    discovered_at: Optional[str]
    created_at: Optional[str]
    workshop_id: int
    pit_id: Optional[int]
    pit_name: Optional[str]
    primary_stream_url: Optional[str]

    class Config:
        from_attributes = True


class CameraListResponse(BaseModel):
    """Schema for camera list response"""
    cameras: List[CameraResponse]
    total: int
    available: int  # Unassigned cameras
    assigned: int


class CameraNotification(BaseModel):
    """Schema for camera notification (WebSocket/MQTT)"""
    type: str  # camera_discovered, camera_online, camera_offline, camera_assigned
    camera_id: int
    device_id: str
    name: str
    ip_address: str
    workshop_id: int
    timestamp: datetime
    message: str
