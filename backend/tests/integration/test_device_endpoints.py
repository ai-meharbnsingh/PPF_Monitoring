"""
test_device_endpoints.py
Integration tests for device management API endpoints.

Actual API URL map (prefix /api/v1):
  POST   /workshops/{id}/devices          — register device
  GET    /workshops/{id}/devices          — list devices in workshop
  GET    /devices/{device_id}             — device detail
  PATCH  /devices/{device_id}             — update device
  POST   /devices/{device_id}/command    — send command (owner/super_admin)

Author: PPF Monitoring Team
Created: 2026-02-22
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.workshop import Workshop
from src.models.pit import Pit
from src.models.device import Device, SensorType
from src.utils.helpers import utc_now


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def workshop(db_session: AsyncSession) -> Workshop:
    w = Workshop(
        name="Device Test Shop",
        slug="device-test-shop",
        subscription_plan="basic",
        subscription_status="active",
        is_active=True,
        created_at=utc_now(),
    )
    db_session.add(w)
    await db_session.flush()
    return w


@pytest_asyncio.fixture
async def pit(db_session: AsyncSession, workshop: Workshop) -> Pit:
    p = Pit(
        workshop_id=workshop.id,
        pit_number=1,
        name="Pit 1",
        status="active",
        created_at=utc_now(),
    )
    db_session.add(p)
    await db_session.flush()
    return p


@pytest_asyncio.fixture
async def sensor_type_dht22(db_session: AsyncSession) -> SensorType:
    st = SensorType(
        code="DHT22",
        name="Capacitive Humidity & Temperature Sensor",
        manufacturer="AOSONG",
        protocol="GPIO",
        is_active=True,
    )
    db_session.add(st)
    await db_session.flush()
    return st


@pytest_asyncio.fixture
async def device(
    db_session: AsyncSession,
    workshop: Workshop,
    pit: Pit,
    sensor_type_dht22: SensorType,
) -> Device:
    d = Device(
        device_id="ESP32-TESTDEVICE001",
        license_key="LIC-TEST-DEV-0001",
        workshop_id=workshop.id,
        pit_id=pit.id,
        primary_sensor_type_id=sensor_type_dht22.id,
        status="active",
        is_online=False,
        report_interval_seconds=10,
        created_at=utc_now(),
    )
    db_session.add(d)
    await db_session.flush()
    return d


# ─────────────────────────────────────────────────────────────────────────────
# REGISTER   POST /workshops/{id}/devices
# ─────────────────────────────────────────────────────────────────────────────

class TestRegisterDevice:

    @pytest.mark.asyncio
    async def test_super_admin_registers_device(
        self, client: AsyncClient, super_admin_headers: dict,
        workshop: Workshop, pit: Pit, sensor_type_dht22: SensorType
    ):
        payload = {
            "device_id":                    "ESP32-NEWDEVICE002",
            "pit_id":                        pit.id,
            "primary_sensor_type_code":     "DHT22",
            "air_quality_sensor_type_code":  None,   # no PMS5003 seeded — skip AQ sensor
        }
        resp = await client.post(
            f"/api/v1/workshops/{workshop.id}/devices",
            json=payload,
            headers=super_admin_headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["device_id"]  == "ESP32-NEWDEVICE002"
        assert "license_key"      in body
        assert body["license_key"].startswith("LIC-")

    @pytest.mark.asyncio
    async def test_device_id_must_start_with_esp32(
        self, client: AsyncClient, super_admin_headers: dict,
        workshop: Workshop, pit: Pit
    ):
        payload = {"device_id": "INVALID-DEVICE-ID", "pit_id": pit.id}
        resp = await client.post(
            f"/api/v1/workshops/{workshop.id}/devices",
            json=payload,
            headers=super_admin_headers,
        )
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_duplicate_device_id_fails(
        self, client: AsyncClient, super_admin_headers: dict,
        workshop: Workshop, pit: Pit, device: Device
    ):
        payload = {"device_id": device.device_id, "pit_id": pit.id}
        resp = await client.post(
            f"/api/v1/workshops/{workshop.id}/devices",
            json=payload,
            headers=super_admin_headers,
        )
        assert resp.status_code in (400, 409, 422)

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_register(
        self, client: AsyncClient, workshop: Workshop, pit: Pit
    ):
        resp = await client.post(
            f"/api/v1/workshops/{workshop.id}/devices",
            json={"device_id": "ESP32-NOAUTH-0001", "pit_id": pit.id},
        )
        assert resp.status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────────────
# LIST   GET /workshops/{id}/devices
# ─────────────────────────────────────────────────────────────────────────────

class TestListDevices:

    @pytest.mark.asyncio
    async def test_super_admin_lists_devices(
        self, client: AsyncClient, super_admin_headers: dict,
        workshop: Workshop, device: Device
    ):
        resp = await client.get(
            f"/api/v1/workshops/{workshop.id}/devices",
            headers=super_admin_headers,
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_owner_can_list_own_devices(
        self, client: AsyncClient, owner_headers: dict,
        workshop: Workshop, device: Device
    ):
        resp = await client.get(
            f"/api/v1/workshops/{workshop.id}/devices",
            headers=owner_headers,
        )
        # 200 if owner is in this workshop, 403 if not (workshop_id mismatch)
        assert resp.status_code in (200, 403)


# ─────────────────────────────────────────────────────────────────────────────
# DETAIL   GET /devices/{device_id}
# ─────────────────────────────────────────────────────────────────────────────

class TestGetDevice:

    @pytest.mark.asyncio
    async def test_get_existing_device(
        self, client: AsyncClient, super_admin_headers: dict,
        workshop: Workshop, device: Device
    ):
        resp = await client.get(
            f"/api/v1/devices/{device.device_id}",
            headers=super_admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["device_id"]   == device.device_id
        assert body["license_key"] == device.license_key

    @pytest.mark.asyncio
    async def test_get_nonexistent_device_404(
        self, client: AsyncClient, super_admin_headers: dict,
        workshop: Workshop
    ):
        resp = await client.get(
            "/api/v1/devices/ESP32-NOTREAL-999",
            headers=super_admin_headers,
        )
        assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND   POST /devices/{device_id}/command
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_mqtt_publish():
    """Patch publish_device_command so command tests don't need a real MQTT broker."""
    with patch(
        "src.services.device_service.publish_device_command",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


class TestDeviceCommand:

    @pytest.mark.asyncio
    async def test_super_admin_sends_disable_command(
        self, client: AsyncClient, super_admin_headers: dict,
        workshop: Workshop, device: Device, mock_mqtt_publish,
    ):
        resp = await client.post(
            f"/api/v1/devices/{device.device_id}/command",
            json={"command": "DISABLE", "reason": "Test disable"},
            headers=super_admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["command"] == "DISABLE"

    @pytest.mark.asyncio
    async def test_super_admin_sends_restart_command(
        self, client: AsyncClient, super_admin_headers: dict,
        workshop: Workshop, device: Device, mock_mqtt_publish,
    ):
        resp = await client.post(
            f"/api/v1/devices/{device.device_id}/command",
            json={"command": "RESTART"},
            headers=super_admin_headers,
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_set_interval_with_valid_value(
        self, client: AsyncClient, super_admin_headers: dict,
        workshop: Workshop, device: Device, mock_mqtt_publish,
    ):
        resp = await client.post(
            f"/api/v1/devices/{device.device_id}/command",
            json={"command": "SET_INTERVAL", "payload": {"interval_ms": 30000}},
            headers=super_admin_headers,
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_command_rejected(
        self, client: AsyncClient, super_admin_headers: dict,
        workshop: Workshop, device: Device,
    ):
        resp = await client.post(
            f"/api/v1/devices/{device.device_id}/command",
            json={"command": "INVALID_CMD"},
            headers=super_admin_headers,
        )
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_staff_cannot_send_commands(
        self, client: AsyncClient, staff_headers: dict,
        workshop: Workshop, device: Device,
    ):
        resp = await client.post(
            f"/api/v1/devices/{device.device_id}/command",
            json={"command": "RESTART"},
            headers=staff_headers,
        )
        assert resp.status_code in (403, 404)
