-- ============================================================
-- Migration: 002_seed_sensor_types.sql
-- Description: Insert supported sensor hardware types
-- Version: v1.0.0
-- Date: 2026-02-21
-- ============================================================

BEGIN;

INSERT INTO sensor_types (code, name, manufacturer, protocol, capabilities, description)
VALUES
(
    'DHT22',
    'Capacitive Humidity & Temperature Sensor',
    'AOSONG',
    'GPIO',
    '{"temperature": true, "humidity": true, "pressure": false, "pm25": false, "pm10": false, "iaq": false, "gas_resistance": false}',
    'Primary sensor for temperature and humidity. Single-wire protocol. Accuracy: ±0.5°C temp, ±2-5% humidity. Max read rate: 0.5Hz.'
),
(
    'PMS5003',
    'Plantower Particulate Matter Sensor',
    'Plantower',
    'UART',
    '{"temperature": false, "humidity": false, "pressure": false, "pm25": true, "pm10": true, "iaq": false, "gas_resistance": false}',
    'Laser-based air quality sensor. Provides PM1.0, PM2.5, PM10 in μg/m³ plus particle counts by size. Used as air quality sensor alongside DHT22.'
),
(
    'BME680',
    'Bosch Environmental Sensor',
    'Bosch Sensortec',
    'I2C',
    '{"temperature": true, "humidity": true, "pressure": true, "pm25": false, "pm10": false, "iaq": true, "gas_resistance": true}',
    'All-in-one environmental sensor. Provides temperature, humidity, barometric pressure, gas resistance and IAQ index via BSEC library. Alternative to DHT22+PMS5003 combination. Requires 24-48h calibration for accurate IAQ.'
)
ON CONFLICT (code) DO NOTHING;

COMMIT;
