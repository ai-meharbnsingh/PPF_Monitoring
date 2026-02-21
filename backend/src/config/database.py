"""
Module: database.py
Purpose:
    SQLAlchemy async engine and session factory.
    Provides get_db() dependency for FastAPI route injection.

Dependencies:
    External:
        - sqlalchemy >= 2.0 (async ORM)
        - asyncpg >= 0.29 (async PostgreSQL driver)
    Internal:
        - src.config.settings (database URL)

Author: PPF Monitoring Team
Created: 2026-02-21
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ─── Lazy Engine (created on first access) ────────────────────────────────────
# Deferred so tests can substitute SQLite before the first DB call,
# and so missing asyncpg does not crash the import.
_engine = None
_session_factory = None


def _get_engine():
    """Return (and lazily create) the SQLAlchemy async engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        db_url = os.environ.get("TEST_DATABASE_URL", settings.DATABASE_URL)
        kwargs: dict = {"echo": settings.DATABASE_ECHO_SQL, "future": True}
        # SQLite (used in tests) does not support pool parameters
        if not db_url.startswith("sqlite"):
            kwargs.update({
                "pool_size":      settings.DATABASE_POOL_SIZE,
                "max_overflow":   settings.DATABASE_MAX_OVERFLOW,
                "pool_timeout":   30,
                "pool_recycle":   3600,
            })
        _engine = create_async_engine(db_url, **kwargs)
    return _engine


def _get_session_factory():
    """Return (and lazily create) the async session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


# Backwards-compatible module-level aliases (resolve lazily on first attribute access)
class _LazyProxy:
    """Proxy that creates the real object on first attribute/call access."""
    def __init__(self, factory):
        object.__setattr__(self, "_factory", factory)
        object.__setattr__(self, "_obj", None)

    def _resolve(self):
        if object.__getattribute__(self, "_obj") is None:
            object.__setattr__(self, "_obj", object.__getattribute__(self, "_factory")())
        return object.__getattribute__(self, "_obj")

    def __getattr__(self, name):
        return getattr(self._resolve(), name)

    def __call__(self, *args, **kwargs):
        return self._resolve()(*args, **kwargs)


engine = _LazyProxy(_get_engine)
AsyncSessionLocal = _LazyProxy(_get_session_factory)


# ─── Declarative Base ─────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# ─── FastAPI Dependency ───────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session per request.
    Automatically commits on success and rolls back on exception.

    Usage in route:
        async def my_route(db: AsyncSession = Depends(get_db)):
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error, rolling back: {e}", exc_info=True)
            raise


# ─── Context Manager (for services/scripts) ──────────────────────────────────
@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions outside of FastAPI routes.
    Use in background services (MQTT subscriber, scheduled tasks).

    Usage:
        async with get_db_context() as db:
            result = await db.execute(...)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database context manager error: {e}", exc_info=True)
            raise
