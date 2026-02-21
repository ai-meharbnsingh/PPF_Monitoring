"""
Module: pit.py
Purpose:
    Pydantic schemas for pit (work bay) endpoints.
    PitCreate, PitUpdate, PitResponse, PitSummary.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.utils.constants import PitStatus


# ─── Requests ─────────────────────────────────────────────────────────────────
class PitCreate(BaseModel):
    """POST /workshops/{workshop_id}/pits"""

    pit_number: int = Field(..., ge=1, le=50, description="Physical bay number")
    name: Optional[str] = Field(None, max_length=50, description="Friendly display name")
    description: Optional[str] = Field(None, max_length=500)
    camera_ip: Optional[str] = Field(None, max_length=50)
    camera_rtsp_url: Optional[str] = Field(None, max_length=1000)
    camera_model: Optional[str] = Field(None, max_length=100)
    camera_username: Optional[str] = Field(None, max_length=50)


class PitUpdate(BaseModel):
    """PATCH /pits/{pit_id}"""

    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[PitStatus] = None
    camera_ip: Optional[str] = Field(None, max_length=50)
    camera_rtsp_url: Optional[str] = Field(None, max_length=1000)
    camera_model: Optional[str] = Field(None, max_length=100)
    camera_username: Optional[str] = Field(None, max_length=50)


# ─── Embedded sub-schemas ─────────────────────────────────────────────────────
class DeviceSummaryInPit(BaseModel):
    """Minimal device info shown inside a pit detail response."""

    device_id: str
    status: str
    is_online: bool
    last_seen: Optional[datetime]
    primary_sensor_code: Optional[str]
    air_quality_sensor_code: Optional[str]

    model_config = {"from_attributes": True}


class ActiveJobSummaryInPit(BaseModel):
    """Minimal active-job snapshot shown inside a pit response."""

    id: int
    work_type: str
    status: str
    car_model: Optional[str]
    car_plate: Optional[str]
    actual_start_time: Optional[datetime]
    estimated_end_time: Optional[datetime]

    model_config = {"from_attributes": True}


# ─── Responses ────────────────────────────────────────────────────────────────
class PitSummary(BaseModel):
    """Lightweight pit row for list responses."""

    id: int
    workshop_id: int
    pit_number: int
    display_name: str
    status: str
    camera_is_online: bool
    has_device: bool

    model_config = {"from_attributes": True}


class PitResponse(BaseModel):
    """Full pit detail."""

    id: int
    workshop_id: int
    pit_number: int
    name: Optional[str]
    display_name: str
    description: Optional[str]
    status: str

    # Camera fields
    camera_ip: Optional[str]
    camera_model: Optional[str]
    camera_is_online: bool
    camera_last_seen: Optional[datetime]

    # Embedded relations
    device: Optional[DeviceSummaryInPit]

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
