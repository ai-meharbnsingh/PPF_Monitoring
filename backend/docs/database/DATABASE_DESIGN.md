# DATABASE DESIGN DOCUMENT
## Smart PPF Workshop Monitoring System

> **Version:** 1.0
> **Date:** 2026-02-21
> **Schema Version:** v1.0.0
> **Database:** PostgreSQL 15+
> **Status:** Production Design — Ready for Migration

---

## TABLE OF CONTENTS

1. [Overview & Design Decisions](#1-overview--design-decisions)
2. [Entity Relationship Overview](#2-entity-relationship-overview)
3. [Table Specifications](#3-table-specifications)
   - [sensor_types](#31-sensor_types)
   - [workshops](#32-workshops)
   - [users](#33-users)
   - [pits](#34-pits)
   - [devices](#35-devices)
   - [subscriptions](#36-subscriptions)
   - [sensor_data](#37-sensor_data)
   - [jobs](#38-jobs)
   - [job_status_history](#39-job_status_history)
   - [alert_configs](#310-alert_configs)
   - [alerts](#311-alerts)
   - [device_commands](#312-device_commands)
   - [audit_logs](#313-audit_logs)
4. [Indexes & Performance](#4-indexes--performance)
5. [Sensor Hardware Support](#5-sensor-hardware-support)
6. [Data Retention Policy](#6-data-retention-policy)
7. [Migration Strategy](#7-migration-strategy)
8. [Schema Changelog](#8-schema-changelog)

---

## 1. OVERVIEW & DESIGN DECISIONS

### 1.1 Purpose
This document defines the complete database schema for the PPF Workshop Monitoring System. The database stores:
- Workshop and organizational data
- Real-time sensor readings (temperature, humidity, air quality)
- Job/work order tracking
- Device licensing and subscription management
- Alerts and notifications
- Complete audit trails

### 1.2 Key Design Decisions

| Decision | Reason |
|---|---|
| **PostgreSQL** | JSONB support for flexible sensor payloads, strong FK constraints, TimescaleDB compatible for future time-series scaling |
| **Multi-sensor schema** | Supports DHT22+PMS5003 (primary) AND BME680 (alternative) in same table via nullable columns — no schema migration needed when switching sensors |
| **TIMESTAMPTZ everywhere** | All timestamps stored with timezone (UTC internally), prevents ambiguity |
| **Soft deletes NOT used** | Jobs and sensor data are immutable. Workshops/users/devices use `is_active` flag |
| **sensor_types reference table** | Single source of truth for supported hardware — easily extend to new sensors |
| **workshop_id on sensor_data** | Denormalized for query performance — avoids JOIN on every dashboard query |
| **JSONB for extra payloads** | PMS5003 particle counts, BME680 gas resistance stored as JSONB to avoid schema bloat while keeping structured data for core fields |
| **Separate alert_configs table** | Each workshop has customizable thresholds, not hardcoded globally |

### 1.3 Sensor Hardware Strategy

The system is designed to support multiple sensor configurations:

```
Configuration A (PRIMARY - Your Hardware):
  ├── DHT22       → temperature, humidity
  └── PMS5003     → pm1, pm25, pm10, particle_counts

Configuration B (ALTERNATIVE - Original Plan):
  └── BME680      → temperature, humidity, pressure, gas_resistance, iaq

Configuration C (FUTURE - Enhanced):
  ├── DHT22       → temperature, humidity
  ├── PMS5003     → pm25, pm10
  └── BME680      → pressure, gas_resistance (supplement)
```

All configurations write to the same `sensor_data` table. Fields irrelevant to a sensor type are NULL.

---

## 2. ENTITY RELATIONSHIP OVERVIEW

```
                          ┌─────────────────┐
                          │   sensor_types  │ (reference)
                          │  DHT22/PMS5003  │
                          │    /BME680       │
                          └────────┬────────┘
                                   │ referenced by
                                   ▼
┌───────────┐    1:N    ┌──────────────────┐    1:N    ┌──────────┐
│   users   │◄──────────│   workshops      │──────────►│   pits   │
│(owner/    │           │                  │           │          │
│staff/     │           └──────────────────┘           └────┬─────┘
│customer)  │                    │ 1:N                       │ 1:N
└─────┬─────┘                    │                           ▼
      │                          ▼                    ┌──────────────┐
      │                ┌──────────────────┐           │   devices    │
      │                │  subscriptions   │           │  (ESP32 GW)  │
      │                └──────────────────┘           └──────┬───────┘
      │                                                       │
      │                         ┌─────────────────────────────┤
      │                         ▼                             ▼
      │                ┌──────────────┐             ┌──────────────────┐
      │                │     jobs     │             │   sensor_data    │
      └────────────────│              │             │ (time-series)    │
         customer_id   └──────┬───────┘             └──────────────────┘
                              │ 1:N
                              ▼
                    ┌──────────────────────┐
                    │  job_status_history  │
                    └──────────────────────┘

Additional Tables (operational):
  ├── alert_configs     (1:1 with workshops — threshold settings)
  ├── alerts            (N:1 with workshops/pits/devices)
  ├── device_commands   (N:1 with devices — kill-switch history)
  └── audit_logs        (append-only audit trail)
```

---

## 3. TABLE SPECIFICATIONS

---

### 3.1 sensor_types

**Purpose:** Reference table defining all supported sensor hardware. Adding new sensor support only requires inserting a row here, not schema migration.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | Internal ID |
| `code` | VARCHAR(20) | UNIQUE NOT NULL | Hardware identifier: `DHT22`, `PMS5003`, `BME680` |
| `name` | VARCHAR(50) | NOT NULL | Human-readable name |
| `manufacturer` | VARCHAR(50) | | Hardware manufacturer |
| `protocol` | VARCHAR(20) | | Communication: `UART`, `I2C`, `SPI`, `GPIO` |
| `capabilities` | JSONB | | What data this sensor provides |
| `description` | TEXT | | Additional notes |
| `is_active` | BOOLEAN | DEFAULT TRUE | Whether this sensor is currently supported |

**`capabilities` JSONB structure:**
```json
{
  "temperature": true,
  "humidity": true,
  "pressure": false,
  "pm25": false,
  "pm10": false,
  "iaq": false,
  "gas_resistance": false
}
```

**Seed Data:**
| code | name | protocol | capabilities |
|------|------|----------|--------------|
| `DHT22` | Capacitive Humidity & Temperature Sensor | GPIO | temp + humidity |
| `PMS5003` | Plantower Particulate Matter Sensor | UART | pm1 + pm25 + pm10 + particle_counts |
| `BME680` | Bosch Environmental Sensor | I2C | temp + humidity + pressure + gas + iaq |

---

### 3.2 workshops

**Purpose:** Represents a PPF business location. This is the top-level tenant in the multi-tenant architecture.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | Internal workshop ID |
| `name` | VARCHAR(100) | NOT NULL | Workshop business name |
| `slug` | VARCHAR(50) | UNIQUE NOT NULL | URL-safe identifier (e.g., `rays-ppf-delhi`) |
| `owner_user_id` | INT | FK → users(id) | The owner user account |
| `address` | TEXT | | Full street address |
| `city` | VARCHAR(50) | | City |
| `state` | VARCHAR(50) | | State/Province |
| `phone` | VARCHAR(20) | | Contact phone |
| `email` | VARCHAR(100) | | Contact email |
| `total_pits` | INT | DEFAULT 0 | Number of pits (updated automatically) |
| `subscription_plan` | VARCHAR(20) | DEFAULT 'trial' | `trial`, `basic`, `standard`, `premium` |
| `subscription_status` | VARCHAR(20) | DEFAULT 'trial' | `trial`, `active`, `suspended`, `expired` |
| `subscription_expires_at` | TIMESTAMPTZ | | When subscription expires |
| `timezone` | VARCHAR(50) | DEFAULT 'Asia/Kolkata' | Workshop local timezone |
| `is_active` | BOOLEAN | DEFAULT TRUE | Soft-disable without deletion |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

**Business Rules:**
- `slug` is auto-generated from `name` on creation
- `total_pits` is updated by trigger when pits are added/removed
- `subscription_status = 'suspended'` → all ESP32 devices receive DISABLE command
- Workshop deletion is never done — use `is_active = FALSE`

---

### 3.3 users

**Purpose:** All human users of the system — super admins, workshop owners, staff, and customers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | |
| `workshop_id` | INT | FK → workshops(id) | NULL for super_admin |
| `username` | VARCHAR(50) | UNIQUE NOT NULL | Login identifier |
| `email` | VARCHAR(100) | UNIQUE | Email (optional for customers) |
| `phone` | VARCHAR(20) | | Phone for SMS notifications |
| `password_hash` | VARCHAR(255) | NOT NULL | bcrypt hash (cost=12) |
| `role` | VARCHAR(20) | NOT NULL CHECK | `super_admin`, `owner`, `staff`, `customer` |
| `first_name` | VARCHAR(50) | | |
| `last_name` | VARCHAR(50) | | |
| `is_active` | BOOLEAN | DEFAULT TRUE | Account enabled/disabled |
| `is_temporary_password` | BOOLEAN | DEFAULT FALSE | Force password change on next login |
| `last_login` | TIMESTAMPTZ | | Last successful login |
| `login_attempt_count` | INT | DEFAULT 0 | Failed attempts counter |
| `locked_until` | TIMESTAMPTZ | | Account lockout expiry (after 5 failed attempts) |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**Role Permissions Matrix:**

| Action | super_admin | owner | staff | customer |
|--------|-------------|-------|-------|----------|
| View all workshops | ✅ | ❌ | ❌ | ❌ |
| Manage own workshop | ✅ | ✅ | ❌ | ❌ |
| Create/modify jobs | ✅ | ✅ | ✅* | ❌ |
| View all pits | ✅ | ✅ | ✅* | ❌ |
| View assigned pit | ✅ | ✅ | ✅ | ✅ |
| Kill-switch devices | ✅ | ❌ | ❌ | ❌ |
| Manage subscriptions | ✅ | ❌ | ❌ | ❌ |

*Staff: only their assigned pits

**Customer Account Notes:**
- Created automatically when a job is created
- `username` = auto-generated (e.g., `cust_abc123`)
- `is_temporary_password = TRUE` always
- Session expires after 24 hours or job completion
- Access is limited to their assigned pit's view

---

### 3.4 pits

**Purpose:** Represents one physical work bay/pit inside a workshop where cars are serviced.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | |
| `workshop_id` | INT | FK NOT NULL → workshops(id) | Parent workshop |
| `pit_number` | INT | NOT NULL | Sequential number within workshop (1, 2, 3…) |
| `name` | VARCHAR(50) | | Custom label: "Bay A", "Pit 1" |
| `description` | TEXT | | Optional notes |
| `status` | VARCHAR(20) | DEFAULT 'active' | `active`, `disabled`, `maintenance` |
| `camera_ip` | VARCHAR(50) | | Hikvision camera LAN IP |
| `camera_rtsp_url` | TEXT | | Full RTSP URL for stream |
| `camera_model` | VARCHAR(100) | | Camera model identifier |
| `camera_username` | VARCHAR(50) | | Camera login username |
| `camera_is_online` | BOOLEAN | DEFAULT FALSE | Real-time online status |
| `camera_last_seen` | TIMESTAMPTZ | | Last successful camera ping |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**Constraints:**
- `UNIQUE(workshop_id, pit_number)` — no duplicate pit numbers within a workshop
- Camera password is stored in environment/vault, NOT in database

---

### 3.5 devices

**Purpose:** Represents one Olimex ESP32-GATEWAY unit installed in a pit. Contains licensing and sensor configuration.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | |
| `pit_id` | INT | FK → pits(id) | Assigned pit (1:1 normally) |
| `workshop_id` | INT | FK NOT NULL → workshops(id) | Denormalized for fast queries |
| `device_id` | VARCHAR(50) | UNIQUE NOT NULL | MAC-based: `ESP32-A1B2C3D4E5F6` |
| `license_key` | VARCHAR(30) | UNIQUE NOT NULL | `LIC-XXXX-YYYY-ZZZZ` |
| `firmware_version` | VARCHAR(20) | | Current firmware: `1.0.0` |
| `primary_sensor_type_id` | INT | FK → sensor_types(id) | DHT22 or BME680 (temp/humidity) |
| `air_quality_sensor_type_id` | INT | FK → sensor_types(id) | PMS5003 (or NULL if BME680) |
| `ip_address` | VARCHAR(50) | | Device LAN IP |
| `mac_address` | VARCHAR(17) | | Hardware MAC address |
| `status` | VARCHAR(20) | DEFAULT 'active' | `active`, `disabled`, `suspended`, `maintenance` |
| `is_online` | BOOLEAN | DEFAULT FALSE | Real-time online status |
| `last_seen` | TIMESTAMPTZ | | Last any communication |
| `last_mqtt_message` | TIMESTAMPTZ | | Last MQTT message received |
| `report_interval_seconds` | INT | DEFAULT 10 | How often device sends data |
| `notes` | TEXT | | Installation notes |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**Sensor Configuration Examples:**

| Setup | primary_sensor_type_id | air_quality_sensor_type_id |
|-------|----------------------|---------------------------|
| DHT22 + PMS5003 (your hardware) | DHT22 | PMS5003 |
| BME680 only | BME680 | NULL |
| BME680 + PMS5003 (future) | BME680 | PMS5003 |

---

### 3.6 subscriptions

**Purpose:** Tracks device licensing and payment status. Used by the kill-switch system.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | |
| `workshop_id` | INT | FK NOT NULL → workshops(id) | |
| `device_id` | VARCHAR(50) | FK → devices(device_id) | Linked device |
| `license_key` | VARCHAR(30) | UNIQUE NOT NULL | Mirrors devices.license_key |
| `plan` | VARCHAR(20) | NOT NULL | `trial`, `basic`, `standard`, `premium` |
| `status` | VARCHAR(20) | NOT NULL | `active`, `suspended`, `expired`, `cancelled` |
| `monthly_fee` | DECIMAL(10,2) | | Fee in currency below |
| `currency` | VARCHAR(3) | DEFAULT 'INR' | |
| `starts_at` | TIMESTAMPTZ | DEFAULT NOW() | Subscription start |
| `expires_at` | TIMESTAMPTZ | | Subscription end |
| `trial_expires_at` | TIMESTAMPTZ | | Trial period end |
| `grace_period_days` | INT | DEFAULT 7 | Days after expiry before suspension |
| `last_payment_date` | TIMESTAMPTZ | | Last successful payment |
| `next_payment_date` | TIMESTAMPTZ | | Next due date |
| `payment_method` | VARCHAR(50) | | `razorpay`, `stripe`, `manual` |
| `payment_reference` | VARCHAR(100) | | Payment gateway reference ID |
| `notes` | TEXT | | Admin notes |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**Kill-Switch Flow:**
```
payment_overdue → status = 'suspended' → DISABLE command sent to device
payment_received → status = 'active'   → ENABLE command sent to device
```

---

### 3.7 sensor_data

**Purpose:** Time-series table storing all sensor readings from ESP32 devices. Designed to support DHT22+PMS5003 (primary) AND BME680 (alternative) in a single table via nullable columns.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PK | |
| `device_id` | VARCHAR(50) | NOT NULL FK → devices | |
| `pit_id` | INT | NOT NULL FK → pits | |
| `workshop_id` | INT | NOT NULL FK → workshops | Denormalized for performance |
| `primary_sensor_type` | VARCHAR(10) | | `DHT22` or `BME680` |
| `air_quality_sensor_type` | VARCHAR(10) | | `PMS5003`, `BME680`, or NULL |
| **DHT22 / BME680 shared fields** | | | |
| `temperature` | FLOAT | | Celsius — from DHT22 or BME680 |
| `humidity` | FLOAT | | % (0–100) — from DHT22 or BME680 |
| **BME680 only fields** | | | |
| `pressure` | FLOAT | | hPa — NULL for DHT22 |
| `gas_resistance` | FLOAT | | Ohms — NULL for DHT22 |
| `iaq` | FLOAT | | IAQ index (0–500) — NULL for DHT22 |
| `iaq_accuracy` | INT | | BSEC accuracy 0–3 — NULL for DHT22 |
| **PMS5003 fields** | | | |
| `pm1` | FLOAT | | PM1.0 μg/m³ |
| `pm25` | FLOAT | | PM2.5 μg/m³ |
| `pm10` | FLOAT | | PM10 μg/m³ |
| `particles_03um` | INT | | Particles >0.3μm per 0.1L |
| `particles_05um` | INT | | Particles >0.5μm per 0.1L |
| `particles_10um` | INT | | Particles >1.0μm per 0.1L |
| `particles_25um` | INT | | Particles >2.5μm per 0.1L |
| `particles_50um` | INT | | Particles >5.0μm per 0.1L |
| `particles_100um` | INT | | Particles >10.0μm per 0.1L |
| **Data quality** | | | |
| `is_valid` | BOOLEAN | DEFAULT TRUE | False if sensor returned error |
| `validation_notes` | TEXT | | Why data is invalid |
| `device_timestamp` | TIMESTAMPTZ | | Timestamp from ESP32 clock |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Server ingestion time |

**Example Rows:**

*DHT22 + PMS5003 (your hardware):*
```
primary_sensor_type: DHT22
air_quality_sensor_type: PMS5003
temperature: 24.5,  humidity: 58.2
pressure: NULL, gas_resistance: NULL, iaq: NULL
pm1: 8.2,  pm25: 14.6,  pm10: 22.1
particles_03um: 1250, particles_05um: 450, ...
```

*BME680 only (alternative):*
```
primary_sensor_type: BME680
air_quality_sensor_type: NULL (BME680 handles both)
temperature: 24.8,  humidity: 57.9
pressure: 1013.2,  gas_resistance: 95000,  iaq: 82.4,  iaq_accuracy: 3
pm1: NULL,  pm25: NULL,  pm10: NULL
```

**Critical Design Note:** The `pm25` column stores PM2.5 (not `pm2_5` or `pm2point5`) for query readability. All PM values use `μg/m³` units.

---

### 3.8 jobs

**Purpose:** Work orders for each car being processed in a pit. Links customer, pit, car, and work type.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | |
| `workshop_id` | INT | FK NOT NULL → workshops | |
| `pit_id` | INT | FK NOT NULL → pits | |
| `customer_user_id` | INT | FK → users | Auto-created customer account |
| `car_model` | VARCHAR(100) | | e.g., "Toyota Fortuner" |
| `car_plate` | VARCHAR(20) | | e.g., "DL01AB1234" |
| `car_color` | VARCHAR(30) | | |
| `car_year` | INT | | |
| `work_type` | VARCHAR(50) | NOT NULL | `Full PPF`, `Partial PPF`, `Ceramic Coating`, `Custom` |
| `work_description` | TEXT | | Detailed work notes |
| `estimated_duration_minutes` | INT | | Estimated job duration |
| `status` | VARCHAR(30) | DEFAULT 'waiting' | `waiting`, `in_progress`, `quality_check`, `completed`, `cancelled` |
| `scheduled_start_time` | TIMESTAMPTZ | | Pre-scheduled start |
| `actual_start_time` | TIMESTAMPTZ | | When work actually began |
| `estimated_end_time` | TIMESTAMPTZ | | Calculated: start + estimated_duration |
| `actual_end_time` | TIMESTAMPTZ | | When job was completed |
| `assigned_staff_ids` | INT[] | | Array of staff user IDs |
| `customer_view_token` | VARCHAR(100) | UNIQUE | Short-lived token for customer portal |
| `customer_view_expires_at` | TIMESTAMPTZ | | Token expiry |
| `owner_notes` | TEXT | | Private notes for owner/staff |
| `staff_notes` | TEXT | | Staff progress notes |
| `quoted_price` | DECIMAL(10,2) | | Job quote in INR |
| `currency` | VARCHAR(3) | DEFAULT 'INR' | |
| `created_by_user_id` | INT | FK → users | Who created the job |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**Status Workflow:**
```
waiting → in_progress → quality_check → completed
        ↘                             ↘
          cancelled                    (any stage can be cancelled)
```

---

### 3.9 job_status_history

**Purpose:** Immutable audit trail of every job status change. Enables time-tracking and dispute resolution.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | |
| `job_id` | INT | FK NOT NULL → jobs | |
| `previous_status` | VARCHAR(30) | | NULL for first transition |
| `new_status` | VARCHAR(30) | NOT NULL | |
| `changed_by_user_id` | INT | FK → users | Who made the change |
| `notes` | TEXT | | Optional reason for change |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | When status changed |

---

### 3.10 alert_configs

**Purpose:** Per-workshop customizable alert thresholds. Allows workshop owners to tune alerts for their environment.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | |
| `workshop_id` | INT | FK NOT NULL UNIQUE → workshops | One config per workshop |
| **Temperature thresholds** | | | |
| `temp_min` | FLOAT | DEFAULT 15.0 | Min safe temperature (°C) |
| `temp_max` | FLOAT | DEFAULT 35.0 | Max safe temperature (°C) |
| **Humidity thresholds** | | | |
| `humidity_max` | FLOAT | DEFAULT 70.0 | Max safe humidity (%) |
| **PM2.5 thresholds (WHO 2021)** | | | |
| `pm25_warning` | FLOAT | DEFAULT 12.0 | Warning level (μg/m³) |
| `pm25_critical` | FLOAT | DEFAULT 35.4 | Critical level (μg/m³) |
| **PM10 thresholds** | | | |
| `pm10_warning` | FLOAT | DEFAULT 54.0 | Warning level (μg/m³) |
| `pm10_critical` | FLOAT | DEFAULT 154.0 | Critical level (μg/m³) |
| **BME680 IAQ thresholds** | | | |
| `iaq_warning` | FLOAT | DEFAULT 100.0 | Warning IAQ level |
| `iaq_critical` | FLOAT | DEFAULT 150.0 | Critical IAQ level |
| **Offline detection** | | | |
| `device_offline_threshold_seconds` | INT | DEFAULT 60 | Seconds before device flagged offline |
| `camera_offline_threshold_seconds` | INT | DEFAULT 30 | Seconds before camera flagged offline |
| **Notification channels** | | | |
| `notify_via_sms` | BOOLEAN | DEFAULT TRUE | Send SMS alerts |
| `notify_via_email` | BOOLEAN | DEFAULT FALSE | Send email alerts |
| `notify_via_webhook` | BOOLEAN | DEFAULT FALSE | POST to webhook URL |
| `webhook_url` | TEXT | | Webhook endpoint |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**Alert Threshold Reference (WHO 2021 Standards):**

| Pollutant | Good | Moderate | Unhealthy | Hazardous |
|-----------|------|----------|-----------|-----------|
| PM2.5 (μg/m³) | 0–12 | 12–35.4 | 35.4–55.4 | >55.4 |
| PM10 (μg/m³) | 0–54 | 54–154 | 154–254 | >254 |
| BME680 IAQ | 0–50 | 51–100 | 101–150 | >150 |

---

### 3.11 alerts

**Purpose:** Log of all triggered alerts. Both auto-generated (from sensor thresholds) and manual.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | |
| `workshop_id` | INT | FK NOT NULL → workshops | |
| `pit_id` | INT | FK → pits | NULL for system-level alerts |
| `device_id` | VARCHAR(50) | FK → devices | NULL for non-device alerts |
| `alert_type` | VARCHAR(50) | NOT NULL | See alert types below |
| `severity` | VARCHAR(20) | NOT NULL | `info`, `warning`, `critical` |
| `message` | TEXT | NOT NULL | Human-readable alert message |
| `trigger_value` | FLOAT | | Actual value that triggered alert |
| `threshold_value` | FLOAT | | Configured threshold exceeded |
| `is_acknowledged` | BOOLEAN | DEFAULT FALSE | Has owner seen this? |
| `acknowledged_by_user_id` | INT | FK → users | |
| `acknowledged_at` | TIMESTAMPTZ | | |
| `resolved_at` | TIMESTAMPTZ | | Auto-set when condition clears |
| `sms_sent` | BOOLEAN | DEFAULT FALSE | SMS notification sent |
| `email_sent` | BOOLEAN | DEFAULT FALSE | Email notification sent |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**Alert Types:**

| alert_type | severity | Trigger |
|------------|----------|---------|
| `high_pm25` | warning/critical | PM2.5 exceeds threshold |
| `high_pm10` | warning/critical | PM10 exceeds threshold |
| `high_iaq` | warning/critical | BME680 IAQ exceeds threshold |
| `temp_too_low` | warning | Temperature below min |
| `temp_too_high` | warning | Temperature above max |
| `humidity_too_high` | warning | Humidity above max |
| `device_offline` | critical | ESP32 not seen for N seconds |
| `camera_offline` | critical | Camera not responding |
| `license_invalid` | critical | Device sending invalid license |
| `subscription_expiring` | info | 7 days before expiry |
| `subscription_suspended` | critical | Kill-switch activated |

---

### 3.12 device_commands

**Purpose:** Log of all commands sent to ESP32 devices (kill-switch, restart, firmware update). Provides audit trail and delivery confirmation.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | |
| `device_id` | VARCHAR(50) | FK NOT NULL → devices | Target device |
| `workshop_id` | INT | FK NOT NULL → workshops | |
| `command` | VARCHAR(50) | NOT NULL | `DISABLE`, `ENABLE`, `RESTART`, `UPDATE_FIRMWARE`, `SET_INTERVAL` |
| `reason` | TEXT | | Why command was sent |
| `payload` | JSONB | | Command parameters |
| `status` | VARCHAR(20) | DEFAULT 'pending' | `pending`, `sent`, `acknowledged`, `failed` |
| `sent_at` | TIMESTAMPTZ | | When MQTT message was published |
| `acknowledged_at` | TIMESTAMPTZ | | When device confirmed receipt |
| `issued_by_user_id` | INT | FK → users | Who triggered the command |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**Example JSONB payloads:**
```json
// DISABLE command
{"reason": "subscription_suspended", "grace_period_seconds": 0}

// SET_INTERVAL command
{"interval_seconds": 30}

// UPDATE_FIRMWARE command
{"firmware_url": "https://...", "version": "1.2.0", "checksum": "sha256:..."}
```

---

### 3.13 audit_logs

**Purpose:** Immutable, append-only audit trail of all state-changing operations. Used for security, compliance, and debugging.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PK | |
| `workshop_id` | INT | FK → workshops | NULL for system-level events |
| `user_id` | INT | FK → users | Who performed the action |
| `action` | VARCHAR(100) | NOT NULL | Dotted notation: `job.created`, `device.disabled` |
| `resource_type` | VARCHAR(50) | | `job`, `device`, `user`, `pit`, `subscription` |
| `resource_id` | INT | | ID of affected resource |
| `old_data` | JSONB | | State before change |
| `new_data` | JSONB | | State after change |
| `ip_address` | VARCHAR(45) | | Request IP address |
| `user_agent` | TEXT | | Browser/device info |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**Action Catalog:**

| Action | Trigger |
|--------|---------|
| `user.login` | Successful login |
| `user.login_failed` | Failed login attempt |
| `user.created` | New user account created |
| `job.created` | New job opened |
| `job.status_changed` | Job status updated |
| `job.completed` | Job marked complete |
| `device.registered` | New device added |
| `device.disabled` | Kill-switch activated |
| `device.enabled` | Device re-activated |
| `subscription.suspended` | Payment overdue |
| `subscription.activated` | Payment received |
| `alert.acknowledged` | Owner acknowledged alert |

---

## 4. INDEXES & PERFORMANCE

```sql
-- sensor_data: primary access patterns
CREATE INDEX idx_sensor_data_pit_time
  ON sensor_data(pit_id, created_at DESC);

CREATE INDEX idx_sensor_data_workshop_time
  ON sensor_data(workshop_id, created_at DESC);

CREATE INDEX idx_sensor_data_device
  ON sensor_data(device_id, created_at DESC);

-- jobs: dashboard queries
CREATE INDEX idx_jobs_workshop_status
  ON jobs(workshop_id, status);

CREATE INDEX idx_jobs_pit_active
  ON jobs(pit_id, created_at DESC)
  WHERE status NOT IN ('completed', 'cancelled');

-- alerts: unacknowledged alerts query
CREATE INDEX idx_alerts_workshop_unack
  ON alerts(workshop_id, created_at DESC)
  WHERE is_acknowledged = FALSE;

-- audit_logs: historical queries
CREATE INDEX idx_audit_logs_workshop
  ON audit_logs(workshop_id, created_at DESC);

CREATE INDEX idx_audit_logs_resource
  ON audit_logs(resource_type, resource_id, created_at DESC);
```

**Future Scaling:** For high-volume sensor data (50+ workshops × 3 pits × 6 readings/min = 900 rows/min), consider migrating `sensor_data` to **TimescaleDB** hypertable — this is a drop-in upgrade for PostgreSQL with no application changes.

---

## 5. SENSOR HARDWARE SUPPORT

### 5.1 DHT22 (Primary - Your Hardware)

- **Protocol:** Single-wire GPIO
- **Readings:** Temperature (±0.5°C), Humidity (±2–5%)
- **Update Rate:** Max 0.5Hz (one reading per 2 seconds)
- **Fields populated:** `temperature`, `humidity`
- **Fields NULL:** `pressure`, `gas_resistance`, `iaq`, `iaq_accuracy`

### 5.2 PMS5003 (Primary - Your Hardware)

- **Protocol:** UART (9600 baud)
- **Readings:** PM1.0, PM2.5, PM10 (μg/m³) + 6 particle size counts
- **Update Rate:** Passive mode, query every 10s
- **Fields populated:** `pm1`, `pm25`, `pm10`, `particles_*`
- **Fields NULL:** `pressure`, `gas_resistance`, `iaq`

### 5.3 BME680 (Alternative Hardware)

- **Protocol:** I2C
- **Readings:** Temperature, Humidity, Pressure, Gas Resistance → IAQ via BSEC
- **Update Rate:** Low-power mode 0.33Hz, normal 1Hz
- **Fields populated:** `temperature`, `humidity`, `pressure`, `gas_resistance`, `iaq`, `iaq_accuracy`
- **Fields NULL:** `pm1`, `pm25`, `pm10`, `particles_*`
- **Note:** BSEC library requires 24–48h calibration for accurate IAQ

### 5.4 Switching Between Sensors

No schema migration needed. Change `devices.primary_sensor_type_id` and `devices.air_quality_sensor_type_id` in the database, and update ESP32 firmware. Historical data retains the sensor type field for accurate historical queries.

---

## 6. DATA RETENTION POLICY

| Table | Retention | Action After Expiry |
|-------|-----------|---------------------|
| `sensor_data` | 90 days (hot) + 1 year (cold) | Move to archive table or TimescaleDB compression |
| `jobs` | Indefinite | Never deleted |
| `alerts` | 180 days | Archive to `alerts_archive` |
| `audit_logs` | 1 year | Archive to cold storage |
| `device_commands` | 90 days | Archive |

**Automated Cleanup Script:** `scripts/maintenance/cleanup_old_data.py` runs nightly via cron.

---

## 7. MIGRATION STRATEGY

All schema changes are managed via numbered SQL migration files in `database/migrations/`.

| File | Description |
|------|-------------|
| `001_initial_schema.sql` | All tables, indexes, constraints |
| `002_seed_sensor_types.sql` | Insert DHT22, PMS5003, BME680 records |
| `003_seed_alert_defaults.sql` | Default alert config template |

**Migration Rules (from claude.md.md):**
1. Never modify production database manually
2. Always create a new migration file for changes
3. Migrations must be reversible (include DOWN script)
4. Test migration on staging before production
5. Take database backup before running migrations
6. Increment schema version in `config/settings.yaml`

---

## 8. SCHEMA CHANGELOG

| Version | Date | Change | Migration File |
|---------|------|--------|---------------|
| v1.0.0 | 2026-02-21 | Initial schema — all 13 tables | 001_initial_schema.sql |
| v1.0.0 | 2026-02-21 | Seed sensor types (DHT22, PMS5003, BME680) | 002_seed_sensor_types.sql |

---

**Document Version:** 1.0
**Last Updated:** 2026-02-21
**Author:** PPF Monitoring System Team
**Next Review:** After Phase 1 deployment
