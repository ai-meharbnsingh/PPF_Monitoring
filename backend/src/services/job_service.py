"""
Module: job_service.py
Purpose:
    Business logic for job (work-order) lifecycle.
    Job creation, status transitions, customer account auto-creation,
    customer view-token generation, progress computation.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.job import Job, JobStatusHistory
from src.models.pit import Pit
from src.models.user import User
from src.schemas.job import JobCreate, JobStatusUpdate
from src.services.auth_service import hash_password
from src.utils.constants import (
    JOB_STATUS_TRANSITIONS,
    WORK_TYPE_DEFAULT_DURATION,
    JobStatus,
    UserRole,
    WorkType,
)
from src.utils.helpers import (
    compute_job_progress,
    generate_customer_username,
    generate_temporary_password,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ─── Helper: Generate unique 6-digit tracking code ─────────────────────────────
async def _generate_tracking_code(db: AsyncSession) -> str:
    """Generate a unique 6-digit tracking code."""
    import random
    from sqlalchemy import select
    
    max_attempts = 10
    for _ in range(max_attempts):
        # Generate random 6-digit number (100000-999999)
        code = str(random.randint(100000, 999999))
        
        # Check if code already exists
        result = await db.execute(select(Job).where(Job.tracking_code == code))
        if result.scalar_one_or_none() is None:
            return code
    
    # If we can't find a unique code after max attempts, use timestamp + random
    import time
    code = str(int(time.time() % 1000000)).zfill(6)
    return code


# ─── Read ──────────────────────────────────────────────────────────────────────
async def get_job_by_id(db: AsyncSession, job_id: int) -> Optional[Job]:
    result = await db.execute(
        select(Job)
        .where(Job.id == job_id)
        .options(selectinload(Job.status_history), selectinload(Job.customer))
    )
    return result.scalar_one_or_none()


async def get_job_by_token(db: AsyncSession, token: str) -> Optional[Job]:
    """Customer tracking — lookup by view token."""
    result = await db.execute(
        select(Job)
        .where(
            Job.customer_view_token == token,
            Job.customer_view_expires_at > datetime.now(tz=timezone.utc),
        )
        .options(selectinload(Job.pit), selectinload(Job.workshop))
    )
    return result.scalar_one_or_none()


async def list_jobs_for_workshop(
    db: AsyncSession,
    workshop_id: int,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    pit_id_filter: Optional[int] = None,
) -> Tuple[List[Job], int]:
    from sqlalchemy.orm import selectinload
    
    base_query = select(Job).where(Job.workshop_id == workshop_id)
    if status_filter:
        base_query = base_query.where(Job.status == status_filter)
    if pit_id_filter:
        base_query = base_query.where(Job.pit_id == pit_id_filter)

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        base_query
        .options(selectinload(Job.customer), selectinload(Job.pit))
        .order_by(Job.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return result.scalars().all(), total


async def get_active_job_for_pit(db: AsyncSession, pit_id: int) -> Optional[Job]:
    """Get any job currently in progress for a given pit."""
    result = await db.execute(
        select(Job).where(
            Job.pit_id == pit_id,
            Job.status.in_([JobStatus.WAITING, JobStatus.IN_PROGRESS, JobStatus.QUALITY_CHECK]),
        ).order_by(Job.created_at.desc())
    )
    return result.scalars().first()


# ─── Create ────────────────────────────────────────────────────────────────────
async def create_job(
    db: AsyncSession,
    workshop_id: int,
    payload: JobCreate,
    created_by_user_id: Optional[int] = None,
) -> Tuple[Job, Optional[User], Optional[str]]:
    """
    Create a job. Optionally auto-creates a customer account.
    Returns (job, customer_user, temporary_password).
    temporary_password is only set when a new account was created.
    """
    # Resolve estimated duration
    estimated_duration = payload.estimated_duration_minutes
    if estimated_duration is None:
        estimated_duration = WORK_TYPE_DEFAULT_DURATION.get(payload.work_type, 0) or None

    # Resolve estimated end time
    estimated_end_time: Optional[datetime] = None
    if estimated_duration:
        start_ref = payload.scheduled_start_time or datetime.now(tz=timezone.utc)
        estimated_end_time = start_ref + timedelta(minutes=estimated_duration)

    customer_user: Optional[User] = None
    temp_password: Optional[str] = None

    if payload.customer_name:
        customer_user, temp_password = await _get_or_create_customer(
            db=db,
            workshop_id=workshop_id,
            name=payload.customer_name,
            phone=payload.customer_phone,
            email=payload.customer_email,
        )

    # Generate customer view token for live tracking
    import secrets
    view_token = secrets.token_urlsafe(32)
    view_expires_at = datetime.now(tz=timezone.utc) + timedelta(days=30)

    # Generate 6-digit tracking code
    tracking_code = await _generate_tracking_code(db)

    job = Job(
        workshop_id=workshop_id,
        pit_id=payload.pit_id,
        customer_user_id=customer_user.id if customer_user else None,
        car_model=payload.car_model,
        car_plate=payload.car_plate,
        car_color=payload.car_color,
        car_year=payload.car_year,
        work_type=payload.work_type.value,
        work_description=payload.work_description,
        estimated_duration_minutes=estimated_duration,
        status=JobStatus.WAITING.value,
        scheduled_start_time=payload.scheduled_start_time,
        estimated_end_time=estimated_end_time,
        quoted_price=payload.quoted_price,
        currency=payload.currency,
        owner_notes=payload.owner_notes,
        created_by_user_id=created_by_user_id,
        customer_view_token=view_token,
        customer_view_expires_at=view_expires_at,
        tracking_code=tracking_code,
        assigned_staff_ids_str="[]",
    )
    db.add(job)
    await db.flush()

    # Seed initial status history
    history = JobStatusHistory(
        job_id=job.id,
        previous_status=None,
        new_status=JobStatus.WAITING.value,
        changed_by_user_id=created_by_user_id,
        notes="Job created",
        created_at=datetime.now(tz=timezone.utc),
    )
    db.add(history)

    await db.commit()
    job_id = job.id
    job = await get_job_by_id(db, job_id)  # re-fetch with eager-loaded relations
    assert job is not None
    logger.info(
        f"Job created: id={job.id} workshop_id={workshop_id} "
        f"pit_id={payload.pit_id} work_type={payload.work_type}"
    )
    return job, customer_user, temp_password


# ─── Status Transition ────────────────────────────────────────────────────────
async def update_job_status(
    db: AsyncSession,
    job: Job,
    payload: JobStatusUpdate,
    changed_by_user_id: Optional[int] = None,
) -> Job:
    """Validate and apply a status transition."""
    current = job.status
    allowed = JOB_STATUS_TRANSITIONS.get(current, set())

    if payload.status.value not in allowed:
        raise ValueError(
            f"Transition from '{current}' to '{payload.status.value}' is not allowed. "
            f"Allowed: {sorted(allowed) if allowed else 'none (terminal state)'}"
        )

    now = datetime.now(tz=timezone.utc)
    previous_status = job.status
    job.status = payload.status.value

    if payload.status == JobStatus.IN_PROGRESS and job.actual_start_time is None:
        job.actual_start_time = now

    if payload.status in (JobStatus.COMPLETED, JobStatus.CANCELLED):
        job.actual_end_time = now

    if payload.staff_notes:
        job.staff_notes = (
            f"{job.staff_notes}\n---\n{payload.staff_notes}"
            if job.staff_notes else payload.staff_notes
        )

    history = JobStatusHistory(
        job_id=job.id,
        previous_status=previous_status,
        new_status=payload.status.value,
        changed_by_user_id=changed_by_user_id,
        notes=payload.notes,
        created_at=now,
    )
    db.add(history)

    await db.commit()
    job_id = job.id
    job = await get_job_by_id(db, job_id)  # re-fetch with eager-loaded relations
    assert job is not None
    logger.info(
        f"Job status updated: id={job_id} {previous_status} → {payload.status.value}"
    )
    return job


# ─── Assign Staff ─────────────────────────────────────────────────────────────
async def assign_staff(
    db: AsyncSession, job: Job, staff_user_ids: List[int]
) -> Job:
    job_id = job.id
    job.assigned_staff_ids_str = json.dumps(staff_user_ids)
    await db.commit()
    job = await get_job_by_id(db, job_id)  # re-fetch with eager-loaded relations
    assert job is not None
    logger.info(f"Job staff assigned: id={job_id} staff_ids={staff_user_ids}")
    return job


# ─── Internal helpers ─────────────────────────────────────────────────────────
async def _get_or_create_customer(
    db: AsyncSession,
    workshop_id: int,
    name: str,
    phone: Optional[str],
    email: Optional[str],
) -> Tuple[User, Optional[str]]:
    """
    If a customer with this phone (or email) already exists in the workshop, reuse.
    Otherwise create a new customer account with a temporary password.
    Returns (user, temp_password). temp_password is None if account already existed.
    """
    # Try matching by phone first, then email
    if phone:
        result = await db.execute(
            select(User).where(
                User.workshop_id == workshop_id,
                User.phone == phone,
                User.role == UserRole.CUSTOMER.value,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing, None

    if email:
        result = await db.execute(
            select(User).where(
                User.email == email,
                User.role == UserRole.CUSTOMER.value,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing, None

    # Create new customer
    username = await _unique_customer_username(db, name)
    temp_password = generate_temporary_password()
    first, *rest = name.strip().split(None, 1)
    last = rest[0] if rest else None

    customer = User(
        workshop_id=workshop_id,
        username=username,
        email=email,
        phone=phone,
        password_hash=hash_password(temp_password),
        role=UserRole.CUSTOMER.value,
        first_name=first,
        last_name=last,
        is_active=True,
        is_temporary_password=True,
    )
    db.add(customer)
    await db.flush()
    logger.info(
        f"Customer account auto-created: username='{username}' "
        f"workshop_id={workshop_id}"
    )
    return customer, temp_password


async def _unique_customer_username(db: AsyncSession, name: str) -> str:
    base = generate_customer_username(name)
    slug = base
    counter = 1
    while True:
        result = await db.execute(select(User).where(User.username == slug))
        if result.scalar_one_or_none() is None:
            return slug
        slug = f"{base}{counter}"
        counter += 1
