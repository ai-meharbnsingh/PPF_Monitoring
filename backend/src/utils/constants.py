"""
Module: constants.py
Purpose:
    All application-wide constants and enumerations.
    Import from here instead of typing strings throughout the codebase.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from enum import Enum


# ─── User Roles ──────────────────────────────────────────────────────────────
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    OWNER = "owner"
    STAFF = "staff"
    CUSTOMER = "customer"


# ─── Job Statuses ─────────────────────────────────────────────────────────────
class JobStatus(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    QUALITY_CHECK = "quality_check"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ─── Valid Job Status Transitions ─────────────────────────────────────────────
# Maps: current_status → set of allowed next statuses
JOB_STATUS_TRANSITIONS: dict[str, set[str]] = {
    JobStatus.WAITING: {JobStatus.IN_PROGRESS, JobStatus.CANCELLED},
    JobStatus.IN_PROGRESS: {JobStatus.QUALITY_CHECK, JobStatus.CANCELLED},
    JobStatus.QUALITY_CHECK: {JobStatus.COMPLETED, JobStatus.IN_PROGRESS, JobStatus.CANCELLED},
    JobStatus.COMPLETED: set(),       # terminal state
    JobStatus.CANCELLED: set(),       # terminal state
}


# ─── Work Types ───────────────────────────────────────────────────────────────
class WorkType(str, Enum):
    FULL_PPF = "Full PPF"
    PARTIAL_PPF = "Partial PPF"
    CERAMIC_COATING = "Ceramic Coating"
    CUSTOM = "Custom"


# Work type default durations (minutes)
WORK_TYPE_DEFAULT_DURATION: dict[str, int] = {
    WorkType.FULL_PPF: 360,
    WorkType.PARTIAL_PPF: 180,
    WorkType.CERAMIC_COATING: 240,
    WorkType.CUSTOM: 0,
}


# ─── Pit Status ───────────────────────────────────────────────────────────────
class PitStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    MAINTENANCE = "maintenance"


# ─── Device Status ────────────────────────────────────────────────────────────
class DeviceStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    SUSPENDED = "suspended"
    MAINTENANCE = "maintenance"


# ─── Device Commands ──────────────────────────────────────────────────────────
class DeviceCommand(str, Enum):
    DISABLE = "DISABLE"
    ENABLE = "ENABLE"
    RESTART = "RESTART"
    UPDATE_FIRMWARE = "UPDATE_FIRMWARE"
    SET_INTERVAL = "SET_INTERVAL"


class DeviceCommandStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"


# ─── Subscription ─────────────────────────────────────────────────────────────
class SubscriptionPlan(str, Enum):
    TRIAL = "trial"
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# ─── Alert Types ──────────────────────────────────────────────────────────────
class AlertType(str, Enum):
    HIGH_PM25 = "high_pm25"
    HIGH_PM10 = "high_pm10"
    HIGH_IAQ = "high_iaq"
    TEMP_TOO_LOW = "temp_too_low"
    TEMP_TOO_HIGH = "temp_too_high"
    HUMIDITY_TOO_HIGH = "humidity_too_high"
    DEVICE_OFFLINE = "device_offline"
    CAMERA_OFFLINE = "camera_offline"
    LICENSE_INVALID = "license_invalid"
    SUBSCRIPTION_EXPIRING = "subscription_expiring"
    SUBSCRIPTION_SUSPENDED = "subscription_suspended"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ─── Sensor Types ─────────────────────────────────────────────────────────────
class SensorTypeCode(str, Enum):
    DHT22 = "DHT22"
    DHT11 = "DHT11"
    PMS5003 = "PMS5003"
    BME680 = "BME680"
    BME688 = "BME688"


# ─── Subscription Plans ───────────────────────────────────────────────────────
PLAN_MONTHLY_FEES_INR: dict[str, float] = {
    SubscriptionPlan.TRIAL: 0,
    SubscriptionPlan.BASIC: 1000,
    SubscriptionPlan.STANDARD: 1500,
    SubscriptionPlan.PREMIUM: 2500,
}


# ─── Workshop Subscription Status ─────────────────────────────────────────────
class WorkshopSubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


# ─── MQTT Topic Templates ─────────────────────────────────────────────────────
MQTT_TOPIC_SENSOR_DATA = "workshop/{workshop_id}/pit/{pit_id}/sensors"
MQTT_TOPIC_DEVICE_COMMAND = "workshop/{workshop_id}/device/{device_id}/command"
MQTT_TOPIC_DEVICE_STATUS = "workshop/{workshop_id}/device/{device_id}/status"

# Wildcard subscription patterns
MQTT_SUBSCRIBE_SENSOR_DATA = "workshop/+/pit/+/sensors"
MQTT_SUBSCRIBE_DEVICE_STATUS = "workshop/+/device/+/status"


# ─── WebSocket Event Types ────────────────────────────────────────────────────
class WSEvent(str, Enum):
    SENSOR_UPDATE = "sensor_update"
    JOB_STATUS = "job_status"
    ALERT = "alert"
    DEVICE_OFFLINE = "device_offline"
    DEVICE_ONLINE = "device_online"
    CAMERA_OFFLINE = "camera_offline"
    PONG = "pong"


# ─── Sensor Status Labels ─────────────────────────────────────────────────────
class SensorStatus(str, Enum):
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


# ─── License Key ──────────────────────────────────────────────────────────────
LICENSE_KEY_PREFIX = "LIC"
LICENSE_KEY_FORMAT = "LIC-{A}-{B}-{C}"   # e.g., LIC-4F8D-9K2L-3P7Q
