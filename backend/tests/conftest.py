"""
conftest.py
Purpose:
    Shared pytest fixtures for the entire test suite.
    Provides: in-memory SQLite DB, async test client, auth tokens per role.

    Test isolation strategy:
      - StaticPool forces all connections to the SAME in-memory SQLite database.
      - setup_test_db (session-scoped) creates all tables ONCE per session.
      - clean_db (function-scoped, autouse) deletes all rows from all tables
        after each test, ensuring a pristine state for the next test.
      - db_session provides a plain AsyncSession for each test. Session
        operations (including commits inside handlers) are visible to the test,
        and clean_db wipes them at teardown.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

# ─── Load test env vars BEFORE any src.* imports ─────────────────────────────
# This must come first so pydantic Settings() picks up test values.
import os
from pathlib import Path

_TEST_ENV = Path(__file__).parent.parent / ".env.test"
if _TEST_ENV.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=_TEST_ENV, override=True)
else:
    # Fallback: set minimum required vars inline
    os.environ.setdefault("DATABASE_USER",       "test_user")
    os.environ.setdefault("DATABASE_PASSWORD",    "test_password_32chars_minimum_ok")
    os.environ.setdefault("DATABASE_HOST",        "localhost")
    os.environ.setdefault("DATABASE_NAME",        "test_db")
    os.environ.setdefault("JWT_SECRET_KEY",       "test_secret_key_that_is_at_least_32_characters_long")
    os.environ.setdefault("MQTT_BROKER_HOST",     "localhost")
    os.environ.setdefault("MQTT_USERNAME",        "test_mqtt_user")
    os.environ.setdefault("MQTT_PASSWORD",        "test_mqtt_password")
    os.environ.setdefault("STREAM_TOKEN_SECRET",  "test_stream_token_secret_32chars_ok")
    os.environ.setdefault("SUPER_ADMIN_PASSWORD", "SuperAdmin@Test123")

# Tell database.py to use SQLite in-memory (avoids asyncpg + live DB requirement)
os.environ["TEST_DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
# ─────────────────────────────────────────────────────────────────────────────

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.config.database import Base, get_db
from src.main import app
from src.models.user import User
from src.services.auth_service import create_access_token, hash_password
from src.utils.constants import UserRole

# ─── Test database engine ─────────────────────────────────────────────────────
# StaticPool: all engine.connect() calls return the SAME underlying connection
#             → single in-memory SQLite database shared across every fixture.
# check_same_thread=False: required when the same SQLite connection is accessed
#             from different coroutine/thread contexts.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ─── Event loop (shared for session-scoped async fixtures) ───────────────────
@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ─── Schema setup (once per session) ─────────────────────────────────────────
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create all tables once per session, drop all after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ─── Per-test data isolation ──────────────────────────────────────────────────
@pytest_asyncio.fixture(autouse=True)
async def clean_db(setup_test_db):
    """
    Delete all rows from every table after each test.

    Uses reversed sorted_tables order to respect FK constraints on delete.
    Disable FK enforcement during truncation for SQLite compatibility.
    """
    yield  # test runs first
    async with test_engine.begin() as conn:
        await conn.execute(text("PRAGMA foreign_keys = OFF"))
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
        await conn.execute(text("PRAGMA foreign_keys = ON"))


# ─── Per-test session ─────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a plain async session for each test."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ─── HTTP test client ─────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP test client with dependency override for DB session."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True,   # FastAPI redirects /foo/ → /foo; follow transparently
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ─── Pre-seeded users ─────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def super_admin_user(db_session: AsyncSession) -> User:
    user = User(
        username="test_super_admin",
        password_hash=hash_password("Admin@1234"),
        role=UserRole.SUPER_ADMIN.value,
        is_active=True,
        is_temporary_password=False,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def owner_user(db_session: AsyncSession) -> User:
    user = User(
        username="test_owner",
        password_hash=hash_password("Owner@1234"),
        role=UserRole.OWNER.value,
        workshop_id=None,
        is_active=True,
        is_temporary_password=False,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def staff_user(db_session: AsyncSession) -> User:
    user = User(
        username="test_staff",
        password_hash=hash_password("Staff@1234"),
        role=UserRole.STAFF.value,
        workshop_id=None,
        is_active=True,
        is_temporary_password=False,
    )
    db_session.add(user)
    await db_session.flush()
    return user


# ─── Auth token helpers ───────────────────────────────────────────────────────
@pytest.fixture
def super_admin_token(super_admin_user: User) -> str:
    return create_access_token(
        user_id=super_admin_user.id,
        username=super_admin_user.username,
        role=super_admin_user.role,
        workshop_id=None,
    )


@pytest.fixture
def owner_token(owner_user: User) -> str:
    return create_access_token(
        user_id=owner_user.id,
        username=owner_user.username,
        role=owner_user.role,
        workshop_id=owner_user.workshop_id,
    )


@pytest.fixture
def staff_token(staff_user: User) -> str:
    return create_access_token(
        user_id=staff_user.id,
        username=staff_user.username,
        role=staff_user.role,
        workshop_id=staff_user.workshop_id,
    )


# ─── Auth header helpers ──────────────────────────────────────────────────────
@pytest.fixture
def super_admin_headers(super_admin_token: str) -> dict:
    return {"Authorization": f"Bearer {super_admin_token}"}


@pytest.fixture
def owner_headers(owner_token: str) -> dict:
    return {"Authorization": f"Bearer {owner_token}"}


@pytest.fixture
def staff_headers(staff_token: str) -> dict:
    return {"Authorization": f"Bearer {staff_token}"}
