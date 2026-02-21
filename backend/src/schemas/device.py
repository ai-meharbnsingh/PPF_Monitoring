"""
Module: device.py
Purpose:
    Pydantic schemas for device registration and management endpoints.
    DeviceRegister, DeviceUpdate, DeviceResponse, DeviceCommandRequest.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from src.utils.constants import DeviceCommand, DeviceStatus, SensorTypeCode


# ─── Sensor type sub-schema ───────────────────────────────────────────────────
class SensorTypeResponse(BaseModel):
    """Sensor hardware type info embedded in device responses."""

    id: int
    code: str
    name: str
    manufacturer: Optional[str]
    protocol: Optional[str]
    description: Optional[str]

    model_config = {"from_attributes": True}


# ─── Requests ─────────────────────────────────────────────────────────────────
class DeviceRegister(BaseModel):
    """POST /workshops/{workshop_id}/devices — register a new ESP32 gateway."""

    device_id: str = Field(
        ...,
        min_length=5,
        max_length=50,
        description="Unique device ID, e.g. ESP32-A1B2C3D4E5F6",
    )
    pit_id: Optional[int] = Field(None, description="Assign to a pit immediately (optional)")
    mac_address: Optional[str] = Field(None, max_length=17)
    primary_sensor_type_code: SensorTypeCode = Field(
        default=SensorTypeCode.DHT22,
        description="Primary sensor: DHT22 or BME680",
    )
    air_quality_sensor_type_code: Optional[SensorTypeCode] = Field(
        default=SensorTypeCode.PMS5003,
        description="Air quality sensor: PMS5003 or null (if BME680 standalone)",
    )
    report_interval_seconds: int = Field(default=10, ge=5, le=3600)
    firmware_version: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("device_id")
    @classmethod
    def validate_device_id(cls, v: str) -> str:
        v = v.strip().upper()
        if not v.startswith("ESP32-"):
            raise ValueError("device_id must start with 'ESP32-'")
        return v


class DeviceUpdate(BaseModel):
    """PATCH /devices/{device_id}"""

    pit_id: Optional[int] = None
    status: Optional[DeviceStatus] = None
    primary_sensor_type_code: Optional[SensorTypeCode] = None
    air_quality_sensor_type_code: Optional[SensorTypeCode] = None
    report_interval_seconds: Optional[int] = Field(None, ge=5, le=3600)
    firmware_version: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=500)


class DeviceCommandRequest(BaseModel):
    """POST /devices/{device_id}/command — send command via MQTT."""

    command: DeviceCommand
    reason: Optional[str] = Field(None, max_length=200, description="Audit reason for command")
    payload: Optional[dict] = Field(None, description="Extra payload, e.g. {interval: 30} for SET_INTERVAL")


# ─── Responses ────────────────────────────────────────────────────────────────
class DeviceSummary(BaseModel):
    """Lightweight device row for list responses."""

    device_id: str
    pit_id: Optional[int]
    workshop_id: int
    status: str
    is_online: bool
    last_seen: Optional[datetime]
    primary_sensor_code: Optional[str]
    air_quality_sensor_code: Optional[str]

    model_config = {"from_attributes": True}


class DeviceResponse(BaseModel):
    """Full device detail."""

    id: int
    device_id: str
    pit_id: Optional[int]
    workshop_id: int
    license_key: str
    firmware_version: Optional[str]

    # Sensor configuration
    primary_sensor_type: Optional[SensorTypeResponse]
    air_quality_sensor_type: Optional[SensorTypeResponse]

    # Network
    ip_address: Optional[str]
    mac_address: Optional[str]

    # Status
    status: str
    is_online: bool
    last_seen: Optional[datetime]
    last_mqtt_message: Optional[datetime]

    report_interval_seconds: int
    notes: Optional[str]

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeviceCommandResponse(BaseModel):
    """Response after posting a device command."""

    id: int
    device_id: str
    command: str
    status: str
    created_at: datetime
    success: bool = True

    model_config = {"from_attributes": True}
