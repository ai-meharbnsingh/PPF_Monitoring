"""
Module: websocket_service.py
Purpose:
    WebSocket connection manager and event broadcaster.
    Maintains a registry of connected clients and their subscriptions.
    Broadcasts sensor updates, job status changes, and alerts in real-time.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

import json
from collections import defaultdict
from typing import Optional

from fastapi import WebSocket

from src.models.alert import Alert
from src.models.sensor_data import SensorData
from src.utils.constants import WSEvent
from src.utils.helpers import utc_now
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    Manages all active WebSocket connections.

    Registry structure:
    - workshop_connections: {workshop_id: set of WebSocket}
    - pit_connections:      {pit_id: set of WebSocket}
    - connection_meta:      {WebSocket: {user_id, role, workshop_id, subscribed_pits}}
    """

    def __init__(self):
        # workshop_id → set of connected WebSockets (owners see all pits)
        self._workshop_connections: dict[int, set[WebSocket]] = defaultdict(set)
        # pit_id → set of connected WebSockets (customers see specific pit)
        self._pit_connections: dict[int, set[WebSocket]] = defaultdict(set)
        # WebSocket → metadata dict
        self._connection_meta: dict[WebSocket, dict] = {}

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        role: str,
        workshop_id: Optional[int],
    ) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._connection_meta[websocket] = {
            "user_id": user_id,
            "role": role,
            "workshop_id": workshop_id,
            "subscribed_pits": set(),
        }
        logger.info(f"WebSocket connected: user_id={user_id} role={role}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected WebSocket from all registries."""
        meta = self._connection_meta.pop(websocket, {})
        workshop_id = meta.get("workshop_id")
        subscribed_pits = meta.get("subscribed_pits", set())

        if workshop_id:
            self._workshop_connections[workshop_id].discard(websocket)

        for pit_id in subscribed_pits:
            self._pit_connections[pit_id].discard(websocket)

        logger.info(f"WebSocket disconnected: user_id={meta.get('user_id')}")

    def subscribe_workshop(self, websocket: WebSocket, workshop_id: int) -> None:
        """Subscribe a connection to all updates from a workshop."""
        self._workshop_connections[workshop_id].add(websocket)
        if websocket in self._connection_meta:
            self._connection_meta[websocket]["workshop_id"] = workshop_id

    def subscribe_pit(self, websocket: WebSocket, pit_id: int) -> None:
        """Subscribe a connection to updates from a specific pit."""
        self._pit_connections[pit_id].add(websocket)
        if websocket in self._connection_meta:
            self._connection_meta[websocket]["subscribed_pits"].add(pit_id)

    def unsubscribe_pit(self, websocket: WebSocket, pit_id: int) -> None:
        """Unsubscribe a connection from a specific pit."""
        self._pit_connections[pit_id].discard(websocket)
        if websocket in self._connection_meta:
            self._connection_meta[websocket]["subscribed_pits"].discard(pit_id)

    async def _send_to_socket(self, websocket: WebSocket, data: dict) -> bool:
        """
        Send JSON data to one WebSocket, handling disconnection gracefully.

        Returns:
            bool: True if sent, False if connection is dead
        """
        try:
            await websocket.send_json(data)
            return True
        except Exception:
            self.disconnect(websocket)
            return False

    async def broadcast_to_workshop(self, workshop_id: int, data: dict) -> None:
        """Send event to all connections subscribed to a workshop."""
        sockets = list(self._workshop_connections.get(workshop_id, set()))
        for ws in sockets:
            await self._send_to_socket(ws, data)

    async def broadcast_to_pit(self, pit_id: int, data: dict) -> None:
        """Send event to all connections subscribed to a specific pit."""
        sockets = list(self._pit_connections.get(pit_id, set()))
        for ws in sockets:
            await self._send_to_socket(ws, data)

    @property
    def total_connections(self) -> int:
        return len(self._connection_meta)


# ─── Global singleton instance ────────────────────────────────────────────────
manager = ConnectionManager()


# ─── Broadcast helpers ────────────────────────────────────────────────────────

async def broadcast_sensor_update(
    workshop_id: int,
    pit_id: int,
    reading: SensorData,
) -> None:
    """
    Broadcast sensor update to all clients watching this workshop/pit.

    Args:
        workshop_id: For broadcasting to owner/staff dashboard
        pit_id: For broadcasting to customer watching this specific pit
        reading: The SensorData instance just stored
    """
    event = {
        "event": WSEvent.SENSOR_UPDATE,
        "pit_id": pit_id,
        "data": {
            "temperature": reading.temperature,
            "humidity": reading.humidity,
            "pm1": reading.pm1,
            "pm25": reading.pm25,
            "pm10": reading.pm10,
            "iaq": reading.iaq,
            "pressure": reading.pressure,
            "is_online": True,
            "recorded_at": reading.created_at.isoformat(),
        },
    }

    # Broadcast to workshop subscribers (owners/staff)
    await manager.broadcast_to_workshop(workshop_id, event)
    # Broadcast to pit subscribers (customers)
    await manager.broadcast_to_pit(pit_id, event)


async def broadcast_job_status(
    workshop_id: int,
    pit_id: int,
    job_id: int,
    previous_status: str,
    new_status: str,
    time_remaining_minutes: int,
) -> None:
    """Broadcast job status change to workshop and pit subscribers."""
    event = {
        "event": WSEvent.JOB_STATUS,
        "job_id": job_id,
        "pit_id": pit_id,
        "data": {
            "previous_status": previous_status,
            "new_status": new_status,
            "time_remaining_minutes": time_remaining_minutes,
            "updated_at": utc_now().isoformat(),
        },
    }
    await manager.broadcast_to_workshop(workshop_id, event)
    await manager.broadcast_to_pit(pit_id, event)


async def broadcast_alert(workshop_id: int, alert: Alert) -> None:
    """Broadcast a new alert to workshop subscribers."""
    event = {
        "event": WSEvent.ALERT,
        "pit_id": alert.pit_id,
        "data": {
            "alert_id": alert.id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "trigger_value": alert.trigger_value,
            "threshold_value": alert.threshold_value,
        },
    }
    await manager.broadcast_to_workshop(workshop_id, event)


async def broadcast_device_offline(workshop_id: int, pit_id: int, device_id: str) -> None:
    """Broadcast device offline event."""
    event = {
        "event": WSEvent.DEVICE_OFFLINE,
        "pit_id": pit_id,
        "data": {
            "device_id": device_id,
            "last_seen": utc_now().isoformat(),
        },
    }
    await manager.broadcast_to_workshop(workshop_id, event)
    await manager.broadcast_to_pit(pit_id, event)
