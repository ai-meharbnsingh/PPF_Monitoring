"""
Module: alert.py
Purpose:
    Pydantic schemas for alert and alert-config endpoints.
    AlertResponse, AlertAcknowledgeRequest, AlertConfigResponse, AlertConfigUpdate.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


# ─── Requests ─────────────────────────────────────────────────────────────────
class AlertAcknowledgeRequest(BaseModel):
    """POST /alerts/{alert_id}/acknowledge"""

    notes: Optional[str] = Field(None, max_length=500)


class AlertConfigUpdate(BaseModel):
    """PATCH /workshops/{workshop_id}/alert-config — update thresholds."""

    # Temperature (°C)
    temp_min: Optional[float] = Field(None, ge=-20, le=60)
    temp_max: Optional[float] = Field(None, ge=-20, le=80)

    # Humidity (%)
    humidity_max: Optional[float] = Field(None, ge=0, le=100)

    # PM2.5 (μg/m³) — WHO 2021 defaults: warning=12, critical=35.4
    pm25_warning: Optional[float] = Field(None, ge=0)
    pm25_critical: Optional[float] = Field(None, ge=0)

    # PM10 (μg/m³)
    pm10_warning: Optional[float] = Field(None, ge=0)
    pm10_critical: Optional[float] = Field(None, ge=0)

    # BME680 IAQ
    iaq_warning: Optional[float] = Field(None, ge=0, le=500)
    iaq_critical: Optional[float] = Field(None, ge=0, le=500)

    # Offline detection (seconds)
    device_offline_threshold_seconds: Optional[int] = Field(None, ge=30, le=3600)
    camera_offline_threshold_seconds: Optional[int] = Field(None, ge=15, le=3600)

    # Notification channels
    notify_via_sms: Optional[bool] = None
    notify_via_email: Optional[bool] = None
    notify_via_webhook: Optional[bool] = None
    webhook_url: Optional[str] = Field(None, max_length=1000)


# ─── Responses ────────────────────────────────────────────────────────────────
class AlertResponse(BaseModel):
    """One triggered alert."""

    id: int
    workshop_id: int
    pit_id: Optional[int]
    device_id: Optional[str]

    alert_type: str
    severity: str
    message: str
    trigger_value: Optional[float]
    threshold_value: Optional[float]

    is_acknowledged: bool
    acknowledged_by_user_id: Optional[int]
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]

    sms_sent: bool
    email_sent: bool

    created_at: datetime

    model_config = {"from_attributes": True}


class AlertConfigResponse(BaseModel):
    """Full alert threshold config for a workshop."""

    id: int
    workshop_id: int

    temp_min: float
    temp_max: float
    humidity_max: float

    pm25_warning: float
    pm25_critical: float
    pm10_warning: float
    pm10_critical: float

    iaq_warning: float
    iaq_critical: float

    device_offline_threshold_seconds: int
    camera_offline_threshold_seconds: int

    notify_via_sms: bool
    notify_via_email: bool
    notify_via_webhook: bool
    webhook_url: Optional[str]

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
