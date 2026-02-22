"""
test_workshop_endpoints.py
Integration tests for /api/v1/workshops endpoints.

Tests:
  GET    /workshops            — list, pagination, role access
  POST   /workshops            — create (super_admin only)
  GET    /workshops/{id}       — detail, role-gated
  PATCH  /workshops/{id}       — update by super_admin or owner
  DELETE /workshops/{id}       — deactivate (super_admin only)

Author: PPF Monitoring Team
Created: 2026-02-22
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.workshop import Workshop
from src.models.alert import AlertConfig
from src.utils.helpers import utc_now


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def workshop(db_session: AsyncSession) -> Workshop:
    """A single Workshop pre-seeded in the test DB."""
    w = Workshop(
        name="Test Auto Shop",
        slug="test-auto-shop",
        subscription_plan="basic",
        subscription_status="active",
        is_active=True,
        created_at=utc_now(),
    )
    db_session.add(w)
    await db_session.flush()
    return w


@pytest_asyncio.fixture
async def workshop_with_config(db_session: AsyncSession, workshop: Workshop) -> Workshop:
    """Workshop + AlertConfig pre-seeded."""
    cfg = AlertConfig(
        workshop_id=workshop.id,
        temp_min=15.0, temp_max=35.0,
        humidity_max=70.0,
        pm25_warning=12.0, pm25_critical=35.4,
        pm10_warning=54.0, pm10_critical=154.0,
        iaq_warning=100.0, iaq_critical=150.0,
        device_offline_threshold_seconds=60,
        camera_offline_threshold_seconds=30,
        notify_via_sms=True, notify_via_email=False,
        notify_via_webhook=False,
        created_at=utc_now(),
    )
    db_session.add(cfg)
    await db_session.flush()
    return workshop


# ─────────────────────────────────────────────────────────────────────────────
# LIST   GET /workshops
# ─────────────────────────────────────────────────────────────────────────────

class TestListWorkshops:

    @pytest.mark.asyncio
    async def test_super_admin_can_list_workshops(
        self, client: AsyncClient, super_admin_headers: dict, workshop: Workshop
    ):
        resp = await client.get("/api/v1/workshops/", headers=super_admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data or "items" in data.get("data", {})

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_list(self, client: AsyncClient):
        resp = await client.get("/api/v1/workshops/")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_pagination_parameters_accepted(
        self, client: AsyncClient, super_admin_headers: dict, workshop: Workshop
    ):
        resp = await client.get(
            "/api/v1/workshops/?page=1&page_size=5",
            headers=super_admin_headers
        )
        assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# CREATE   POST /workshops
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateWorkshop:

    @pytest.mark.asyncio
    async def test_super_admin_creates_workshop(
        self, client: AsyncClient, super_admin_headers: dict
    ):
        payload = {
            "name":  "New PPF Workshop",
            "city":  "Mumbai",
            "state": "Maharashtra",
            "phone": "+919876543210",
            "email": "new@ppfshop.com",
        }
        resp = await client.post(
            "/api/v1/workshops/", json=payload, headers=super_admin_headers
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "New PPF Workshop"
        assert "id"   in body
        assert "slug" in body

    @pytest.mark.asyncio
    async def test_owner_cannot_create_workshop(
        self, client: AsyncClient, owner_headers: dict
    ):
        payload = {"name": "Another Workshop"}
        resp    = await client.post(
            "/api/v1/workshops/", json=payload, headers=owner_headers
        )
        assert resp.status_code in (403, 422)

    @pytest.mark.asyncio
    async def test_create_workshop_missing_name_fails(
        self, client: AsyncClient, super_admin_headers: dict
    ):
        resp = await client.post(
            "/api/v1/workshops/", json={}, headers=super_admin_headers
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_duplicate_name_creates_unique_slug(
        self, client: AsyncClient, super_admin_headers: dict
    ):
        payload = {"name": "Slug Test Workshop"}
        r1 = await client.post("/api/v1/workshops/", json=payload, headers=super_admin_headers)
        r2 = await client.post("/api/v1/workshops/", json=payload, headers=super_admin_headers)
        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.json()["slug"] != r2.json()["slug"]


# ─────────────────────────────────────────────────────────────────────────────
# GET /workshops/{id}
# ─────────────────────────────────────────────────────────────────────────────

class TestGetWorkshop:

    @pytest.mark.asyncio
    async def test_super_admin_gets_any_workshop(
        self, client: AsyncClient, super_admin_headers: dict, workshop: Workshop
    ):
        resp = await client.get(
            f"/api/v1/workshops/{workshop.id}", headers=super_admin_headers
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == workshop.id

    @pytest.mark.asyncio
    async def test_nonexistent_workshop_returns_404(
        self, client: AsyncClient, super_admin_headers: dict
    ):
        resp = await client.get("/api/v1/workshops/99999", headers=super_admin_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthenticated_get_returns_401(
        self, client: AsyncClient, workshop: Workshop
    ):
        resp = await client.get(f"/api/v1/workshops/{workshop.id}")
        assert resp.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /workshops/{id}
# ─────────────────────────────────────────────────────────────────────────────

class TestUpdateWorkshop:

    @pytest.mark.asyncio
    async def test_super_admin_updates_workshop(
        self, client: AsyncClient, super_admin_headers: dict, workshop: Workshop
    ):
        resp = await client.patch(
            f"/api/v1/workshops/{workshop.id}",
            json={"city": "Delhi"},
            headers=super_admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["city"] == "Delhi"

    @pytest.mark.asyncio
    async def test_partial_update_only_changes_provided_fields(
        self, client: AsyncClient, super_admin_headers: dict, workshop: Workshop
    ):
        original_name = workshop.name
        resp = await client.patch(
            f"/api/v1/workshops/{workshop.id}",
            json={"phone": "+911234567890"},
            headers=super_admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == original_name   # unchanged


# ─────────────────────────────────────────────────────────────────────────────
# DELETE /workshops/{id}
# ─────────────────────────────────────────────────────────────────────────────

class TestDeactivateWorkshop:

    @pytest.mark.asyncio
    async def test_super_admin_deactivates_workshop(
        self, client: AsyncClient, super_admin_headers: dict, workshop: Workshop
    ):
        resp = await client.delete(
            f"/api/v1/workshops/{workshop.id}", headers=super_admin_headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is True or body.get("is_active") is False

    @pytest.mark.asyncio
    async def test_owner_cannot_delete_workshop(
        self, client: AsyncClient, owner_headers: dict, workshop: Workshop
    ):
        resp = await client.delete(
            f"/api/v1/workshops/{workshop.id}", headers=owner_headers
        )
        assert resp.status_code in (403, 404)
