"""
Module: jobs.py
Purpose:
    Job (work-order) lifecycle API routes.
    Create, status transitions, staff assignment, customer tracking.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    get_current_user,
    get_owner_or_admin,
    get_staff_or_above,
    require_workshop_access,
)
from src.config.database import get_db
from src.models.user import User
from src.schemas.common import build_paginated
from src.schemas.job import (
    JobAssignStaff,
    JobCreate,
    JobResponse,
    JobStatusUpdate,
    JobSummary,
    JobTrackingResponse,
)
from src.services import job_service
from src.utils.constants import UserRole
from src.utils.helpers import compute_job_progress
from src.utils.logger import get_logger

router = APIRouter(tags=["jobs"])
logger = get_logger(__name__)


def _job_to_response(job) -> dict:
    """Build a JobResponse dict, decoding assigned_staff_ids from JSON string."""
    import json
    staff_ids = []
    try:
        if job.assigned_staff_ids_str:
            staff_ids = json.loads(job.assigned_staff_ids_str)
    except (ValueError, TypeError):
        staff_ids = []

    customer = job.customer
    customer_data = None
    if customer:
        customer_data = {
            "id": customer.id,
            "username": customer.username,
            "full_name": customer.full_name,
            "phone": customer.phone,
            "email": customer.email,
        }

    return {
        "id": job.id,
        "pit_id": job.pit_id,
        "workshop_id": job.workshop_id,
        "customer_user_id": job.customer_user_id,
        "car_model": job.car_model,
        "car_plate": job.car_plate,
        "car_color": job.car_color,
        "car_year": job.car_year,
        "work_type": job.work_type,
        "work_description": job.work_description,
        "estimated_duration_minutes": job.estimated_duration_minutes,
        "status": job.status,
        "scheduled_start_time": job.scheduled_start_time,
        "actual_start_time": job.actual_start_time,
        "estimated_end_time": job.estimated_end_time,
        "actual_end_time": job.actual_end_time,
        "quoted_price": float(job.quoted_price) if job.quoted_price else None,
        "currency": job.currency,
        "owner_notes": job.owner_notes,
        "staff_notes": job.staff_notes,
        "assigned_staff_ids": staff_ids,
        "customer_view_token": job.customer_view_token,
        "customer_view_expires_at": job.customer_view_expires_at,
        "tracking_code": job.tracking_code,
        "created_by_user_id": job.created_by_user_id,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "customer": customer_data,
        "status_history": [
            {
                "id": h.id,
                "previous_status": h.previous_status,
                "new_status": h.new_status,
                "changed_by_user_id": h.changed_by_user_id,
                "notes": h.notes,
                "created_at": h.created_at,
            }
            for h in (job.status_history or [])
        ],
    }


# ─── List jobs for a workshop ─────────────────────────────────────────────────
@router.get("/workshops/{workshop_id}/jobs", response_model=dict)
async def list_jobs(
    workshop_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    pit_id: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_workshop_access()),
):
    """List jobs for a workshop with optional status/pit filters."""
    jobs, total = await job_service.list_jobs_for_workshop(
        db,
        workshop_id=workshop_id,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        pit_id_filter=pit_id,
    )
    items = []
    for job in jobs:
        import json
        staff_ids = []
        try:
            if job.assigned_staff_ids_str:
                staff_ids = json.loads(job.assigned_staff_ids_str)
        except (ValueError, TypeError):
            pass
        items.append({
            "id": job.id,
            "pit_id": job.pit_id,
            "pit_name": job.pit.display_name if job.pit else None,
            "workshop_id": job.workshop_id,
            "work_type": job.work_type,
            "status": job.status,
            "car_model": job.car_model,
            "car_plate": job.car_plate,
            "scheduled_start_time": job.scheduled_start_time,
            "actual_start_time": job.actual_start_time,
            "estimated_end_time": job.estimated_end_time,
            "quoted_price": float(job.quoted_price) if job.quoted_price else None,
            "currency": job.currency,
            "created_at": job.created_at,
            "customer_name": job.customer.full_name if job.customer else None,
            "tracking_code": job.tracking_code,
        })
    return build_paginated(items=items, total=total, page=page, page_size=page_size)


# ─── Create job ───────────────────────────────────────────────────────────────
@router.post(
    "/workshops/{workshop_id}/jobs",
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    workshop_id: int,
    payload: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_staff_or_above),
):
    """Create a new job. staff, owner, or super_admin."""
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    job, customer, temp_password = await job_service.create_job(
        db,
        workshop_id=workshop_id,
        payload=payload,
        created_by_user_id=current_user.id,
    )

    response = _job_to_response(job)
    if customer and temp_password:
        response["customer_created"] = {
            "user_id": customer.id,
            "username": customer.username,
            "temporary_password": temp_password,
            "message": "Customer account created. Share credentials with the customer.",
        }
    return response


# ─── Get single job ───────────────────────────────────────────────────────────
@router.get("/jobs/{job_id}")
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_staff_or_above),
):
    """Get full job detail."""
    job = await job_service.get_job_by_id(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != job.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return _job_to_response(job)


# ─── Update job status ────────────────────────────────────────────────────────
@router.post("/jobs/{job_id}/status")
async def update_job_status(
    job_id: int,
    payload: JobStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_staff_or_above),
):
    """Advance or change a job's status."""
    job = await job_service.get_job_by_id(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != job.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        job = await job_service.update_job_status(
            db, job, payload, changed_by_user_id=current_user.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _job_to_response(job)


# ─── Assign staff ─────────────────────────────────────────────────────────────
@router.patch("/jobs/{job_id}/assign-staff")
async def assign_staff(
    job_id: int,
    payload: JobAssignStaff,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """Assign staff users to a job."""
    job = await job_service.get_job_by_id(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != job.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    job = await job_service.assign_staff(db, job, payload.staff_user_ids)
    return _job_to_response(job)


# ─── Job progress (for customer view) ────────────────────────────────────────
@router.get("/jobs/{job_id}/progress")
async def job_progress(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_staff_or_above),
):
    """Get computed progress % and minutes remaining for an active job."""
    job = await job_service.get_job_by_id(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != job.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    progress, remaining = compute_job_progress(job.actual_start_time, job.estimated_end_time)
    return {
        "job_id": job_id,
        "status": job.status,
        "progress_percent": progress,
        "remaining_minutes": remaining,
        "actual_start_time": job.actual_start_time,
        "estimated_end_time": job.estimated_end_time,
    }


# ─── Customer public tracking (no auth) ───────────────────────────────────────
@router.get("/track/{view_token}")
async def customer_track_job(
    view_token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint — no auth required.
    Customer uses the tracking link to monitor job progress.
    """
    job = await job_service.get_job_by_token(db, view_token)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracking link not found or expired",
        )

    progress, remaining = compute_job_progress(job.actual_start_time, job.estimated_end_time)
    return {
        "job_id": job.id,
        "tracking_code": job.tracking_code,
        "work_type": job.work_type,
        "status": job.status,
        "car_model": job.car_model,
        "car_plate": job.car_plate,
        "scheduled_start_time": job.scheduled_start_time,
        "actual_start_time": job.actual_start_time,
        "estimated_end_time": job.estimated_end_time,
        "actual_end_time": job.actual_end_time,
        "progress_percent": progress,
        "remaining_minutes": remaining,
        "pit_display_name": job.pit.display_name if job.pit else "Bay",
        "workshop_name": job.workshop.name if job.workshop else "",
        "pit_id": job.pit_id,
    }


# ─── Customer tracking by 6-digit code (no auth) ──────────────────────────────
@router.get("/track/code/{tracking_code}")
async def customer_track_job_by_code(
    tracking_code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint — no auth required.
    Customer enters 6-digit code to view their car status and live video.
    """
    from sqlalchemy import select
    from src.models.job import Job
    
    # Validate code format (6 digits)
    if not tracking_code.isdigit() or len(tracking_code) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tracking code format. Must be 6 digits.",
        )
    
    # Find job by tracking code
    result = await db.execute(select(Job).where(Job.tracking_code == tracking_code))
    job = result.scalar_one_or_none()
    
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracking code not found",
        )
    
    # Load related objects
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Job)
        .where(Job.id == job.id)
        .options(selectinload(Job.pit), selectinload(Job.workshop))
    )
    job = result.scalar_one()

    progress, remaining = compute_job_progress(job.actual_start_time, job.estimated_end_time)
    return {
        "job_id": job.id,
        "tracking_code": job.tracking_code,
        "work_type": job.work_type,
        "status": job.status,
        "car_model": job.car_model,
        "car_plate": job.car_plate,
        "car_color": job.car_color,
        "car_year": job.car_year,
        "scheduled_start_time": job.scheduled_start_time,
        "actual_start_time": job.actual_start_time,
        "estimated_end_time": job.estimated_end_time,
        "actual_end_time": job.actual_end_time,
        "progress_percent": progress,
        "remaining_minutes": remaining,
        "pit_display_name": job.pit.display_name if job.pit else "Bay",
        "workshop_name": job.workshop.name if job.workshop else "",
        "pit_id": job.pit_id,
    }
