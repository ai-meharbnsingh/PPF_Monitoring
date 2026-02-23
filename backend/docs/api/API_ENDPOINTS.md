# API ENDPOINTS DOCUMENTATION
## Smart PPF Workshop Monitoring System — Backend API

> **Version:** 1.0
> **Date:** 2026-02-21
> **Base URL:** `https://api.ppf-monitor.com/api/v1`
> **WebSocket URL:** `wss://api.ppf-monitor.com/ws`
> **Auth:** Bearer JWT Token (except /auth/login and /health)
> **Content-Type:** `application/json`

---

## TABLE OF CONTENTS

1. [Authentication](#1-authentication)
2. [Workshops](#2-workshops)
3. [Pits](#3-pits)
4. [Devices](#4-devices)
5. [Sensor Data](#5-sensor-data)
6. [Jobs](#6-jobs)
7. [Users](#7-users)
8. [Alerts](#8-alerts)
9. [Streams (Video)](#9-streams-video)
10. [Subscriptions](#10-subscriptions)
11. [Admin](#11-admin)
12. [WebSocket Events](#12-websocket-events)
13. [Health & Metrics](#13-health--metrics)
14. [Error Codes Reference](#14-error-codes-reference)
15. [Role-Based Access Table](#15-role-based-access-table)

---

## GLOBAL CONVENTIONS

### Request Headers
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
X-Workshop-ID: <workshop_id>          (optional, for super_admin multi-tenant)
```

### Standard Response Envelope
```json
{
  "success": true,
  "data": { ... },
  "message": "Human-readable message",
  "timestamp": "2026-02-21T10:30:00Z"
}
```

### Standard Error Response
```json
{
  "success": false,
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Job with ID 42 not found",
    "details": { ... }
  },
  "timestamp": "2026-02-21T10:30:00Z"
}
```

### Pagination (for list endpoints)
```
Query params: ?page=1&limit=20&sort_by=created_at&sort_order=desc

Response includes:
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

### Date Format
All dates in ISO 8601 with timezone: `2026-02-21T10:30:00Z`

---

## 1. AUTHENTICATION

### POST `/auth/login`
**Access:** Public

Login and receive JWT tokens.

**Request Body:**
```json
{
  "username": "owner_rays_ppf",
  "password": "SecurePass123"
}
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "user": {
      "id": 1,
      "username": "owner_rays_ppf",
      "role": "owner",
      "workshop_id": 3,
      "first_name": "Rahul",
      "is_temporary_password": false
    }
  }
}
```

**Errors:**
- `401 INVALID_CREDENTIALS` — Wrong username/password
- `401 ACCOUNT_LOCKED` — Too many failed attempts; includes `locked_until` timestamp
- `401 ACCOUNT_DISABLED` — Account deactivated by admin

---

### POST `/auth/logout`
**Access:** All authenticated users

Invalidate current token (server-side blocklist).

**Response `200 OK`:**
```json
{ "success": true, "message": "Logged out successfully" }
```

---

### GET `/auth/me`
**Access:** All authenticated users

Get current user profile.

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "owner_rays_ppf",
    "role": "owner",
    "workshop_id": 3,
    "workshop_name": "Rays PPF Delhi",
    "first_name": "Rahul",
    "last_name": "Sharma",
    "email": "rahul@rays-ppf.com",
    "phone": "+91-9876543210",
    "last_login": "2026-02-21T08:00:00Z"
  }
}
```

---

### POST `/auth/change-password`
**Access:** All authenticated users

**Request Body:**
```json
{
  "current_password": "OldPass123",
  "new_password": "NewSecurePass456"
}
```

**Response `200 OK`:**
```json
{ "success": true, "message": "Password changed successfully" }
```

**Errors:**
- `400 INVALID_CURRENT_PASSWORD`
- `400 PASSWORD_TOO_WEAK` — Minimum 8 chars, 1 uppercase, 1 number

---

### POST `/auth/refresh-token`
**Access:** All authenticated users

Refresh JWT before it expires.

**Request Body:**
```json
{ "access_token": "current_token_here" }
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "access_token": "new_token_here",
    "expires_in": 86400
  }
}
```

---

## 2. WORKSHOPS

### GET `/workshops`
**Access:** `super_admin` only

List all workshops (multi-tenant view).

**Query Params:** `?page=1&limit=20&status=active&search=rays`

**Response `200 OK`:**
```json
{
  "success": true,
  "data": [
    {
      "id": 3,
      "name": "Rays PPF Delhi",
      "slug": "rays-ppf-delhi",
      "city": "Delhi",
      "total_pits": 3,
      "subscription_status": "active",
      "subscription_plan": "standard",
      "is_active": true,
      "created_at": "2026-01-15T00:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

---

### POST `/workshops`
**Access:** `super_admin` only

Create a new workshop tenant.

**Request Body:**
```json
{
  "name": "Rays PPF Delhi",
  "address": "123 Main St, Lajpat Nagar",
  "city": "Delhi",
  "state": "Delhi",
  "phone": "+91-9876543210",
  "email": "contact@rays-ppf.com",
  "subscription_plan": "standard",
  "timezone": "Asia/Kolkata"
}
```

**Response `201 Created`:**
```json
{
  "success": true,
  "data": {
    "workshop_id": 3,
    "slug": "rays-ppf-delhi",
    "owner_credentials": {
      "username": "owner_rays_ppf_delhi",
      "temporary_password": "TempPass@2026"
    },
    "message": "Workshop created. Credentials sent to owner."
  }
}
```

---

### GET `/workshops/{workshop_id}`
**Access:** `super_admin`, `owner` (own workshop only)

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "id": 3,
    "name": "Rays PPF Delhi",
    "slug": "rays-ppf-delhi",
    "address": "123 Main St",
    "city": "Delhi",
    "state": "Delhi",
    "phone": "+91-9876543210",
    "email": "contact@rays-ppf.com",
    "total_pits": 3,
    "subscription_plan": "standard",
    "subscription_status": "active",
    "subscription_expires_at": "2026-12-31T23:59:59Z",
    "timezone": "Asia/Kolkata",
    "is_active": true,
    "created_at": "2026-01-15T00:00:00Z"
  }
}
```

---

### PATCH `/workshops/{workshop_id}`
**Access:** `super_admin`, `owner` (own workshop; limited fields)

**Request Body (any updatable fields):**
```json
{
  "name": "Rays PPF & Ceramic Delhi",
  "phone": "+91-9876543211",
  "email": "newcontact@rays-ppf.com"
}
```

**Response `200 OK`:**
```json
{ "success": true, "data": { "workshop_id": 3, "updated_fields": ["name", "phone"] } }
```

---

## 3. PITS

### GET `/workshops/{workshop_id}/pits`
**Access:** `super_admin`, `owner`, `staff`

List all pits with current status.

**Response `200 OK`:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "pit_number": 1,
      "name": "Bay A",
      "status": "active",
      "camera_is_online": true,
      "camera_last_seen": "2026-02-21T10:29:00Z",
      "current_job": {
        "job_id": 42,
        "car_model": "Toyota Fortuner",
        "status": "in_progress",
        "estimated_end_time": "2026-02-21T16:00:00Z"
      },
      "latest_sensors": {
        "temperature": 24.5,
        "humidity": 58.2,
        "pm25": 14.6,
        "pm10": 22.1,
        "recorded_at": "2026-02-21T10:29:50Z"
      }
    }
  ]
}
```

---

### POST `/workshops/{workshop_id}/pits`
**Access:** `super_admin`, `owner`

Add a new pit to the workshop.

**Request Body:**
```json
{
  "pit_number": 4,
  "name": "Bay D",
  "camera_ip": "192.168.1.104",
  "camera_rtsp_url": "rtsp://admin:pass@192.168.1.104:554/Streaming/Channels/101",
  "camera_model": "Hikvision DS-2CD1323G0E-I",
  "camera_username": "admin"
}
```

**Response `201 Created`:**
```json
{
  "success": true,
  "data": { "pit_id": 4, "pit_number": 4, "name": "Bay D" }
}
```

---

### GET `/pits/{pit_id}`
**Access:** `super_admin`, `owner`, `staff` (assigned pits), `customer` (own pit)

Get full pit details including current sensor readings and active job.

---

### PATCH `/pits/{pit_id}`
**Access:** `super_admin`, `owner`

Update pit configuration (camera settings, name, status).

---

### DELETE `/pits/{pit_id}`
**Access:** `super_admin` only

**Note:** Requires no active jobs on the pit. Does not delete sensor history.

---

## 4. DEVICES

### GET `/workshops/{workshop_id}/devices`
**Access:** `super_admin`, `owner`

List all ESP32 devices with real-time status.

**Response `200 OK`:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "device_id": "ESP32-A1B2C3D4E5F6",
      "license_key": "LIC-4F8D-9K2L-3P7Q",
      "pit_id": 1,
      "pit_name": "Bay A",
      "firmware_version": "1.0.0",
      "primary_sensor": "DHT22",
      "air_quality_sensor": "PMS5003",
      "status": "active",
      "is_online": true,
      "last_seen": "2026-02-21T10:29:55Z",
      "report_interval_seconds": 10
    }
  ]
}
```

---

### POST `/devices`
**Access:** `super_admin` only

Register a new ESP32 device and generate a license key.

**Request Body:**
```json
{
  "workshop_id": 3,
  "pit_id": 1,
  "device_id": "ESP32-A1B2C3D4E5F6",
  "mac_address": "A1:B2:C3:D4:E5:F6",
  "firmware_version": "1.0.0",
  "primary_sensor_type": "DHT22",
  "air_quality_sensor_type": "PMS5003",
  "report_interval_seconds": 10,
  "notes": "Installed in Bay A on 2026-02-21"
}
```

**Response `201 Created`:**
```json
{
  "success": true,
  "data": {
    "device_id": "ESP32-A1B2C3D4E5F6",
    "license_key": "LIC-4F8D-9K2L-3P7Q",
    "mqtt_topic": "workshop/3/pit/1/sensors",
    "command_topic": "workshop/3/device/ESP32-A1B2C3D4E5F6/command",
    "firmware_config": {
      "mqtt_broker": "10.8.0.1",
      "mqtt_port": 1883,
      "workshop_id": "3",
      "pit_id": "1",
      "device_id": "ESP32-A1B2C3D4E5F6",
      "license_key": "LIC-4F8D-9K2L-3P7Q"
    }
  }
}
```

---

### GET `/devices/{device_id}`
**Access:** `super_admin`, `owner`

Full device details including sensor config and command history.

---

### PATCH `/devices/{device_id}`
**Access:** `super_admin`, `owner`

Update device configuration (sensor types, report interval, notes).

---

### POST `/devices/{device_id}/commands`
**Access:** `super_admin` only (DISABLE/ENABLE/UPDATE_FIRMWARE), `owner` (RESTART only)

Send a command to an ESP32 device via MQTT.

**Request Body:**
```json
{
  "command": "DISABLE",
  "reason": "subscription_suspended",
  "payload": {}
}
```

**Available Commands:**

| command | Access | Description |
|---------|--------|-------------|
| `DISABLE` | super_admin | Stop sensor reporting (kill-switch) |
| `ENABLE` | super_admin | Resume sensor reporting |
| `RESTART` | super_admin, owner | Reboot the ESP32 |
| `UPDATE_FIRMWARE` | super_admin | OTA firmware update |
| `SET_INTERVAL` | super_admin, owner | Change reporting interval |

**Response `202 Accepted`:**
```json
{
  "success": true,
  "data": {
    "command_id": 15,
    "status": "sent",
    "mqtt_topic": "workshop/3/device/ESP32-A1B2C3D4E5F6/command"
  }
}
```

---

### GET `/devices/{device_id}/commands`
**Access:** `super_admin`, `owner`

Command history for a device.

**Query Params:** `?limit=20&status=acknowledged`

---

## 5. SENSOR DATA

### GET `/pits/{pit_id}/sensors/latest`
**Access:** `super_admin`, `owner`, `staff`, `customer` (own pit)

Get the most recent sensor reading for a pit.

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "pit_id": 1,
    "device_id": "ESP32-A1B2C3D4E5F6",
    "sensor_config": {
      "primary": "DHT22",
      "air_quality": "PMS5003"
    },
    "readings": {
      "temperature": 24.5,
      "humidity": 58.2,
      "pm1": 8.2,
      "pm25": 14.6,
      "pm10": 22.1,
      "pressure": null,
      "iaq": null
    },
    "status": {
      "temperature": "normal",
      "humidity": "normal",
      "pm25": "good",
      "pm10": "good"
    },
    "is_online": true,
    "recorded_at": "2026-02-21T10:29:50Z",
    "server_received_at": "2026-02-21T10:29:51Z"
  }
}
```

**Status values:** `good`, `warning`, `critical`, `unknown`

---

### GET `/pits/{pit_id}/sensors/history`
**Access:** `super_admin`, `owner`, `staff`, `customer` (own pit, last 24h only)

**Query Params:**
```
?from=2026-02-21T00:00:00Z
&to=2026-02-21T23:59:59Z
&fields=temperature,humidity,pm25,pm10   (optional, filters columns)
&interval=5m                              (optional: 1m, 5m, 15m, 1h — server-side averaging)
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "pit_id": 1,
    "from": "2026-02-21T00:00:00Z",
    "to": "2026-02-21T23:59:59Z",
    "interval": "5m",
    "count": 288,
    "readings": [
      {
        "timestamp": "2026-02-21T00:00:00Z",
        "temperature": 22.1,
        "humidity": 55.3,
        "pm25": 10.2,
        "pm10": 15.8
      }
    ]
  }
}
```

---

### GET `/workshops/{workshop_id}/sensors/summary`
**Access:** `super_admin`, `owner`

Snapshot of all pits' latest sensor readings in one call (dashboard overview).

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "workshop_id": 3,
    "pits": [
      {
        "pit_id": 1,
        "pit_name": "Bay A",
        "is_device_online": true,
        "temperature": 24.5,
        "humidity": 58.2,
        "pm25": 14.6,
        "pm25_status": "good",
        "recorded_at": "2026-02-21T10:29:50Z"
      },
      {
        "pit_id": 2,
        "pit_name": "Bay B",
        "is_device_online": false,
        "temperature": null,
        "humidity": null,
        "pm25": null,
        "pm25_status": "unknown",
        "recorded_at": null
      }
    ]
  }
}
```

---

### POST `/sensors/ingest`
**Access:** MQTT internal only (not exposed to external clients)

> **Note:** Sensor data is ingested via MQTT, not HTTP. This internal endpoint is called by the MQTT subscriber service to persist data. It is not accessible from outside the server.

---

## 6. JOBS

### GET `/workshops/{workshop_id}/jobs`
**Access:** `super_admin`, `owner`, `staff`

List jobs for a workshop.

**Query Params:**
```
?status=in_progress           (filter by status)
?pit_id=1                     (filter by pit)
?date=2026-02-21              (filter by date)
?page=1&limit=20
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": [
    {
      "id": 42,
      "pit_id": 1,
      "pit_name": "Bay A",
      "customer_name": "Rajesh Kumar",
      "car_model": "Toyota Fortuner",
      "car_plate": "DL01AB1234",
      "work_type": "Full PPF",
      "status": "in_progress",
      "estimated_duration_minutes": 360,
      "actual_start_time": "2026-02-21T09:00:00Z",
      "estimated_end_time": "2026-02-21T15:00:00Z",
      "time_remaining_minutes": 285,
      "progress_percent": 21,
      "created_at": "2026-02-21T08:45:00Z"
    }
  ]
}
```

---

### POST `/workshops/{workshop_id}/jobs`
**Access:** `super_admin`, `owner`, `staff`

Create a new job and optionally auto-create a customer account.

**Request Body:**
```json
{
  "pit_id": 1,
  "customer_name": "Rajesh Kumar",
  "customer_phone": "+91-9811223344",
  "car_model": "Toyota Fortuner",
  "car_plate": "DL01AB1234",
  "car_color": "White",
  "car_year": 2023,
  "work_type": "Full PPF",
  "work_description": "Full body PPF with ceramic coat on hood",
  "estimated_duration_minutes": 360,
  "scheduled_start_time": "2026-02-21T09:00:00Z",
  "quoted_price": 45000,
  "assigned_staff_ids": [5, 6],
  "send_credentials_via": "sms"
}
```

**Response `201 Created`:**
```json
{
  "success": true,
  "data": {
    "job_id": 42,
    "customer_credentials": {
      "username": "raj_kumar_abc",
      "temporary_password": "PPF@9834",
      "login_url": "https://view.ppf-monitor.com/login",
      "view_token": "tok_xyz123",
      "expires_at": "2026-02-22T15:00:00Z"
    },
    "message": "Credentials sent via SMS to +91-9811223344"
  }
}
```

---

### GET `/jobs/{job_id}`
**Access:** `super_admin`, `owner`, `staff`, `customer` (own job)

Full job details including status history.

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "id": 42,
    "workshop_id": 3,
    "pit_id": 1,
    "pit_name": "Bay A",
    "customer": {
      "name": "Rajesh Kumar",
      "phone": "+91-9811223344"
    },
    "car": {
      "model": "Toyota Fortuner",
      "plate": "DL01AB1234",
      "color": "White",
      "year": 2023
    },
    "work_type": "Full PPF",
    "work_description": "Full body PPF...",
    "status": "in_progress",
    "estimated_duration_minutes": 360,
    "actual_start_time": "2026-02-21T09:00:00Z",
    "estimated_end_time": "2026-02-21T15:00:00Z",
    "time_remaining_minutes": 285,
    "progress_percent": 21,
    "quoted_price": 45000,
    "assigned_staff": [
      { "id": 5, "name": "Amit Singh" },
      { "id": 6, "name": "Vijay Kumar" }
    ],
    "status_history": [
      {
        "from": null,
        "to": "waiting",
        "changed_by": "owner_rays_ppf",
        "at": "2026-02-21T08:45:00Z"
      },
      {
        "from": "waiting",
        "to": "in_progress",
        "changed_by": "amit_staff",
        "at": "2026-02-21T09:00:00Z"
      }
    ],
    "created_at": "2026-02-21T08:45:00Z"
  }
}
```

---

### PATCH `/jobs/{job_id}/status`
**Access:** `super_admin`, `owner`, `staff`

Update job status.

**Request Body:**
```json
{
  "status": "quality_check",
  "notes": "PPF applied, now checking for bubbles"
}
```

**Valid Transitions:**

| From | To | Allowed By |
|------|----|-----------|
| `waiting` | `in_progress` | owner, staff |
| `waiting` | `cancelled` | owner |
| `in_progress` | `quality_check` | owner, staff |
| `in_progress` | `cancelled` | owner |
| `quality_check` | `completed` | owner |
| `quality_check` | `in_progress` | owner, staff |
| `quality_check` | `cancelled` | owner |

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "job_id": 42,
    "previous_status": "in_progress",
    "new_status": "quality_check",
    "updated_at": "2026-02-21T14:00:00Z"
  }
}
```

---

### PATCH `/jobs/{job_id}/time`
**Access:** `super_admin`, `owner`

Update estimated end time for a job (real-time adjustment).

**Request Body:**
```json
{
  "estimated_end_time": "2026-02-21T17:00:00Z",
  "reason": "Complex PPF around spoiler taking longer"
}
```

---

### PATCH `/jobs/{job_id}`
**Access:** `super_admin`, `owner`

Update job details (car info, description, price).

---

### DELETE `/jobs/{job_id}`
**Access:** `super_admin`, `owner`

Cancel and delete a job (only if status is `waiting` or `cancelled`). Completed jobs cannot be deleted.

---

### GET `/jobs/{job_id}/history`
**Access:** `super_admin`, `owner`

Full status change history for a job.

---

### GET `/jobs/{job_id}/sensor-report`
**Access:** `super_admin`, `owner`

Environmental conditions during the job (sensor readings from job start to end).

**Response:** Time-series sensor data filtered to job timeframe — used for job summary PDF.

---

## 7. USERS

### GET `/workshops/{workshop_id}/users`
**Access:** `super_admin`, `owner`

**Query Params:** `?role=staff&is_active=true`

**Response `200 OK`:**
```json
{
  "success": true,
  "data": [
    {
      "id": 5,
      "username": "amit_staff",
      "first_name": "Amit",
      "last_name": "Singh",
      "role": "staff",
      "phone": "+91-9876500001",
      "is_active": true,
      "last_login": "2026-02-21T09:00:00Z"
    }
  ]
}
```

---

### POST `/workshops/{workshop_id}/users`
**Access:** `super_admin`, `owner`

Create staff or operator account.

**Request Body:**
```json
{
  "first_name": "Suresh",
  "last_name": "Verma",
  "phone": "+91-9876500002",
  "role": "staff",
  "username": "suresh_staff"
}
```

**Response `201 Created`:**
```json
{
  "success": true,
  "data": {
    "user_id": 8,
    "username": "suresh_staff",
    "temporary_password": "Staff@5678"
  }
}
```

---

### GET `/users/{user_id}`
**Access:** `super_admin`, `owner` (own workshop), self

---

### PATCH `/users/{user_id}`
**Access:** `super_admin`, `owner` (own workshop staff), self (own profile only)

---

### DELETE `/users/{user_id}`
**Access:** `super_admin`, `owner`

Deactivates the user (`is_active = FALSE`). Does not hard-delete.

---

## 8. ALERTS

### GET `/workshops/{workshop_id}/alerts`
**Access:** `super_admin`, `owner`, `staff`

**Query Params:** `?severity=critical&is_acknowledged=false&limit=50`

**Response `200 OK`:**
```json
{
  "success": true,
  "data": [
    {
      "id": 201,
      "pit_id": 2,
      "pit_name": "Bay B",
      "device_id": "ESP32-B2C3D4E5F6A1",
      "alert_type": "high_pm25",
      "severity": "warning",
      "message": "PM2.5 level 38.2 μg/m³ exceeded warning threshold of 35.4 μg/m³ in Bay B",
      "trigger_value": 38.2,
      "threshold_value": 35.4,
      "is_acknowledged": false,
      "created_at": "2026-02-21T10:15:00Z"
    }
  ]
}
```

---

### PATCH `/alerts/{alert_id}/acknowledge`
**Access:** `super_admin`, `owner`, `staff`

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "alert_id": 201,
    "acknowledged_by": "owner_rays_ppf",
    "acknowledged_at": "2026-02-21T10:20:00Z"
  }
}
```

---

### GET `/workshops/{workshop_id}/alert-config`
**Access:** `super_admin`, `owner`

Get current alert threshold configuration.

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "workshop_id": 3,
    "temperature": { "min": 15.0, "max": 35.0, "unit": "°C" },
    "humidity": { "max": 70.0, "unit": "%" },
    "pm25": { "warning": 12.0, "critical": 35.4, "unit": "μg/m³" },
    "pm10": { "warning": 54.0, "critical": 154.0, "unit": "μg/m³" },
    "iaq": { "warning": 100.0, "critical": 150.0 },
    "device_offline_threshold_seconds": 60,
    "camera_offline_threshold_seconds": 30,
    "notifications": {
      "sms": true,
      "email": false,
      "webhook": false
    }
  }
}
```

---

### PUT `/workshops/{workshop_id}/alert-config`
**Access:** `super_admin`, `owner`

Update alert thresholds. Full replacement of config.

**Request Body:**
```json
{
  "temp_min": 18.0,
  "temp_max": 32.0,
  "humidity_max": 65.0,
  "pm25_warning": 12.0,
  "pm25_critical": 35.4,
  "pm10_warning": 54.0,
  "pm10_critical": 154.0,
  "iaq_warning": 100.0,
  "iaq_critical": 150.0,
  "device_offline_threshold_seconds": 60,
  "notify_via_sms": true,
  "notify_via_email": true
}
```

---

## 9. STREAMS (VIDEO)

### GET `/pits/{pit_id}/stream`
**Access:** `super_admin`, `owner`, `staff`, `customer` (own pit)

Get authenticated stream URL for a pit's Hikvision camera.

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "pit_id": 1,
    "stream_url": "https://video.ppf-monitor.com/pit/1/live?token=stream_tok_abc",
    "protocol": "webrtc",
    "hls_fallback_url": "https://video.ppf-monitor.com/pit/1/live.m3u8?token=stream_tok_abc",
    "token_expires_at": "2026-02-21T11:30:00Z",
    "camera_is_online": true
  }
}
```

**Notes:**
- `webrtc` → low latency (~1–2 seconds), preferred
- `hls_fallback_url` → compatibility mode (~5–10 second delay)
- Stream token expires every 1 hour; call this endpoint to refresh
- Camera offline → returns `camera_is_online: false` with no URL

---

## 10. SUBSCRIPTIONS

### GET `/workshops/{workshop_id}/subscriptions`
**Access:** `super_admin`, `owner`

List all device subscriptions for a workshop.

**Response `200 OK`:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "device_id": "ESP32-A1B2C3D4E5F6",
      "license_key": "LIC-4F8D-9K2L-3P7Q",
      "pit_name": "Bay A",
      "plan": "standard",
      "status": "active",
      "monthly_fee": 1500,
      "currency": "INR",
      "expires_at": "2026-12-31T23:59:59Z",
      "next_payment_date": "2026-03-01T00:00:00Z",
      "days_until_expiry": 313
    }
  ]
}
```

---

### PATCH `/subscriptions/{subscription_id}`
**Access:** `super_admin` only

Update subscription status or plan (used for payment events).

**Request Body:**
```json
{
  "status": "active",
  "payment_reference": "razorpay_order_abc123",
  "last_payment_date": "2026-02-21T10:00:00Z",
  "next_payment_date": "2026-03-21T10:00:00Z"
}
```

**Side Effects:**
- Setting `status = "suspended"` → automatically sends `DISABLE` command to device
- Setting `status = "active"` → automatically sends `ENABLE` command to device

---

### POST `/subscriptions/{subscription_id}/suspend`
**Access:** `super_admin` only

Manually suspend a subscription (payment overdue).

**Request Body:**
```json
{ "reason": "Payment overdue by 15 days" }
```

---

### POST `/subscriptions/{subscription_id}/activate`
**Access:** `super_admin` only

Re-activate a suspended subscription.

---

## 11. ADMIN

### GET `/admin/workshops`
**Access:** `super_admin` only

All workshops with usage stats.

---

### POST `/admin/workshops/{workshop_id}/suspend`
**Access:** `super_admin` only

Suspend entire workshop (suspends all devices).

---

### POST `/admin/workshops/{workshop_id}/activate`
**Access:** `super_admin` only

Re-activate a suspended workshop.

---

### GET `/admin/metrics`
**Access:** `super_admin` only

System-wide metrics for operations dashboard.

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "total_workshops": 12,
    "active_workshops": 11,
    "total_pits": 34,
    "active_devices": 32,
    "online_devices": 29,
    "active_jobs": 8,
    "sensor_readings_today": 142560,
    "active_alerts": 3,
    "subscriptions_expiring_7_days": 2,
    "server_uptime_hours": 720
  }
}
```

---

### GET `/admin/audit-logs`
**Access:** `super_admin` only

**Query Params:** `?action=device.disabled&workshop_id=3&from=2026-02-01&limit=100`

---

## 12. WEBSOCKET EVENTS

### Connection
```
wss://api.ppf-monitor.com/ws?token=<JWT_TOKEN>
```

### Client → Server Messages

**Subscribe to a pit:**
```json
{ "action": "subscribe_pit", "pit_id": 1 }
```

**Subscribe to all pits (owner only):**
```json
{ "action": "subscribe_workshop", "workshop_id": 3 }
```

**Unsubscribe:**
```json
{ "action": "unsubscribe", "pit_id": 1 }
```

**Heartbeat (keep-alive):**
```json
{ "action": "ping" }
```

---

### Server → Client Events

**Sensor update (every 10 seconds per pit):**
```json
{
  "event": "sensor_update",
  "pit_id": 1,
  "data": {
    "temperature": 24.5,
    "humidity": 58.2,
    "pm25": 14.6,
    "pm10": 22.1,
    "pm1": 8.2,
    "iaq": null,
    "is_online": true,
    "recorded_at": "2026-02-21T10:30:00Z"
  }
}
```

**Job status changed:**
```json
{
  "event": "job_status",
  "job_id": 42,
  "pit_id": 1,
  "data": {
    "previous_status": "in_progress",
    "new_status": "quality_check",
    "time_remaining_minutes": 30,
    "updated_at": "2026-02-21T14:00:00Z"
  }
}
```

**Alert triggered:**
```json
{
  "event": "alert",
  "pit_id": 2,
  "data": {
    "alert_id": 201,
    "alert_type": "high_pm25",
    "severity": "warning",
    "message": "PM2.5 level 38.2 μg/m³ exceeded warning threshold in Bay B",
    "trigger_value": 38.2,
    "threshold_value": 35.4
  }
}
```

**Device went offline:**
```json
{
  "event": "device_offline",
  "pit_id": 1,
  "data": {
    "device_id": "ESP32-A1B2C3D4E5F6",
    "last_seen": "2026-02-21T10:29:00Z"
  }
}
```

**Device came back online:**
```json
{
  "event": "device_online",
  "pit_id": 1,
  "data": { "device_id": "ESP32-A1B2C3D4E5F6" }
}
```

**Pong (heartbeat response):**
```json
{ "event": "pong", "timestamp": "2026-02-21T10:30:00Z" }
```

---

## 13. HEALTH & METRICS

### GET `/health`
**Access:** Public

System health check — used by load balancers and monitoring.

**Response `200 OK`:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "database": "connected",
    "mqtt_broker": "connected",
    "media_server": "connected"
  },
  "uptime_seconds": 86400,
  "timestamp": "2026-02-21T10:30:00Z"
}
```

**Response `503 Service Unavailable`:** (if any critical component is down)

---

### GET `/metrics`
**Access:** `super_admin` only (or internal monitoring IP)

Prometheus-compatible metrics endpoint.

---

## 14. ERROR CODES REFERENCE

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 400 | `VALIDATION_ERROR` | Request body validation failed |
| 400 | `INVALID_STATUS_TRANSITION` | Job status change not allowed |
| 400 | `PASSWORD_TOO_WEAK` | Password doesn't meet requirements |
| 401 | `INVALID_CREDENTIALS` | Wrong username/password |
| 401 | `TOKEN_EXPIRED` | JWT has expired |
| 401 | `TOKEN_INVALID` | JWT is malformed or tampered |
| 401 | `ACCOUNT_LOCKED` | Too many failed login attempts |
| 403 | `INSUFFICIENT_PERMISSIONS` | Role not allowed for this action |
| 403 | `WORKSHOP_ACCESS_DENIED` | Accessing another workshop's data |
| 403 | `PIT_ACCESS_DENIED` | Customer accessing unassigned pit |
| 404 | `WORKSHOP_NOT_FOUND` | Workshop ID doesn't exist |
| 404 | `JOB_NOT_FOUND` | Job ID doesn't exist |
| 404 | `DEVICE_NOT_FOUND` | Device ID doesn't exist |
| 404 | `PIT_NOT_FOUND` | Pit ID doesn't exist |
| 409 | `DUPLICATE_DEVICE_ID` | Device already registered |
| 409 | `DUPLICATE_PIT_NUMBER` | Pit number already exists in workshop |
| 409 | `JOB_ALREADY_ACTIVE` | Pit already has an active job |
| 422 | `INVALID_LICENSE_KEY` | License key format invalid |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Unexpected server error |
| 503 | `SERVICE_UNAVAILABLE` | Database or critical service down |

---

## 15. ROLE-BASED ACCESS TABLE

| Endpoint | super_admin | owner | staff | customer |
|----------|:-----------:|:-----:|:-----:|:--------:|
| `POST /auth/login` | ✅ | ✅ | ✅ | ✅ |
| `GET /auth/me` | ✅ | ✅ | ✅ | ✅ |
| `GET /workshops` | ✅ | ❌ | ❌ | ❌ |
| `POST /workshops` | ✅ | ❌ | ❌ | ❌ |
| `GET /workshops/{id}` | ✅ | ✅ own | ❌ | ❌ |
| `GET /workshops/{id}/pits` | ✅ | ✅ | ✅ | ❌ |
| `POST /workshops/{id}/pits` | ✅ | ✅ | ❌ | ❌ |
| `GET /pits/{id}` | ✅ | ✅ | ✅ assigned | ✅ own |
| `GET /workshops/{id}/devices` | ✅ | ✅ | ❌ | ❌ |
| `POST /devices` | ✅ | ❌ | ❌ | ❌ |
| `POST /devices/{id}/commands` | ✅ | RESTART only | ❌ | ❌ |
| `GET /pits/{id}/sensors/latest` | ✅ | ✅ | ✅ | ✅ own |
| `GET /pits/{id}/sensors/history` | ✅ | ✅ | ✅ | ✅ own 24h |
| `GET /workshops/{id}/jobs` | ✅ | ✅ | ✅ | ❌ |
| `POST /workshops/{id}/jobs` | ✅ | ✅ | ✅ | ❌ |
| `PATCH /jobs/{id}/status` | ✅ | ✅ | ✅ | ❌ |
| `GET /jobs/{id}` | ✅ | ✅ | ✅ | ✅ own |
| `GET /workshops/{id}/alerts` | ✅ | ✅ | ✅ | ❌ |
| `PUT /workshops/{id}/alert-config` | ✅ | ✅ | ❌ | ❌ |
| `GET /pits/{id}/stream` | ✅ | ✅ | ✅ | ✅ own |
| `GET /workshops/{id}/subscriptions` | ✅ | ✅ | ❌ | ❌ |
| `PATCH /subscriptions/{id}` | ✅ | ❌ | ❌ | ❌ |
| `GET /admin/*` | ✅ | ❌ | ❌ | ❌ |
| `GET /health` | ✅ | ✅ | ✅ | ✅ |

---

**Document Version:** 1.1
**Last Updated:** 2026-02-24
**Author:** PPF Monitoring System Team
**Status:** Phase 1 API validation complete — 126/126 tests passing
