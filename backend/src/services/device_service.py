"""
Module: device_service.py
Purpose:
    Business logic for device registration, updates, and command dispatch.
    Handles sensor-type resolution and license key assignment.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.device import Device, SensorType
from src.models.device_command import DeviceCommand as DeviceCommandModel
from src.models.subscription import Subscription
from src.schemas.device import DeviceCommandRequest, DeviceRegister, DeviceUpdate
from src.services.mqtt_service import publish_device_command
from src.utils.constants import (
    DeviceCommand,
    DeviceCommandStatus,
    DeviceStatus,
    SensorTypeCode,
    SubscriptionPlan,
    SubscriptionStatus,
)
from src.utils.helpers import generate_license_key, utc_now
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ─── Sensor type lookup ────────────────────────────────────────────────────────
async def get_sensor_type_by_code(
    db: AsyncSession, code: str
) -> Optional[SensorType]:
    result = await db.execute(
        select(SensorType).where(SensorType.code == code, SensorType.is_active.is_(True))
    )
    return result.scalar_one_or_none()


# ─── Read ──────────────────────────────────────────────────────────────────────
async def get_device_by_device_id(
    db: AsyncSession, device_id: str
) -> Optional[Device]:
    result = await db.execute(
        select(Device).where(Device.device_id == device_id)
    )
    return result.scalar_one_or_none()


async def list_devices_for_workshop(
    db: AsyncSession,
    workshop_id: int,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Device], int]:
    from sqlalchemy import func

    base_query = select(Device).where(Device.workshop_id == workshop_id)
    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        base_query.order_by(Device.created_at.desc()).offset(offset).limit(page_size)
    )
    return result.scalars().all(), total


# ─── Create ────────────────────────────────────────────────────────────────────
async def register_device(
    db: AsyncSession, workshop_id: int, payload: DeviceRegister
) -> Device:
    """
    Register a new ESP32 gateway device.
    Auto-generates a license key and creates a basic subscription.
    """
    # Resolve sensor type IDs
    primary_sensor = await get_sensor_type_by_code(
        db, payload.primary_sensor_type_code.value
    )
    if primary_sensor is None:
        raise ValueError(
            f"Sensor type '{payload.primary_sensor_type_code}' not found in database"
        )

    air_quality_sensor = None
    if payload.air_quality_sensor_type_code:
        air_quality_sensor = await get_sensor_type_by_code(
            db, payload.air_quality_sensor_type_code.value
        )
        if air_quality_sensor is None:
            raise ValueError(
                f"Sensor type '{payload.air_quality_sensor_type_code}' not found in database"
            )

    # Ensure device_id is unique
    existing = await get_device_by_device_id(db, payload.device_id)
    if existing is not None:
        raise ValueError(f"Device '{payload.device_id}' is already registered")

    license_key = await _unique_license_key(db)

    device = Device(
        workshop_id=workshop_id,
        pit_id=payload.pit_id,
        device_id=payload.device_id,
        license_key=license_key,
        mac_address=payload.mac_address,
        primary_sensor_type_id=primary_sensor.id,
        air_quality_sensor_type_id=air_quality_sensor.id if air_quality_sensor else None,
        report_interval_seconds=payload.report_interval_seconds,
        firmware_version=payload.firmware_version,
        notes=payload.notes,
        status=DeviceStatus.ACTIVE.value,
        is_online=False,
    )
    db.add(device)
    await db.flush()

    # Auto-create subscription tied to this device
    subscription = Subscription(
        workshop_id=workshop_id,
        device_id=device.device_id,
        license_key=license_key,
        plan=SubscriptionPlan.TRIAL.value,
        status=SubscriptionStatus.ACTIVE.value,
        grace_period_days=7,
    )
    db.add(subscription)

    await db.commit()
    await db.refresh(device)

    logger.info(
        f"Device registered: device_id='{device.device_id}' "
        f"workshop_id={workshop_id} license='{license_key}'"
    )
    return device


# ─── Update ────────────────────────────────────────────────────────────────────
async def update_device(
    db: AsyncSession, device: Device, payload: DeviceUpdate
) -> Device:
    update_data = payload.model_dump(exclude_unset=True, exclude={"primary_sensor_type_code", "air_quality_sensor_type_code"})

    # Handle sensor type code changes
    if payload.primary_sensor_type_code is not None:
        sensor = await get_sensor_type_by_code(db, payload.primary_sensor_type_code.value)
        if sensor is None:
            raise ValueError(f"Sensor type '{payload.primary_sensor_type_code}' not found")
        device.primary_sensor_type_id = sensor.id

    if "air_quality_sensor_type_code" in payload.model_fields_set:
        if payload.air_quality_sensor_type_code is not None:
            sensor = await get_sensor_type_by_code(db, payload.air_quality_sensor_type_code.value)
            if sensor is None:
                raise ValueError(f"Sensor type '{payload.air_quality_sensor_type_code}' not found")
            device.air_quality_sensor_type_id = sensor.id
        else:
            device.air_quality_sensor_type_id = None

    for field, value in update_data.items():
        setattr(device, field, value)

    await db.commit()
    await db.refresh(device)
    logger.info(f"Device updated: device_id='{device.device_id}' fields={list(update_data.keys())}")
    return device


# ─── Command dispatch ─────────────────────────────────────────────────────────
async def send_device_command(
    db: AsyncSession,
    device: Device,
    request: DeviceCommandRequest,
    issued_by_user_id: Optional[int] = None,
) -> DeviceCommandModel:
    """
    Persist a DeviceCommand record and publish via MQTT.
    Returns the persisted command for response.
    """
    cmd_record = DeviceCommandModel(
        device_id=device.device_id,
        workshop_id=device.workshop_id,
        command=request.command.value,
        payload=str(request.payload) if request.payload else None,
        issued_by_user_id=issued_by_user_id,
        status=DeviceCommandStatus.PENDING.value,
        created_at=utc_now(),
    )
    db.add(cmd_record)
    await db.flush()

    try:
        await publish_device_command(
            workshop_id=device.workshop_id,
            device_id=device.device_id,
            command=request.command.value,
            reason=request.reason or "",
            payload=request.payload,
        )
        cmd_record.status = DeviceCommandStatus.SENT.value
        logger.info(
            f"Command sent: device_id='{device.device_id}' cmd={request.command.value}"
        )
    except Exception as exc:
        cmd_record.status = DeviceCommandStatus.FAILED.value
        logger.error(
            f"Command publish failed: device_id='{device.device_id}' "
            f"cmd={request.command.value} error={exc}"
        )
        raise

    await db.commit()
    await db.refresh(cmd_record)
    return cmd_record


# ─── Internal helpers ─────────────────────────────────────────────────────────
async def _unique_license_key(db: AsyncSession) -> str:
    """Generate a unique license key not already in devices or subscriptions."""
    while True:
        key = generate_license_key()
        result = await db.execute(select(Device).where(Device.license_key == key))
        if result.scalar_one_or_none() is None:
            return key
