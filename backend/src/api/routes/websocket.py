"""
Module: routes/websocket.py
Purpose:
    WebSocket endpoint for real-time sensor updates, job status, and alerts.
    Clients authenticate with JWT token via query param.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select

from src.config.database import AsyncSessionLocal
from src.models.user import User
from src.services.auth_service import decode_access_token
from src.services.websocket_service import manager
from src.utils.constants import UserRole, WSEvent
from src.utils.helpers import utc_now
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
):
    """
    WebSocket endpoint for real-time updates.

    Connect: wss://api.ppf-monitor.com/ws?token=<JWT>

    Client actions:
        subscribe_pit      → {"action": "subscribe_pit", "pit_id": 1}
        subscribe_workshop → {"action": "subscribe_workshop", "workshop_id": 3}
        unsubscribe        → {"action": "unsubscribe", "pit_id": 1}
        ping               → {"action": "ping"}

    Server events: sensor_update, job_status, alert, device_offline, pong
    """
    # ── Authenticate ────────────────────────────────────────────────────────
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
        role = payload["role"]
        workshop_id = payload.get("workshop_id")
    except (ValueError, KeyError) as e:
        await websocket.close(code=4001, reason="Invalid or expired token")
        logger.warning(f"WebSocket auth failed: {e}")
        return

    # ── Connect ─────────────────────────────────────────────────────────────
    await manager.connect(
        websocket=websocket,
        user_id=user_id,
        role=role,
        workshop_id=workshop_id,
    )

    # Auto-subscribe owners to their workshop
    if role in (UserRole.OWNER, UserRole.SUPER_ADMIN) and workshop_id:
        manager.subscribe_workshop(websocket, workshop_id)

    try:
        while True:
            # Wait for client action message
            raw = await websocket.receive_text()

            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "event": "error",
                    "message": "Invalid JSON",
                })
                continue

            action = message.get("action", "")

            if action == "ping":
                await websocket.send_json({
                    "event": WSEvent.PONG,
                    "timestamp": utc_now().isoformat(),
                })

            elif action == "subscribe_pit":
                pit_id = message.get("pit_id")
                if pit_id:
                    manager.subscribe_pit(websocket, pit_id)
                    await websocket.send_json({
                        "event": "subscribed",
                        "pit_id": pit_id,
                    })

            elif action == "subscribe_workshop":
                ws_id = message.get("workshop_id")
                # Only owner/admin can subscribe to full workshop
                if ws_id and role in (UserRole.OWNER, UserRole.SUPER_ADMIN, UserRole.STAFF):
                    manager.subscribe_workshop(websocket, ws_id)
                    await websocket.send_json({
                        "event": "subscribed",
                        "workshop_id": ws_id,
                    })
                else:
                    await websocket.send_json({
                        "event": "error",
                        "message": "Insufficient permissions to subscribe to workshop",
                    })

            elif action == "unsubscribe":
                pit_id = message.get("pit_id")
                if pit_id:
                    manager.unsubscribe_pit(websocket, pit_id)

            else:
                await websocket.send_json({
                    "event": "error",
                    "message": f"Unknown action: {action}",
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected: user_id={user_id}")
    except Exception as e:
        manager.disconnect(websocket)
        logger.error(f"WebSocket error for user_id={user_id}: {e}", exc_info=True)
