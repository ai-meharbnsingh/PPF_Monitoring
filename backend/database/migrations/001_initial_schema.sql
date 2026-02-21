-- ============================================================
-- Migration: 001_initial_schema.sql
-- Description: Create all tables for PPF Workshop Monitoring System
-- Version: v1.0.0
-- Date: 2026-02-21
-- Author: PPF Monitoring Team
-- ============================================================

-- Run with: psql -U ppf_user -d ppf_monitoring -f 001_initial_schema.sql

BEGIN;

-- ============================================================
-- SENSOR TYPES (reference table)
-- ============================================================
CREATE TABLE IF NOT EXISTS sensor_types (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(20) UNIQUE NOT NULL,
    name        VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(50),
    protocol    VARCHAR(20),
    capabilities JSONB,
    description TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE
);

-- ============================================================
-- WORKSHOPS (top-level tenant)
-- ============================================================
CREATE TABLE IF NOT EXISTS workshops (
    id                      SERIAL PRIMARY KEY,
    name                    VARCHAR(100) NOT NULL,
    slug                    VARCHAR(50) UNIQUE NOT NULL,
    owner_user_id           INTEGER,                        -- FK added after users table
    address                 TEXT,
    city                    VARCHAR(50),
    state                   VARCHAR(50),
    phone                   VARCHAR(20),
    email                   VARCHAR(100),
    total_pits              INTEGER NOT NULL DEFAULT 0,
    subscription_plan       VARCHAR(20) NOT NULL DEFAULT 'trial',
    subscription_status     VARCHAR(20) NOT NULL DEFAULT 'trial',
    subscription_expires_at TIMESTAMPTZ,
    timezone                VARCHAR(50) NOT NULL DEFAULT 'Asia/Kolkata',
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- USERS
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id                      SERIAL PRIMARY KEY,
    workshop_id             INTEGER REFERENCES workshops(id),
    username                VARCHAR(50) UNIQUE NOT NULL,
    email                   VARCHAR(100) UNIQUE,
    phone                   VARCHAR(20),
    password_hash           VARCHAR(255) NOT NULL,
    role                    VARCHAR(20) NOT NULL CHECK (role IN ('super_admin', 'owner', 'staff', 'customer')),
    first_name              VARCHAR(50),
    last_name               VARCHAR(50),
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    is_temporary_password   BOOLEAN NOT NULL DEFAULT FALSE,
    last_login              TIMESTAMPTZ,
    login_attempt_count     INTEGER NOT NULL DEFAULT 0,
    locked_until            TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add FK from workshops to users (deferred to after users created)
ALTER TABLE workshops
    ADD CONSTRAINT fk_workshop_owner
    FOREIGN KEY (owner_user_id) REFERENCES users(id);

-- ============================================================
-- PITS
-- ============================================================
CREATE TABLE IF NOT EXISTS pits (
    id                  SERIAL PRIMARY KEY,
    workshop_id         INTEGER NOT NULL REFERENCES workshops(id),
    pit_number          INTEGER NOT NULL,
    name                VARCHAR(50),
    description         TEXT,
    status              VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'disabled', 'maintenance')),
    camera_ip           VARCHAR(50),
    camera_rtsp_url     TEXT,
    camera_model        VARCHAR(100),
    camera_username     VARCHAR(50),
    camera_is_online    BOOLEAN NOT NULL DEFAULT FALSE,
    camera_last_seen    TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (workshop_id, pit_number)
);

-- ============================================================
-- DEVICES (ESP32 Gateway units)
-- ============================================================
CREATE TABLE IF NOT EXISTS devices (
    id                          SERIAL PRIMARY KEY,
    pit_id                      INTEGER REFERENCES pits(id),
    workshop_id                 INTEGER NOT NULL REFERENCES workshops(id),
    device_id                   VARCHAR(50) UNIQUE NOT NULL,
    license_key                 VARCHAR(30) UNIQUE NOT NULL,
    firmware_version            VARCHAR(20),
    primary_sensor_type_id      INTEGER REFERENCES sensor_types(id),
    air_quality_sensor_type_id  INTEGER REFERENCES sensor_types(id),
    ip_address                  VARCHAR(50),
    mac_address                 VARCHAR(17),
    status                      VARCHAR(20) NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active', 'disabled', 'suspended', 'maintenance')),
    is_online                   BOOLEAN NOT NULL DEFAULT FALSE,
    last_seen                   TIMESTAMPTZ,
    last_mqtt_message           TIMESTAMPTZ,
    report_interval_seconds     INTEGER NOT NULL DEFAULT 10,
    notes                       TEXT,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- SUBSCRIPTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id                  SERIAL PRIMARY KEY,
    workshop_id         INTEGER NOT NULL REFERENCES workshops(id),
    device_id           VARCHAR(50) REFERENCES devices(device_id),
    license_key         VARCHAR(30) UNIQUE NOT NULL,
    plan                VARCHAR(20) NOT NULL DEFAULT 'basic'
                        CHECK (plan IN ('trial', 'basic', 'standard', 'premium')),
    status              VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'suspended', 'expired', 'cancelled')),
    monthly_fee         DECIMAL(10,2),
    currency            VARCHAR(3) NOT NULL DEFAULT 'INR',
    starts_at           TIMESTAMPTZ DEFAULT NOW(),
    expires_at          TIMESTAMPTZ,
    trial_expires_at    TIMESTAMPTZ,
    grace_period_days   INTEGER NOT NULL DEFAULT 7,
    last_payment_date   TIMESTAMPTZ,
    next_payment_date   TIMESTAMPTZ,
    payment_method      VARCHAR(50),
    payment_reference   VARCHAR(100),
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- SENSOR DATA (time-series)
-- Supports DHT22+PMS5003 (primary) AND BME680 (alternative)
-- ============================================================
CREATE TABLE IF NOT EXISTS sensor_data (
    id                          BIGSERIAL PRIMARY KEY,
    device_id                   VARCHAR(50) NOT NULL REFERENCES devices(device_id),
    pit_id                      INTEGER NOT NULL REFERENCES pits(id),
    workshop_id                 INTEGER NOT NULL REFERENCES workshops(id),

    -- Sensor type context
    primary_sensor_type         VARCHAR(10),          -- 'DHT22' | 'BME680'
    air_quality_sensor_type     VARCHAR(10),          -- 'PMS5003' | 'BME680' | NULL

    -- DHT22 / BME680 shared
    temperature                 FLOAT,                -- Celsius
    humidity                    FLOAT,                -- %

    -- BME680 specific (NULL for DHT22)
    pressure                    FLOAT,                -- hPa
    gas_resistance              FLOAT,                -- Ohms
    iaq                         FLOAT,                -- IAQ 0-500 (BSEC)
    iaq_accuracy                INTEGER,              -- BSEC accuracy 0-3

    -- PMS5003 specific (NULL for BME680-only)
    pm1                         FLOAT,                -- PM1.0 μg/m³
    pm25                        FLOAT,                -- PM2.5 μg/m³
    pm10                        FLOAT,                -- PM10 μg/m³

    -- PMS5003 particle counts (optional)
    particles_03um              INTEGER,              -- >0.3μm per 0.1L
    particles_05um              INTEGER,
    particles_10um              INTEGER,
    particles_25um              INTEGER,
    particles_50um              INTEGER,
    particles_100um             INTEGER,

    -- Data quality
    is_valid                    BOOLEAN NOT NULL DEFAULT TRUE,
    validation_notes            TEXT,

    -- Timestamps
    device_timestamp            TIMESTAMPTZ,          -- From ESP32 clock
    created_at                  TIMESTAMPTZ NOT NULL  -- Server ingestion time
);

-- Indexes for common query patterns
CREATE INDEX idx_sensor_data_pit_time       ON sensor_data(pit_id, created_at DESC);
CREATE INDEX idx_sensor_data_workshop_time  ON sensor_data(workshop_id, created_at DESC);
CREATE INDEX idx_sensor_data_device         ON sensor_data(device_id, created_at DESC);

-- ============================================================
-- JOBS
-- ============================================================
CREATE TABLE IF NOT EXISTS jobs (
    id                          SERIAL PRIMARY KEY,
    workshop_id                 INTEGER NOT NULL REFERENCES workshops(id),
    pit_id                      INTEGER NOT NULL REFERENCES pits(id),
    customer_user_id            INTEGER REFERENCES users(id),
    car_model                   VARCHAR(100),
    car_plate                   VARCHAR(20),
    car_color                   VARCHAR(30),
    car_year                    INTEGER,
    work_type                   VARCHAR(50) NOT NULL,
    work_description            TEXT,
    estimated_duration_minutes  INTEGER,
    status                      VARCHAR(30) NOT NULL DEFAULT 'waiting'
                                CHECK (status IN ('waiting', 'in_progress', 'quality_check', 'completed', 'cancelled')),
    scheduled_start_time        TIMESTAMPTZ,
    actual_start_time           TIMESTAMPTZ,
    estimated_end_time          TIMESTAMPTZ,
    actual_end_time             TIMESTAMPTZ,
    assigned_staff_ids          INTEGER[],
    customer_view_token         VARCHAR(100) UNIQUE,
    customer_view_expires_at    TIMESTAMPTZ,
    owner_notes                 TEXT,
    staff_notes                 TEXT,
    quoted_price                DECIMAL(10,2),
    currency                    VARCHAR(3) NOT NULL DEFAULT 'INR',
    created_by_user_id          INTEGER REFERENCES users(id),
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_jobs_workshop_status ON jobs(workshop_id, status);
CREATE INDEX idx_jobs_pit_active ON jobs(pit_id, created_at DESC)
    WHERE status NOT IN ('completed', 'cancelled');

-- ============================================================
-- JOB STATUS HISTORY
-- ============================================================
CREATE TABLE IF NOT EXISTS job_status_history (
    id                      SERIAL PRIMARY KEY,
    job_id                  INTEGER NOT NULL REFERENCES jobs(id),
    previous_status         VARCHAR(30),
    new_status              VARCHAR(30) NOT NULL,
    changed_by_user_id      INTEGER REFERENCES users(id),
    notes                   TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- ALERT CONFIGS (per-workshop threshold settings)
-- ============================================================
CREATE TABLE IF NOT EXISTS alert_configs (
    id                                  SERIAL PRIMARY KEY,
    workshop_id                         INTEGER NOT NULL UNIQUE REFERENCES workshops(id),
    temp_min                            FLOAT NOT NULL DEFAULT 15.0,
    temp_max                            FLOAT NOT NULL DEFAULT 35.0,
    humidity_max                        FLOAT NOT NULL DEFAULT 70.0,
    pm25_warning                        FLOAT NOT NULL DEFAULT 12.0,
    pm25_critical                       FLOAT NOT NULL DEFAULT 35.4,
    pm10_warning                        FLOAT NOT NULL DEFAULT 54.0,
    pm10_critical                       FLOAT NOT NULL DEFAULT 154.0,
    iaq_warning                         FLOAT NOT NULL DEFAULT 100.0,
    iaq_critical                        FLOAT NOT NULL DEFAULT 150.0,
    device_offline_threshold_seconds    INTEGER NOT NULL DEFAULT 60,
    camera_offline_threshold_seconds    INTEGER NOT NULL DEFAULT 30,
    notify_via_sms                      BOOLEAN NOT NULL DEFAULT TRUE,
    notify_via_email                    BOOLEAN NOT NULL DEFAULT FALSE,
    notify_via_webhook                  BOOLEAN NOT NULL DEFAULT FALSE,
    webhook_url                         TEXT,
    created_at                          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- ALERTS
-- ============================================================
CREATE TABLE IF NOT EXISTS alerts (
    id                          SERIAL PRIMARY KEY,
    workshop_id                 INTEGER NOT NULL REFERENCES workshops(id),
    pit_id                      INTEGER REFERENCES pits(id),
    device_id                   VARCHAR(50) REFERENCES devices(device_id),
    alert_type                  VARCHAR(50) NOT NULL,
    severity                    VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    message                     TEXT NOT NULL,
    trigger_value               FLOAT,
    threshold_value             FLOAT,
    is_acknowledged             BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_by_user_id     INTEGER REFERENCES users(id),
    acknowledged_at             TIMESTAMPTZ,
    resolved_at                 TIMESTAMPTZ,
    sms_sent                    BOOLEAN NOT NULL DEFAULT FALSE,
    email_sent                  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                  TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_alerts_workshop ON alerts(workshop_id, created_at DESC);
CREATE INDEX idx_alerts_unack ON alerts(workshop_id, created_at DESC)
    WHERE is_acknowledged = FALSE;

-- ============================================================
-- DEVICE COMMANDS (kill-switch log)
-- ============================================================
CREATE TABLE IF NOT EXISTS device_commands (
    id                  SERIAL PRIMARY KEY,
    device_id           VARCHAR(50) NOT NULL REFERENCES devices(device_id),
    workshop_id         INTEGER NOT NULL REFERENCES workshops(id),
    command             VARCHAR(50) NOT NULL,
    reason              TEXT,
    payload             JSONB,
    status              VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'sent', 'acknowledged', 'failed')),
    sent_at             TIMESTAMPTZ,
    acknowledged_at     TIMESTAMPTZ,
    issued_by_user_id   INTEGER REFERENCES users(id),
    created_at          TIMESTAMPTZ NOT NULL
);

-- ============================================================
-- AUDIT LOGS (append-only)
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id              BIGSERIAL PRIMARY KEY,
    workshop_id     INTEGER REFERENCES workshops(id),
    user_id         INTEGER REFERENCES users(id),
    action          VARCHAR(100) NOT NULL,
    resource_type   VARCHAR(50),
    resource_id     INTEGER,
    old_data        JSONB,
    new_data        JSONB,
    ip_address      VARCHAR(45),
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_audit_logs_workshop ON audit_logs(workshop_id, created_at DESC);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id, created_at DESC);

COMMIT;

-- ============================================================
-- DOWN SCRIPT (for rollback)
-- Run: psql ... -f 001_initial_schema_down.sql
-- ============================================================
-- DROP TABLE IF EXISTS audit_logs CASCADE;
-- DROP TABLE IF EXISTS device_commands CASCADE;
-- DROP TABLE IF EXISTS alerts CASCADE;
-- DROP TABLE IF EXISTS alert_configs CASCADE;
-- DROP TABLE IF EXISTS job_status_history CASCADE;
-- DROP TABLE IF EXISTS jobs CASCADE;
-- DROP TABLE IF EXISTS sensor_data CASCADE;
-- DROP TABLE IF EXISTS subscriptions CASCADE;
-- DROP TABLE IF EXISTS devices CASCADE;
-- DROP TABLE IF EXISTS pits CASCADE;
-- ALTER TABLE workshops DROP CONSTRAINT IF EXISTS fk_workshop_owner;
-- DROP TABLE IF EXISTS users CASCADE;
-- DROP TABLE IF EXISTS workshops CASCADE;
-- DROP TABLE IF EXISTS sensor_types CASCADE;
