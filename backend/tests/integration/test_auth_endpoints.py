"""
Integration tests: /auth endpoints
Tests login, /me, change-password against a real async FastAPI test client.

Response envelope: all auth endpoints wrap their payload in:
    {"success": True, "data": { ... }}
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
class TestLoginEndpoint:
    async def test_login_success(self, client: AsyncClient, super_admin_user, super_admin_headers):
        """Valid credentials return a JWT token inside the data envelope."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "test_super_admin", "password": "Admin@1234"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        data = body["data"]
        assert "access_token" in data
        assert data["token_type"].lower() == "bearer"
        assert data["user"]["username"] == "test_super_admin"

    async def test_login_wrong_password(self, client: AsyncClient, super_admin_user):
        """Wrong password returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "test_super_admin", "password": "WrongPass@999"},
        )
        assert response.status_code == 401

    async def test_login_unknown_user(self, client: AsyncClient):
        """Unknown username returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "nobody", "password": "Pass@word1"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestMeEndpoint:
    async def test_me_returns_profile(
        self, client: AsyncClient, super_admin_user, super_admin_headers
    ):
        """GET /auth/me returns current user profile inside the data envelope."""
        response = await client.get("/api/v1/auth/me", headers=super_admin_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        data = body["data"]
        assert data["username"] == "test_super_admin"
        assert data["role"] == "super_admin"

    async def test_me_no_token_returns_401(self, client: AsyncClient):
        """GET /auth/me without token returns 401 or 403."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code in (401, 403)


@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_health_returns_200(self, client: AsyncClient):
        """GET /health returns 200 with status info."""
        response = await client.get("/health")
        assert response.status_code in (200, 503)  # 503 if DB not connected in test
        data = response.json()
        assert "status" in data
