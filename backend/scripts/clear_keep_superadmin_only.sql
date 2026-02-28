-- ============================================================
-- PRODUCTION DATABASE CLEANUP - Keep Only Super Admin
-- Clears ALL data including workshops, keeps only super_admin user
-- ============================================================

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

-- 12. Delete ALL users except super_admin
DELETE FROM users WHERE username != 'super_admin';

-- 13. Delete ALL workshops
DELETE FROM workshops;

COMMIT;

-- Reset sequences for clean IDs
ALTER SEQUENCE IF EXISTS workshops_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS users_id_seq RESTART WITH 1;
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

-- Reset super_admin ID to 1 (optional - cleaner)
-- UPDATE users SET id = 1 WHERE username = 'super_admin';

-- Verify cleanup
SELECT '=== VERIFICATION ===' as info;
SELECT 'Users (should be 1 - super_admin)' as table_name, COUNT(*) as count FROM users;
SELECT 'Workshops (should be 0)' as table_name, COUNT(*) as count FROM workshops;
SELECT 'Pits (should be 0)' as table_name, COUNT(*) as count FROM pits;
SELECT 'Devices (should be 0)' as table_name, COUNT(*) as count FROM devices;
SELECT 'Sensor Data (should be 0)' as table_name, COUNT(*) as count FROM sensor_data;
SELECT 'Jobs (should be 0)' as table_name, COUNT(*) as count FROM jobs;
SELECT 'Alerts (should be 0)' as table_name, COUNT(*) as count FROM alerts;
SELECT 'Subscriptions (should be 0)' as table_name, COUNT(*) as count FROM subscriptions;
