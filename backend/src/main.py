"""
Module: main.py
Purpose:
    FastAPI application entry point.
    Initialises app, mounts all routers, starts MQTT service on startup,
    configures CORS, and handles graceful shutdown.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import (
    admin,
    admin_devices,
    alerts,
    auth,
    devices,
    firmware,
    health,
    jobs,
    pits,
    sensors,
    streams,
    subscriptions,
    users,
    websocket,
    workshops,
)
from src.config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def _render_keep_alive() -> None:
    """
    Background task: pings this service's own /health endpoint every 10 minutes
    to prevent Render free-tier from spinning the process down.

    Only runs when BACKEND_BASE_URL is set (i.e., on Render, not in local dev).
    """
    base_url = getattr(settings, "BACKEND_BASE_URL", None)
    if not base_url:
        logger.debug("BACKEND_BASE_URL not set — Render keep-alive disabled")
        return

    ping_url = f"{base_url}/health"
    logger.info(f"Render keep-alive started — pinging {ping_url} every 10 min")

    import httpx

    while True:
        try:
            await asyncio.sleep(10 * 60)  # 10 minutes
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(ping_url)
                logger.info(f"Keep-alive ping → {resp.status_code}")
        except asyncio.CancelledError:
            logger.info("Render keep-alive cancelled")
            break
        except Exception as exc:
            logger.warning(f"Keep-alive ping failed: {exc}")


async def _stale_device_sweeper() -> None:
    """
    Background task: marks devices offline when no sensor message has been
    received within SENSOR_OFFLINE_THRESHOLD_SECONDS.

    Runs every 30 seconds so the UI reflects disconnections quickly.
    """
    from datetime import timedelta
    from sqlalchemy import select
    from src.config.database import get_db_context
    from src.models.device import Device
    from src.utils.helpers import utc_now

    threshold = settings.SENSOR_OFFLINE_THRESHOLD_SECONDS
    logger.info(f"Stale-device sweeper started (threshold={threshold}s, interval=30s)")

    while True:
        try:
            await asyncio.sleep(30)
            cutoff = utc_now() - timedelta(seconds=threshold)
            async with get_db_context() as db:
                result = await db.execute(
                    select(Device).where(
                        Device.is_online == True,  # noqa: E712
                        Device.last_seen < cutoff,
                        Device.workshop_id.isnot(None),  # only assigned devices
                    )
                )
                stale = result.scalars().all()
                for dev in stale:
                    dev.is_online = False
                    logger.info(
                        f"Stale sweeper: marked '{dev.device_id}' offline "
                        f"(last_seen={dev.last_seen})"
                    )
                if stale:
                    await db.commit()
        except asyncio.CancelledError:
            logger.info("Stale-device sweeper cancelled")
            break
        except Exception as exc:
            logger.error(f"Stale-device sweeper error: {exc}", exc_info=True)


# ─── Application Lifecycle ────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown lifecycle manager.
    - Startup:  Connect to MQTT broker, start background sweeper
    - Shutdown: Cancel tasks, disconnect MQTT cleanly
    """
    # ── STARTUP ──────────────────────────────────────────────────────────────
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Start MQTT subscriber
    try:
        from src.services.mqtt_service import setup_mqtt
        loop = asyncio.get_event_loop()
        setup_mqtt(loop)
        logger.info("MQTT subscriber started")
    except Exception as e:
        logger.error(f"Failed to start MQTT subscriber: {e}", exc_info=True)
        # Non-fatal in development — allow app to start without MQTT

    # Start background stale-device sweeper
    sweeper_task = asyncio.create_task(_stale_device_sweeper())

    # Keep Render free-tier awake (no-op if BACKEND_BASE_URL is not set)
    keepalive_task = asyncio.create_task(_render_keep_alive())

    logger.info(f"API running at: {settings.SERVER_HOST}:{settings.SERVER_PORT}{settings.API_PREFIX}")

    yield  # Application runs here

    # ── SHUTDOWN ─────────────────────────────────────────────────────────────
    logger.info("Shutting down...")

    sweeper_task.cancel()
    keepalive_task.cancel()
    for task in (sweeper_task, keepalive_task):
        try:
            await task
        except asyncio.CancelledError:
            pass

    try:
        from src.services.mqtt_service import teardown_mqtt
        teardown_mqtt()
        logger.info("MQTT subscriber stopped")
    except Exception as e:
        logger.warning(f"MQTT teardown error: {e}")

    logger.info(f"{settings.APP_NAME} shut down cleanly")


# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Smart PPF Workshop Monitoring System API. "
        "Real-time sensor data, live video streaming, and job tracking."
    ),
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)


# ─── CORS ─────────────────────────────────────────────────────────────────────
# Allow all origins in development for easier testing
logger.info(f"CORS Setup - Environment: {settings.ENVIRONMENT}, is_development: {settings.is_development}")
if settings.is_development:
    logger.info("CORS: Allowing all origins [*] in development mode")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Production: Add Vercel frontend to allowed origins
    cors_origins = settings.CORS_ORIGINS.copy()
    vercel_origins = [
        "https://ppf-monitoring.vercel.app",
        "https://ppf-monitoring-*.vercel.app",  # Preview deployments
    ]
    for origin in vercel_origins:
        if origin not in cors_origins:
            cors_origins.append(origin)
    logger.info(f"CORS: Using origins: {cors_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ─── Routes ───────────────────────────────────────────────────────────────────
API = settings.API_PREFIX

# Public
app.include_router(health.router)            # GET /health, GET /metrics

# Auth
app.include_router(auth.router, prefix=API)  # POST /api/v1/auth/*

# WebSocket (no prefix — uses /ws directly)
app.include_router(websocket.router)

# Workshop & pits
app.include_router(workshops.router, prefix=API)
app.include_router(pits.router, prefix=API)
app.include_router(pits.root_router, prefix=API)

# Devices
app.include_router(devices.router, prefix=API)

# Sensor data
app.include_router(sensors.router, prefix=API)

# Jobs
app.include_router(jobs.router, prefix=API)

# Users
app.include_router(users.router, prefix=API)

# Alerts & alert config
app.include_router(alerts.router, prefix=API)

# Video streams
app.include_router(streams.router, prefix=API)

# Subscriptions
app.include_router(subscriptions.router, prefix=API)

# Firmware OTA management
app.include_router(firmware.router, prefix=API)

# Admin utilities
app.include_router(admin.router, prefix=API)
app.include_router(admin_devices.router, prefix=API)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled in production",
    }
