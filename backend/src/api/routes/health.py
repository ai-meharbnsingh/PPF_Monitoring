"""
Module: routes/health.py
Purpose:
    Health check and metrics endpoints.
    GET /health — public, used by load balancers and uptime monitors.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_super_admin
from src.config.database import get_db
from src.config.settings import get_settings
from src.models.user import User
from src.services.websocket_service import manager
from src.utils.helpers import utc_now
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(tags=["Health"])

# Track startup time
_startup_time = utc_now()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    System health check — public endpoint.
    Returns 200 if all critical components are healthy.
    Returns 503 if any critical component is down.
    """
    components = {}
    overall_healthy = True

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        components["database"] = "connected"
    except Exception as e:
        logger.error(f"Health check: Database DOWN: {e}")
        components["database"] = "disconnected"
        overall_healthy = False

    # Check MQTT (simple flag — connected state tracked in mqtt_service)
    try:
        from src.services.mqtt_service import get_mqtt_client
        client = get_mqtt_client()
        components["mqtt_broker"] = "connected" if client.is_connected() else "disconnected"
        if not client.is_connected():
            overall_healthy = False
    except RuntimeError:
        components["mqtt_broker"] = "not_initialized"
        # Not fatal for health check — MQTT may not be started in test mode

    uptime_seconds = int((utc_now() - _startup_time).total_seconds())

    response = {
        "status": "healthy" if overall_healthy else "degraded",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "components": components,
        "uptime_seconds": uptime_seconds,
        "active_ws_connections": manager.total_connections,
        "timestamp": utc_now().isoformat(),
    }

    if not overall_healthy:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content=response)

    return response


@router.get("/metrics")
async def get_metrics(current_user: User = Depends(get_super_admin)):
    """System metrics — super_admin only."""
    return {
        "success": True,
        "data": {
            "active_ws_connections": manager.total_connections,
            "uptime_seconds": int((utc_now() - _startup_time).total_seconds()),
            "version": settings.APP_VERSION,
        },
    }
