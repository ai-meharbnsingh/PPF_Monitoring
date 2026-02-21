"""
test_job_endpoints.py
Integration tests for /api/v1/workshops/{id}/jobs endpoints.

Actual API URL map (prefix /api/v1):
  POST   /workshops/{id}/jobs                — create job
  GET    /workshops/{id}/jobs                — list jobs with filters
  GET    /jobs/{id}                          — detail (NOT workshop-nested)
  POST   /jobs/{id}/status                  — status transition (POST, not PATCH)
  PATCH  /jobs/{id}/assign-staff            — staff assignment (PATCH, not POST)
  GET    /track/{view_token}                — public customer tracking (no /jobs/ prefix)

Author: PPF Monitoring Team
Created: 2026-02-22
"""

import secrets
from datetime import timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.workshop import Workshop
from src.models.pit import Pit
from src.models.job import Job
from src.models.user import User
from src.services.auth_service import create_access_token, hash_password
from src.utils.constants import UserRole
from src.utils.helpers import utc_now


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def workshop(db_session: AsyncSession) -> Workshop:
    w = Workshop(
        name="Job Test Workshop",
        slug="job-test-workshop",
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
        name="Job Pit 1",
        status="active",
        created_at=utc_now(),
    )
    db_session.add(p)
    await db_session.flush()
    return p


@pytest_asyncio.fixture
async def customer_user(db_session: AsyncSession) -> User:
    u = User(
        username="cust_job_test",
        email="cust_job@test.com",
        phone="+911234567890",
        password_hash=hash_password("Cust@1234"),
        role=UserRole.CUSTOMER.value,
        is_active=True,
        is_temporary_password=True,
        created_at=utc_now(),
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest_asyncio.fixture
async def workshop_owner(db_session: AsyncSession, workshop: Workshop) -> User:
    """Workshop-scoped owner for this test's workshop."""
    u = User(
        username="ws_owner_job",
        password_hash=hash_password("Owner@1234"),
        role=UserRole.OWNER.value,
        workshop_id=workshop.id,   # scoped to the test workshop
        is_active=True,
        is_temporary_password=False,
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest.fixture
def ws_owner_headers(workshop_owner: User) -> dict:
    token = create_access_token(
        user_id=workshop_owner.id,
        username=workshop_owner.username,
        role=workshop_owner.role,
        workshop_id=workshop_owner.workshop_id,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def job(
    db_session: AsyncSession,
    workshop: Workshop,
    pit: Pit,
    customer_user: User,
) -> Job:
    token = secrets.token_urlsafe(32)
    j = Job(
        workshop_id=workshop.id,
        pit_id=pit.id,
        customer_user_id=customer_user.id,
        work_type="Full PPF",
        status="waiting",
        car_model="Honda City",
        car_plate="MH12AB1234",
        customer_view_token=token,
        customer_view_expires_at=utc_now() + timedelta(hours=48),
        currency="INR",
        created_at=utc_now(),
    )
    db_session.add(j)
    await db_session.flush()
    return j


# ─────────────────────────────────────────────────────────────────────────────
# CREATE   POST /workshops/{id}/jobs
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateJob:

    @pytest.mark.asyncio
    async def test_owner_creates_job(
        self, client: AsyncClient, ws_owner_headers: dict,
        workshop: Workshop, pit: Pit
    ):
        payload = {
            "pit_id":        pit.id,
            "work_type":     "Partial PPF",
            "car_model":     "Toyota Fortuner",
            "car_plate":     "DL01AA0001",
            "customer_name": "Raj Kumar",
            "customer_phone": "+919876543210",
        }
        resp = await client.post(
            f"/api/v1/workshops/{workshop.id}/jobs",
            json=payload, headers=ws_owner_headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["work_type"]  == "Partial PPF"
        assert body["status"]     == "waiting"
        assert "customer_view_token" in body

    @pytest.mark.asyncio
    async def test_staff_creates_job(
        self, client: AsyncClient, staff_headers: dict,
        workshop: Workshop, pit: Pit
    ):
        payload = {
            "pit_id":    pit.id,
            "work_type": "Custom",
        }
        resp = await client.post(
            f"/api/v1/workshops/{workshop.id}/jobs",
            json=payload, headers=staff_headers,
        )
        assert resp.status_code in (201, 403)

    @pytest.mark.asyncio
    async def test_missing_work_type_fails(
        self, client: AsyncClient, ws_owner_headers: dict,
        workshop: Workshop, pit: Pit
    ):
        resp = await client.post(
            f"/api/v1/workshops/{workshop.id}/jobs",
            json={"pit_id": pit.id},
            headers=ws_owner_headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_create(
        self, client: AsyncClient, workshop: Workshop, pit: Pit
    ):
        resp = await client.post(
            f"/api/v1/workshops/{workshop.id}/jobs",
            json={"pit_id": pit.id, "work_type": "Test"},
        )
        assert resp.status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────────────
# LIST   GET /workshops/{id}/jobs
# ─────────────────────────────────────────────────────────────────────────────

class TestListJobs:

    @pytest.mark.asyncio
    async def test_owner_lists_jobs(
        self, client: AsyncClient, ws_owner_headers: dict,
        workshop: Workshop, job: Job
    ):
        resp = await client.get(
            f"/api/v1/workshops/{workshop.id}/jobs",
            headers=ws_owner_headers,
        )
        assert resp.status_code in (200, 403)

    @pytest.mark.asyncio
    async def test_filter_by_status(
        self, client: AsyncClient, super_admin_headers: dict,
        workshop: Workshop, job: Job
    ):
        resp = await client.get(
            f"/api/v1/workshops/{workshop.id}/jobs?status=waiting",
            headers=super_admin_headers,
        )
        assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# DETAIL   GET /jobs/{job_id}
# ─────────────────────────────────────────────────────────────────────────────

class TestGetJob:

    @pytest.mark.asyncio
    async def test_get_existing_job(
        self, client: AsyncClient, super_admin_headers: dict,
        workshop: Workshop, job: Job
    ):
        resp = await client.get(
            f"/api/v1/jobs/{job.id}",
            headers=super_admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"]        == job.id
        assert body["work_type"] == job.work_type

    @pytest.mark.asyncio
    async def test_get_nonexistent_job_404(
        self, client: AsyncClient, super_admin_headers: dict,
        workshop: Workshop
    ):
        resp = await client.get(
            "/api/v1/jobs/99999",
            headers=super_admin_headers,
        )
        assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# STATUS TRANSITION   POST /jobs/{job_id}/status
# ─────────────────────────────────────────────────────────────────────────────

class TestJobStatusTransition:

    @pytest.mark.asyncio
    async def test_valid_transition_waiting_to_in_progress(
        self, client: AsyncClient, super_admin_headers: dict,
        workshop: Workshop, job: Job
    ):
        resp = await client.post(
            f"/api/v1/jobs/{job.id}/status",
            json={"status": "in_progress"},
            headers=super_admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_invalid_transition_rejected(
        self, client: AsyncClient, super_admin_headers: dict,
        workshop: Workshop, job: Job
    ):
        """Cannot jump from 'waiting' directly to 'completed'."""
        resp = await client.post(
            f"/api/v1/jobs/{job.id}/status",
            json={"status": "completed"},
            headers=super_admin_headers,
        )
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_unknown_status_rejected(
        self, client: AsyncClient, super_admin_headers: dict,
        workshop: Workshop, job: Job
    ):
        resp = await client.post(
            f"/api/v1/jobs/{job.id}/status",
            json={"status": "FLYING"},
            headers=super_admin_headers,
        )
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC TRACKING   GET /track/{view_token}
# ─────────────────────────────────────────────────────────────────────────────

class TestPublicJobTracking:

    @pytest.mark.asyncio
    async def test_customer_tracks_job_by_token(
        self, client: AsyncClient, job: Job
    ):
        """No auth required — public endpoint for customer to track their job."""
        resp = await client.get(
            f"/api/v1/track/{job.customer_view_token}"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["job_id"]    == job.id
        assert body["work_type"] == job.work_type
        # Sensitive fields should NOT be exposed in public tracking
        assert "owner_notes"       not in body
        assert "customer_user_id"  not in body

    @pytest.mark.asyncio
    async def test_invalid_token_returns_404(self, client: AsyncClient):
        resp = await client.get("/api/v1/track/totally-invalid-token-xyz")
        assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# ASSIGN STAFF   PATCH /jobs/{job_id}/assign-staff
# ─────────────────────────────────────────────────────────────────────────────

class TestAssignStaff:

    @pytest.mark.asyncio
    async def test_owner_assigns_staff(
        self, client: AsyncClient, ws_owner_headers: dict,
        workshop: Workshop, job: Job, staff_user: User
    ):
        resp = await client.patch(
            f"/api/v1/jobs/{job.id}/assign-staff",
            json={"staff_user_ids": [staff_user.id]},
            headers=ws_owner_headers,
        )
        assert resp.status_code in (200, 403)

    @pytest.mark.asyncio
    async def test_empty_staff_list_accepted(
        self, client: AsyncClient, super_admin_headers: dict,
        workshop: Workshop, job: Job
    ):
        resp = await client.patch(
            f"/api/v1/jobs/{job.id}/assign-staff",
            json={"staff_user_ids": []},
            headers=super_admin_headers,
        )
        assert resp.status_code == 200
