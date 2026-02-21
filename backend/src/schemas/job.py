"""
Module: job.py
Purpose:
    Pydantic schemas for job (work order) endpoints.
    JobCreate, JobStatusUpdate, JobResponse, JobStatusHistoryResponse.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from src.utils.constants import JobStatus, WorkType


# ─── Requests ─────────────────────────────────────────────────────────────────
class JobCreate(BaseModel):
    """POST /workshops/{workshop_id}/jobs"""

    pit_id: int = Field(..., description="Which pit (bay) this job runs in")
    work_type: WorkType
    car_model: Optional[str] = Field(None, max_length=100)
    car_plate: Optional[str] = Field(None, max_length=20)
    car_color: Optional[str] = Field(None, max_length=30)
    car_year: Optional[int] = Field(None, ge=1980, le=2100)
    work_description: Optional[str] = Field(None, max_length=2000)
    estimated_duration_minutes: Optional[int] = Field(None, ge=1, le=10080)
    scheduled_start_time: Optional[datetime] = None
    customer_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Creates a customer account if provided",
    )
    customer_phone: Optional[str] = Field(None, max_length=20)
    customer_email: Optional[str] = Field(None, max_length=100)
    quoted_price: Optional[float] = Field(None, ge=0)
    currency: str = Field(default="INR", max_length=3)
    owner_notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("car_plate")
    @classmethod
    def upper_plate(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().upper() if v else v


class JobStatusUpdate(BaseModel):
    """POST /jobs/{job_id}/status"""

    status: JobStatus
    notes: Optional[str] = Field(None, max_length=1000)
    staff_notes: Optional[str] = Field(None, max_length=2000)


class JobAssignStaff(BaseModel):
    """PATCH /jobs/{job_id}/assign-staff"""

    staff_user_ids: List[int] = Field(..., min_length=0, max_length=10)


# ─── Responses ────────────────────────────────────────────────────────────────
class CustomerInJob(BaseModel):
    """Minimal customer info embedded in job response."""

    id: int
    username: str
    full_name: str
    phone: Optional[str]
    email: Optional[str]

    model_config = {"from_attributes": True}


class JobStatusHistoryResponse(BaseModel):
    """One entry in the job's status audit trail."""

    id: int
    previous_status: Optional[str]
    new_status: str
    changed_by_user_id: Optional[int]
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class JobSummary(BaseModel):
    """Lightweight job row for list responses."""

    id: int
    pit_id: int
    workshop_id: int
    work_type: str
    status: str
    car_model: Optional[str]
    car_plate: Optional[str]
    scheduled_start_time: Optional[datetime]
    actual_start_time: Optional[datetime]
    estimated_end_time: Optional[datetime]
    quoted_price: Optional[float]
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}


class JobResponse(BaseModel):
    """Full job detail with status history."""

    id: int
    pit_id: int
    workshop_id: int
    customer_user_id: Optional[int]

    # Car info
    car_model: Optional[str]
    car_plate: Optional[str]
    car_color: Optional[str]
    car_year: Optional[int]

    # Work
    work_type: str
    work_description: Optional[str]
    estimated_duration_minutes: Optional[int]

    # Status
    status: str

    # Timestamps
    scheduled_start_time: Optional[datetime]
    actual_start_time: Optional[datetime]
    estimated_end_time: Optional[datetime]
    actual_end_time: Optional[datetime]

    # Pricing
    quoted_price: Optional[float]
    currency: str

    # Notes
    owner_notes: Optional[str]
    staff_notes: Optional[str]

    # Staff IDs (JSON-decoded list from DB string)
    assigned_staff_ids: Optional[List[int]]

    # Customer access token for live tracking link
    customer_view_token: Optional[str]
    customer_view_expires_at: Optional[datetime]

    # Audit
    created_by_user_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    # Embedded
    customer: Optional[CustomerInJob]
    status_history: List[JobStatusHistoryResponse] = []

    model_config = {"from_attributes": True}


class JobTrackingResponse(BaseModel):
    """
    Public response for customer live-tracking page.
    Accessed via customer_view_token — no auth required.
    Contains only public-safe fields.
    """

    job_id: int
    work_type: str
    status: str
    car_model: Optional[str]
    car_plate: Optional[str]
    scheduled_start_time: Optional[datetime]
    actual_start_time: Optional[datetime]
    estimated_end_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    pit_display_name: str
    workshop_name: str

    model_config = {"from_attributes": True}
