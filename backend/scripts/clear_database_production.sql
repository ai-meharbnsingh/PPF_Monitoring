-- ============================================================
-- PRODUCTION DATABASE CLEANUP
-- Run this in Render PostgreSQL Shell
-- Clears ALL data except user accounts
-- ============================================================

-- Connect to database (Render will handle this)
-- \c ppf_monitoring

BEGIN;

-- 1. Delete audit logs
DELETE FROM audit_logs;

-- 2. Delete device commands
DELETE FROM device_commands;

-- 3. Delete alerts
DELETE FROM alerts;

-- 4. Delete pit alert configs
DELETE FROM pit_alert_configs;

-- 5. Delete alert configs
DELETE FROM alert_configs;

-- 6. Delete job status history
DELETE FROM job_status_history;

-- 7. Delete jobs
DELETE FROM jobs;

-- 8. Delete sensor data
DELETE FROM sensor_data;

-- 9. Delete subscriptions
DELETE FROM subscriptions;

-- 10. Delete devices
DELETE FROM devices;

-- 11. Delete pits
DELETE FROM pits;

-- 12. Reset workshops
UPDATE workshops SET 
    total_pits = 0,
    subscription_status = 'trial',
    subscription_expires_at = NULL,
    owner_user_id = NULL,
    updated_at = NOW();

COMMIT;

-- Reset sequences for clean IDs
ALTER SEQUENCE IF EXISTS pits_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS devices_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS jobs_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS sensor_data_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS subscriptions_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS alerts_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS audit_logs_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS job_status_history_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS device_commands_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS pit_alert_configs_id_seq RESTART WITH 1;

-- Verify cleanup
SELECT '=== VERIFICATION ===' as info;
SELECT 'Users' as table_name, COUNT(*) as count FROM users;
SELECT 'Workshops' as table_name, COUNT(*) as count FROM workshops;
SELECT 'Pits' as table_name, COUNT(*) as count FROM pits;
SELECT 'Devices' as table_name, COUNT(*) as count FROM devices;
SELECT 'Sensor Data' as table_name, COUNT(*) as count FROM sensor_data;
SELECT 'Jobs' as table_name, COUNT(*) as count FROM jobs;
SELECT 'Alerts' as table_name, COUNT(*) as count FROM alerts;
SELECT 'Subscriptions' as table_name, COUNT(*) as count FROM subscriptions;
