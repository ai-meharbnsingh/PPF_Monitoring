"""
Module: mqtt_service.py
Purpose:
    MQTT subscriber that listens for sensor data from ESP32 devices.
    On each message:
      1. Parses JSON payload
      2. Validates license key
      3. Stores sensor reading
      4. Evaluates alert conditions
      5. Pushes update to WebSocket clients

    Also publishes device commands (kill-switch, enable, restart).

Author: PPF Monitoring Team
Created: 2026-02-21
"""

import asyncio
import json
import os
import ssl
import uuid
from typing import TYPE_CHECKING, Optional

import paho.mqtt.client as mqtt

from src.config.database import get_db_context
from src.config.settings import get_settings
from src.services.license_service import validate_license
from src.services.sensor_service import (
    evaluate_alerts,
    parse_sensor_payload,
    store_sensor_reading,
)
from src.utils.constants import (
    MQTT_SUBSCRIBE_DEVICE_STATUS,
    MQTT_SUBSCRIBE_PROVISIONING,
    MQTT_SUBSCRIBE_SENSOR_DATA,
    DeviceCommand,
    DeviceCommandStatus,
)
from src.utils.helpers import utc_now
from src.utils.logger import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)
settings = get_settings()

# Global MQTT client instance (singleton for the service)
_mqtt_client: Optional[mqtt.Client] = None
_event_loop: Optional[asyncio.AbstractEventLoop] = None


def get_mqtt_client() -> mqtt.Client:
    """Return the global MQTT client instance."""
    if _mqtt_client is None:
        raise RuntimeError("MQTT service not initialized. Call setup_mqtt() first.")
    return _mqtt_client


def publish_device_command(
    workshop_id: int,
    device_id: str,
    command: str,
    reason: str = "",
    payload: Optional[dict] = None,
) -> bool:
    """
    Publish a command to an ESP32 device via MQTT.

    Args:
        workshop_id: Workshop ID (for topic routing)
        device_id: Target device ID
        command: Command name (DISABLE, ENABLE, RESTART, etc.)
        reason: Human-readable reason
        payload: Additional command parameters

    Returns:
        bool: True if published successfully
    """
    client = get_mqtt_client()
    topic = f"workshop/{workshop_id}/device/{device_id}/command"

    message = {
        "command": command,
        "reason": reason,
        "payload": payload or {},
        "issued_at": utc_now().isoformat(),
    }

    try:
        result = client.publish(
            topic,
            json.dumps(message),
            qos=settings.MQTT_QOS,
            retain=False,
        )
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(
                f"Published command '{command}' to device '{device_id}' "
                f"topic='{topic}' reason='{reason}'"
            )
            return True
        else:
            logger.error(
                f"Failed to publish command to device '{device_id}': "
                f"MQTT error code {result.rc}"
            )
            return False
    except Exception as e:
        logger.error(
            f"Exception publishing command to device '{device_id}': {e}",
            exc_info=True
        )
        return False


def _on_connect(client: mqtt.Client, userdata, flags, rc: int) -> None:
    """Callback: called when MQTT broker connection is established."""
    if rc == 0:
        logger.info(
            f"Connected to MQTT broker at "
            f"{settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}"
        )
        # Subscribe to sensor data and device status topics
        client.subscribe(MQTT_SUBSCRIBE_SENSOR_DATA, qos=settings.MQTT_QOS)
        client.subscribe(MQTT_SUBSCRIBE_DEVICE_STATUS, qos=settings.MQTT_QOS)
        client.subscribe(MQTT_SUBSCRIBE_PROVISIONING, qos=settings.MQTT_QOS)
        logger.info(f"Subscribed to: {MQTT_SUBSCRIBE_SENSOR_DATA}")
        logger.info(f"Subscribed to: {MQTT_SUBSCRIBE_DEVICE_STATUS}")
        logger.info(f"Subscribed to: {MQTT_SUBSCRIBE_PROVISIONING}")
    else:
        error_messages = {
            1: "Connection refused — incorrect protocol version",
            2: "Connection refused — invalid client ID",
            3: "Connection refused — server unavailable",
            4: "Connection refused — bad username or password",
            5: "Connection refused — not authorized",
        }
        logger.error(
            f"MQTT connection failed: rc={rc} — "
            f"{error_messages.get(rc, 'Unknown error')}"
        )


def _on_disconnect(client: mqtt.Client, userdata, rc: int) -> None:
    """Callback: called when disconnected from MQTT broker."""
    if rc == 0:
        logger.info("Disconnected from MQTT broker cleanly")
    else:
        logger.warning(
            f"Unexpected MQTT disconnect rc={rc}. "
            f"Will attempt reconnect in {settings.MQTT_RECONNECT_DELAY}s"
        )


def _on_message(client: mqtt.Client, userdata, message: mqtt.MQTTMessage) -> None:
    """
    Callback: called when a subscribed MQTT message arrives.
    Runs on the MQTT network thread — submits async work to the event loop.
    """
    topic = message.topic
    try:
        payload_str = message.payload.decode("utf-8")
    except UnicodeDecodeError as e:
        logger.error(f"Failed to decode MQTT message on topic '{topic}': {e}")
        return

    # Route to appropriate handler based on topic pattern
    if "/sensors" in topic:
        asyncio.run_coroutine_threadsafe(
            _handle_sensor_message(topic, payload_str),
            _event_loop,
        )
    elif "/status" in topic:
        asyncio.run_coroutine_threadsafe(
            _handle_device_status(topic, payload_str),
            _event_loop,
        )
    elif "provisioning/announce" in topic:
        asyncio.run_coroutine_threadsafe(
            _handle_provisioning_announce(topic, payload_str),
            _event_loop,
        )


async def _handle_sensor_message(topic: str, payload_str: str) -> None:
    """
    Process incoming sensor data message.

    Flow:
    1. Parse JSON
    2. Validate license
    3. Store reading
    4. Evaluate alerts
    5. Push WebSocket update
    """
    # Parse payload
    payload = parse_sensor_payload(payload_str)
    if not payload:
        logger.warning(f"Dropping invalid sensor payload on topic '{topic}'")
        return

    device_id = payload.get("device_id", "")
    license_key = payload.get("license_key", "")

    async with get_db_context() as db:
        # Validate license
        validation = await validate_license(db, device_id, license_key)

        if not validation.is_valid:
            logger.warning(
                f"Invalid license for device '{device_id}': {validation.reason}. "
                f"Sending DISABLE command."
            )
            if validation.device:
                publish_device_command(
                    workshop_id=validation.device.workshop_id,
                    device_id=device_id,
                    command=DeviceCommand.DISABLE,
                    reason=validation.reason,
                )
            return

        device = validation.device
        workshop_id = validation.workshop_id
        pit_id = validation.pit_id

        # Update device online status
        device.is_online = True
        device.last_seen = utc_now()
        device.last_mqtt_message = utc_now()

        # Store sensor reading
        reading = await store_sensor_reading(
            db=db,
            payload=payload,
            device=device,
            workshop_id=workshop_id,
            pit_id=pit_id,
        )

        if reading:
            # Evaluate alert conditions
            alerts = await evaluate_alerts(
                db=db,
                reading=reading,
                workshop_id=workshop_id,
                pit_id=pit_id,
            )

            await db.commit()

            # Push WebSocket update (import here to avoid circular deps)
            try:
                from src.services.websocket_service import broadcast_sensor_update
                await broadcast_sensor_update(
                    workshop_id=workshop_id,
                    pit_id=pit_id,
                    reading=reading,
                )
                if alerts:
                    from src.services.websocket_service import broadcast_alert
                    for alert in alerts:
                        await broadcast_alert(workshop_id=workshop_id, alert=alert)
            except Exception as ws_error:
                logger.warning(f"WebSocket broadcast failed: {ws_error}")


async def _handle_device_status(topic: str, payload_str: str) -> None:
    """Handle device status messages (online/offline confirmations)."""
    try:
        data = json.loads(payload_str)
        logger.debug(f"Device status on '{topic}': {data}")
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid device status JSON on '{topic}': {e}")


async def _handle_provisioning_announce(topic: str, payload_str: str) -> None:
    """
    Handle provisioning announce messages from new ESP32 devices.
    Creates a pending device record if one does not already exist.
    """
    try:
        data = json.loads(payload_str)
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid provisioning announce JSON on '{topic}': {e}")
        return

    device_id = data.get("device_id", "")
    mac = data.get("mac", "")
    fw_version = data.get("firmware_version", "")
    ip_address = data.get("ip", "")

    if not device_id:
        logger.warning("Provisioning announce missing device_id, ignoring")
        return

    try:
        from sqlalchemy import select
        from src.models.device import Device

        async with get_db_context() as db:
            existing = await db.execute(
                select(Device).where(Device.device_id == device_id)
            )
            device = existing.scalar_one_or_none()

            if device is None:
                # New device -- create as pending (no license key, no workshop)
                device = Device(
                    device_id=device_id,
                    mac_address=mac,
                    firmware_version=fw_version,
                    ip_address=ip_address,
                    status="pending",
                    is_online=True,
                    last_seen=utc_now(),
                )
                db.add(device)
                await db.commit()
                logger.info(f"New pending device detected: {device_id}")
            elif device.status == "pending":
                # Already pending -- update last_seen
                device.last_seen = utc_now()
                device.ip_address = ip_address
                device.firmware_version = fw_version
                device.is_online = True
                await db.commit()
                logger.debug(f"Pending device re-announced: {device_id}")
            else:
                # Already provisioned (active/disabled/etc) -- ignore
                logger.debug(
                    f"Provisioning announce from already-provisioned device "
                    f"{device_id} (status={device.status}), ignoring"
                )
    except Exception as e:
        logger.error(f"Error handling provisioning announce: {e}", exc_info=True)


def publish_provisioning_config(
    device_id: str,
    license_key: str,
    workshop_id: int,
    pit_id: int = 0,
) -> bool:
    """
    Publish provisioning config (license key, workshop assignment) to a device.

    Args:
        device_id: Target device ID
        license_key: Generated license key
        workshop_id: Workshop to assign the device to
        pit_id: Optional pit assignment (0 = unassigned)

    Returns:
        bool: True if published successfully
    """
    client = get_mqtt_client()
    topic = f"provisioning/{device_id}/config"
    message = {
        "command": "PROVISION",
        "license_key": license_key,
        "workshop_id": workshop_id,
        "pit_id": pit_id,
    }
    try:
        result = client.publish(topic, json.dumps(message), qos=1, retain=False)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(
                f"Published provisioning config to device '{device_id}' "
                f"topic='{topic}'"
            )
            return True
        else:
            logger.error(
                f"Failed to publish provisioning config to '{device_id}': "
                f"MQTT error code {result.rc}"
            )
            return False
    except Exception as e:
        logger.error(
            f"Exception publishing provisioning config to '{device_id}': {e}",
            exc_info=True,
        )
        return False


def setup_mqtt(loop: asyncio.AbstractEventLoop) -> None:
    """
    Initialize and start the MQTT client.
    Call this once at application startup.

    Args:
        loop: The asyncio event loop for the main application
    """
    global _mqtt_client, _event_loop
    _event_loop = loop

    unique_id = f"ppf_backend_{os.getpid()}_{uuid.uuid4().hex[:8]}"
    client = mqtt.Client(client_id=unique_id, clean_session=True)
    client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

    # Enable TLS for cloud MQTT brokers (e.g., HiveMQ Cloud on port 8883)
    if settings.MQTT_USE_TLS:
        client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
        logger.info("MQTT TLS enabled")

    client.on_connect = _on_connect
    client.on_disconnect = _on_disconnect
    client.on_message = _on_message

    try:
        client.connect(
            settings.MQTT_BROKER_HOST,
            settings.MQTT_BROKER_PORT,
            settings.MQTT_KEEPALIVE,
        )
        client.loop_start()  # runs on background thread
        _mqtt_client = client
        logger.info(
            f"MQTT client connecting to "
            f"{settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}"
        )
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}", exc_info=True)
        raise


def teardown_mqtt() -> None:
    """Cleanly shut down the MQTT client. Call at application shutdown."""
    global _mqtt_client
    if _mqtt_client:
        _mqtt_client.loop_stop()
        _mqtt_client.disconnect()
        _mqtt_client = None
        logger.info("MQTT client disconnected cleanly")
