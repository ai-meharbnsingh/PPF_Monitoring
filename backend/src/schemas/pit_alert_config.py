"""
Module: pit_alert_config.py
Purpose:
    Pydantic schemas for per-pit alert threshold configuration.

Author: PPF Monitoring Team
Created: 2026-02-26
"""

from typing import Optional

from pydantic import BaseModel, Field


class PitAlertConfigUpdate(BaseModel):
    """Update per-pit alert thresholds. All fields optional — null clears the override."""

    temp_min: Optional[float] = Field(None, description="Min temperature (°C)")
    temp_max: Optional[float] = Field(None, description="Max temperature (°C)")
    humidity_max: Optional[float] = Field(None, description="Max humidity (%)")
    pm25_warning: Optional[float] = Field(None, description="PM2.5 warning (μg/m³)")
    pm25_critical: Optional[float] = Field(None, description="PM2.5 critical (μg/m³)")
    pm10_warning: Optional[float] = Field(None, description="PM10 warning (μg/m³)")
    pm10_critical: Optional[float] = Field(None, description="PM10 critical (μg/m³)")
    iaq_warning: Optional[float] = Field(None, description="IAQ warning threshold")
    iaq_critical: Optional[float] = Field(None, description="IAQ critical threshold")
    device_offline_threshold_seconds: Optional[int] = Field(
        None, description="Device offline seconds"
    )


class PitAlertConfigResponse(BaseModel):
    """Merged alert config for a pit (pit overrides + workshop defaults).

    `source` indicates where each value comes from: 'pit' or 'workshop'.
    """

    pit_id: int

    temp_min: float
    temp_min_source: str = "workshop"
    temp_max: float
    temp_max_source: str = "workshop"

    humidity_max: float
    humidity_max_source: str = "workshop"

    pm25_warning: float
    pm25_warning_source: str = "workshop"
    pm25_critical: float
    pm25_critical_source: str = "workshop"

    pm10_warning: float
    pm10_warning_source: str = "workshop"
    pm10_critical: float
    pm10_critical_source: str = "workshop"

    iaq_warning: float
    iaq_warning_source: str = "workshop"
    iaq_critical: float
    iaq_critical_source: str = "workshop"

    device_offline_threshold_seconds: int
    device_offline_threshold_seconds_source: str = "workshop"

    class Config:
        from_attributes = True
