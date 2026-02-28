-- ============================================================
-- Script: Clear all data except user accounts
-- Description: Deletes all devices, sensor data, jobs, alerts, etc.
--              Keeps only: users, workshops, sensor_types (reference data)
-- Usage: psql $DATABASE_URL -f clear_all_data_keep_users.sql
-- ============================================================

BEGIN;

-- Disable foreign key checks temporarily (PostgreSQL uses triggers)
-- We'll delete in proper order to avoid FK violations

-- 1. Delete audit logs (no FK dependencies)
DELETE FROM audit_logs;

-- 2. Delete device commands (references devices, users)
DELETE FROM device_commands;

-- 3. Delete alerts (references workshops, pits, devices, users)
DELETE FROM alerts;

-- 4. Delete pit alert configs (references pits)
DELETE FROM pit_alert_configs;

-- 5. Delete alert configs (references workshops)
DELETE FROM alert_configs;

-- 6. Delete job status history (references jobs, users)
DELETE FROM job_status_history;

-- 7. Delete jobs (references workshops, pits, users)
DELETE FROM jobs;

-- 8. Delete sensor data (references devices, pits, workshops)
DELETE FROM sensor_data;

-- 9. Delete subscriptions (references workshops, devices)
DELETE FROM subscriptions;

-- 10. Delete devices (references pits, workshops, sensor_types)
DELETE FROM devices;

-- 11. Reset pits (remove device associations, camera info)
UPDATE pits SET 
    camera_ip = NULL,
    camera_rtsp_url = NULL,
    camera_model = NULL,
    camera_username = NULL,
    camera_is_online = FALSE,
    camera_last_seen = NULL,
    status = 'active';

-- 12. Reset workshops (clear device counts)
UPDATE workshops SET 
    total_pits = 0,
    subscription_status = 'trial',
    subscription_expires_at = NULL,
    updated_at = NOW();

-- Reset sequences (optional - for clean ID numbering)
-- Uncomment if you want to reset ID counters
-- ALTER SEQUENCE devices_id_seq RESTART WITH 1;
-- ALTER SEQUENCE pits_id_seq RESTART WITH 1;
-- ALTER SEQUENCE jobs_id_seq RESTART WITH 1;
-- ALTER SEQUENCE sensor_data_id_seq RESTART WITH 1;
-- ALTER SEQUENCE subscriptions_id_seq RESTART WITH 1;
-- ALTER SEQUENCE alerts_id_seq RESTART WITH 1;
-- ALTER SEQUENCE audit_logs_id_seq RESTART WITH 1;

COMMIT;

-- Verify what remains
SELECT 'Users remaining:' as info, COUNT(*) as count FROM users;
SELECT 'Workshops remaining:' as info, COUNT(*) as count FROM workshops;
SELECT 'Pits remaining (cleared):' as info, COUNT(*) as count FROM pits;
SELECT 'Devices remaining:' as info, COUNT(*) as count FROM devices;
SELECT 'Sensor data rows:' as info, COUNT(*) as count FROM sensor_data;
SELECT 'Jobs remaining:' as info, COUNT(*) as count FROM jobs;
SELECT 'Alerts remaining:' as info, COUNT(*) as count FROM alerts;
