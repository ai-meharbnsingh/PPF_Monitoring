"""
Module: pits.py
Purpose:
    Pit (work bay) CRUD API routes.
    owner/super_admin: full CRUD.
    staff: read + status update.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    get_owner_or_admin,
    get_staff_or_above,
    require_workshop_access,
)
from src.config.database import get_db
from src.models.pit import Pit
from src.models.user import User
from src.schemas.common import SuccessResponse
from src.schemas.pit import PitCreate, PitResponse, PitSummary, PitUpdate
from src.schemas.pit_alert_config import PitAlertConfigUpdate
from src.utils.logger import get_logger

router = APIRouter(prefix="/workshops/{workshop_id}/pits", tags=["pits"])
root_router = APIRouter(prefix="/pits", tags=["pits"])
logger = get_logger(__name__)


def _pit_response(pit: Pit) -> dict:
    """Build PitResponse dict including device sub-schema."""
    device = pit.device
    device_data = None
    if device:
        device_data = {
            "device_id": device.device_id,
            "status": device.status,
            "is_online": device.is_online,
            "last_seen": device.last_seen,
            "primary_sensor_code": device.primary_sensor_code,
            "air_quality_sensor_code": device.air_quality_sensor_code,
        }
    return {
        "id": pit.id,
        "workshop_id": pit.workshop_id,
        "pit_number": pit.pit_number,
        "name": pit.name,
        "display_name": pit.display_name,
        "description": pit.description,
        "status": pit.status,
        "camera_ip": pit.camera_ip,
        "camera_rtsp_url": pit.camera_rtsp_url,
        "camera_model": pit.camera_model,
        "camera_is_online": pit.camera_is_online,
        "camera_last_seen": pit.camera_last_seen,
        "device": device_data,
        "created_at": pit.created_at,
        "updated_at": pit.updated_at,
    }


# ─── List pits for a workshop ──────────────────────────────────────────────────
@router.get("", response_model=list)
async def list_pits(
    workshop_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_workshop_access()),
):
    """List all pits in a workshop."""
    result = await db.execute(
        select(Pit)
        .where(Pit.workshop_id == workshop_id)
        .order_by(Pit.pit_number.asc())
    )
    pits = result.scalars().all()
    return [_pit_response(p) for p in pits]


# ─── Create pit ───────────────────────────────────────────────────────────────
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_pit(
    workshop_id: int,
    payload: PitCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """Create a new pit in the workshop."""
    from src.utils.constants import UserRole
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Check pit_number uniqueness within workshop
    existing = await db.execute(
        select(Pit).where(
            Pit.workshop_id == workshop_id,
            Pit.pit_number == payload.pit_number,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Pit number {payload.pit_number} already exists in this workshop",
        )

    from src.models.workshop import Workshop
    workshop = await db.get(Workshop, workshop_id)
    if workshop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workshop not found")

    pit = Pit(
        workshop_id=workshop_id,
        pit_number=payload.pit_number,
        name=payload.name,
        description=payload.description,
        camera_ip=payload.camera_ip,
        camera_rtsp_url=payload.camera_rtsp_url,
        camera_model=payload.camera_model,
        camera_username=payload.camera_username,
    )
    db.add(pit)

    # Update workshop.total_pits counter
    workshop.total_pits = (workshop.total_pits or 0) + 1

    await db.commit()
    await db.refresh(pit)
    logger.info(f"Pit created: id={pit.id} workshop_id={workshop_id} pit_number={payload.pit_number}")
    return _pit_response(pit)


# ─── Get single pit ───────────────────────────────────────────────────────────
@router.get("/{pit_id}")
async def get_pit(
    workshop_id: int,
    pit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_workshop_access()),
):
    """Get a single pit's full detail."""
    pit = await db.get(Pit, pit_id)
    if pit is None or pit.workshop_id != workshop_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pit not found")
    return _pit_response(pit)


# ─── Update pit ───────────────────────────────────────────────────────────────
@router.patch("/{pit_id}")
async def update_pit(
    workshop_id: int,
    pit_id: int,
    payload: PitUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """Update pit config. owner or super_admin."""
    from src.utils.constants import UserRole
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    pit = await db.get(Pit, pit_id)
    if pit is None or pit.workshop_id != workshop_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pit not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status":
            setattr(pit, field, value.value if hasattr(value, "value") else value)
        else:
            setattr(pit, field, value)

    await db.commit()
    await db.refresh(pit)
    logger.info(f"Pit updated: id={pit_id} fields={list(update_data.keys())}")
    return _pit_response(pit)


# ─── Delete pit ───────────────────────────────────────────────────────────────
@router.delete("/{pit_id}", response_model=SuccessResponse)
async def delete_pit(
    workshop_id: int,
    pit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """Delete a pit. owner or super_admin. Pit must have no active jobs."""
    from src.utils.constants import UserRole
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    pit = await db.get(Pit, pit_id)
    if pit is None or pit.workshop_id != workshop_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pit not found")

    from src.models.job import Job
    from src.utils.constants import JobStatus
    active_job = await db.execute(
        select(Job).where(
            Job.pit_id == pit_id,
            Job.status.in_([JobStatus.WAITING.value, JobStatus.IN_PROGRESS.value, JobStatus.QUALITY_CHECK.value]),
        )
    )
    if active_job.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete pit with an active job. Complete or cancel the job first.",
        )

    await db.delete(pit)

    # Decrement workshop.total_pits
    from src.models.workshop import Workshop
    workshop = await db.get(Workshop, workshop_id)
    if workshop and workshop.total_pits > 0:
        workshop.total_pits -= 1

    await db.commit()
    logger.info(f"Pit deleted: id={pit_id} workshop_id={workshop_id}")
    return SuccessResponse(message=f"Pit {pit.display_name} deleted")


# ─── Root level pit routing ───────────────────────────────────────────────────
@root_router.get("/{pit_id}")
async def get_pit_by_id(
    pit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_staff_or_above),
):
    """Get a single pit's full detail without knowing workshop_id."""
    pit = await db.get(Pit, pit_id)
    if pit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pit not found")
        
    from src.utils.constants import UserRole
    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != pit.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
    return _pit_response(pit)


# ─── Per-pit alert config: get (merged) ──────────────────────────────────────
@root_router.get("/{pit_id}/alert-config")
async def get_pit_alert_config(
    pit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_staff_or_above),
):
    """Get merged alert config for a pit (pit overrides + workshop defaults)."""
    from src.utils.constants import UserRole
    from src.models.alert import AlertConfig
    from src.models.pit_alert_config import PitAlertConfig

    pit = await db.get(Pit, pit_id)
    if pit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pit not found")

    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != pit.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Fetch both configs
    ws_result = await db.execute(
        select(AlertConfig).where(AlertConfig.workshop_id == pit.workshop_id)
    )
    ws_config = ws_result.scalar_one_or_none()

    pit_result = await db.execute(
        select(PitAlertConfig).where(PitAlertConfig.pit_id == pit_id)
    )
    pit_config = pit_result.scalar_one_or_none()

    # Build merged response with source tracking
    THRESHOLD_FIELDS = [
        ("temp_min", 15.0),
        ("temp_max", 35.0),
        ("humidity_max", 70.0),
        ("pm25_warning", 12.0),
        ("pm25_critical", 35.4),
        ("pm10_warning", 54.0),
        ("pm10_critical", 154.0),
        ("iaq_warning", 100.0),
        ("iaq_critical", 150.0),
        ("device_offline_threshold_seconds", 60),
    ]

    result = {"pit_id": pit_id}
    for field, default in THRESHOLD_FIELDS:
        pit_val = getattr(pit_config, field, None) if pit_config else None
        ws_val = getattr(ws_config, field, None) if ws_config else None

        if pit_val is not None:
            result[field] = pit_val
            result[f"{field}_source"] = "pit"
        elif ws_val is not None:
            result[field] = ws_val
            result[f"{field}_source"] = "workshop"
        else:
            result[field] = default
            result[f"{field}_source"] = "default"

    return result


# ─── Per-pit alert config: upsert ────────────────────────────────────────────
@root_router.put("/{pit_id}/alert-config")
async def update_pit_alert_config(
    pit_id: int,
    payload: PitAlertConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_owner_or_admin),
):
    """Update per-pit alert threshold overrides. Null fields inherit from workshop."""
    from src.utils.constants import UserRole
    from src.models.pit_alert_config import PitAlertConfig

    pit = await db.get(Pit, pit_id)
    if pit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pit not found")

    if (
        current_user.role != UserRole.SUPER_ADMIN.value
        and current_user.workshop_id != pit.workshop_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Fetch existing or create
    result = await db.execute(
        select(PitAlertConfig).where(PitAlertConfig.pit_id == pit_id)
    )
    pit_config = result.scalar_one_or_none()

    if pit_config is None:
        pit_config = PitAlertConfig(pit_id=pit_id)
        db.add(pit_config)

    # Apply all submitted fields (including explicit nulls to clear overrides)
    update_data = payload.model_dump()
    for field, value in update_data.items():
        setattr(pit_config, field, value)

    await db.commit()
    await db.refresh(pit_config)

    logger.info(f"Pit alert config updated: pit_id={pit_id} by user_id={current_user.id}")
    return {"message": "Pit alert thresholds saved", "pit_id": pit_id}

