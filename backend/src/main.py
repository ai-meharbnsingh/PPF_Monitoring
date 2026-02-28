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


# ─── Application Lifecycle ────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown lifecycle manager.
    - Startup:  Connect to MQTT broker
    - Shutdown: Disconnect MQTT cleanly
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

    logger.info(f"API running at: {settings.SERVER_HOST}:{settings.SERVER_PORT}{settings.API_PREFIX}")

    yield  # Application runs here

    # ── SHUTDOWN ─────────────────────────────────────────────────────────────
    logger.info("Shutting down...")
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
