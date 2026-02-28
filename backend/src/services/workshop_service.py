"""
Module: workshop_service.py
Purpose:
    Business logic for workshop CRUD operations.
    All DB interactions go through this service; routes stay thin.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.alert import AlertConfig
from src.models.workshop import Workshop
from src.schemas.workshop import WorkshopCreate, WorkshopUpdate
from src.utils.helpers import generate_workshop_slug
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ─── Read ──────────────────────────────────────────────────────────────────────
async def get_workshop_by_id(
    db: AsyncSession, workshop_id: int
) -> Optional[Workshop]:
    result = await db.execute(select(Workshop).where(Workshop.id == workshop_id))
    return result.scalar_one_or_none()


async def get_workshop_by_slug(
    db: AsyncSession, slug: str
) -> Optional[Workshop]:
    result = await db.execute(select(Workshop).where(Workshop.slug == slug))
    return result.scalar_one_or_none()


async def list_workshops(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    active_only: bool = False,
) -> Tuple[List[Workshop], int]:
    """Returns (workshops, total_count)."""
    base_query = select(Workshop)
    if active_only:
        base_query = base_query.where(Workshop.is_active.is_(True))

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        base_query.order_by(Workshop.created_at.desc()).offset(offset).limit(page_size)
    )
    return result.scalars().all(), total


# ─── Create ────────────────────────────────────────────────────────────────────
async def create_workshop(
    db: AsyncSession, payload: WorkshopCreate
) -> Workshop:
    slug = await _unique_slug(db, payload.name)

    workshop = Workshop(
        name=payload.name,
        slug=slug,
        address=payload.address,
        city=payload.city,
        state=payload.state,
        phone=payload.phone,
        email=payload.email,
        timezone=payload.timezone,
        owner_user_id=payload.owner_user_id,
    )
    db.add(workshop)
    await db.flush()  # get ID before default AlertConfig

    # Auto-create default AlertConfig for this workshop
    alert_config = AlertConfig(workshop_id=workshop.id)
    db.add(alert_config)

    await db.commit()
    await db.refresh(workshop)

    logger.info(f"Workshop created: id={workshop.id} name='{workshop.name}' slug='{workshop.slug}' owner={payload.owner_user_id}")
    return workshop


# ─── Update ────────────────────────────────────────────────────────────────────
async def update_workshop(
    db: AsyncSession, workshop: Workshop, payload: WorkshopUpdate
) -> Workshop:
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workshop, field, value)

    await db.commit()
    await db.refresh(workshop)
    logger.info(f"Workshop updated: id={workshop.id} fields={list(update_data.keys())}")
    return workshop


# ─── Delete (soft) ────────────────────────────────────────────────────────────
async def deactivate_workshop(db: AsyncSession, workshop: Workshop) -> Workshop:
    workshop.is_active = False
    await db.commit()
    await db.refresh(workshop)
    logger.warning(f"Workshop deactivated: id={workshop.id} name='{workshop.name}'")
    return workshop


# ─── Internal helpers ─────────────────────────────────────────────────────────
async def _unique_slug(db: AsyncSession, name: str) -> str:
    """Generate a slug from workshop name, ensuring uniqueness."""
    base_slug = generate_workshop_slug(name)
    slug = base_slug
    counter = 1
    while True:
        result = await db.execute(select(Workshop).where(Workshop.slug == slug))
        if result.scalar_one_or_none() is None:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1
