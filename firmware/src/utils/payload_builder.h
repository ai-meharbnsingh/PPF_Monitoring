/**
 * payload_builder.h
 * JSON Payload Builder — Header
 *
 * Builds the exact JSON payloads that the backend's sensor_service.py
 * parse_sensor_payload() function expects.
 *
 * DHT22 + PMS5003 payload:
 * {
 *   "device_id":       "ESP32-A1B2C3D4E5F6",
 *   "license_key":     "LIC-XXXX-YYYY-ZZZZ",
 *   "sensor_type":     "DHT22+PMS5003",
 *   "temperature":     24.5,
 *   "humidity":        58.2,
 *   "pm1":             8.2,
 *   "pm25":            14.6,
 *   "pm10":            22.1,
 *   "particles_03um":  1200,
 *   "particles_05um":  800,
 *   "particles_10um":  400,
 *   "particles_25um":  150,
 *   "particles_50um":  50,
 *   "particles_100um": 10,
 *   "timestamp":       "2026-02-22T10:30:00Z"
 * }
 *
 * BME680 payload:
 * {
 *   "device_id":       "ESP32-A1B2C3D4E5F6",
 *   "license_key":     "LIC-XXXX-YYYY-ZZZZ",
 *   "sensor_type":     "BME680",
 *   "temperature":     24.5,
 *   "humidity":        58.2,
 *   "pressure":        1013.2,
 *   "gas_resistance":  95000,
 *   "iaq":             82.4,
 *   "iaq_accuracy":    3,
 *   "timestamp":       "2026-02-22T10:30:00Z"
 * }
 *
 * Status payload:
 * {
 *   "device_id":    "ESP32-A1B2C3D4E5F6",
 *   "status":       "online",
 *   "fw_version":   "1.0.0",
 *   "ip":           "192.168.1.50",
 *   "uptime_ms":    123456,
 *   "heap_free":    123456,
 *   "disabled":     false,
 *   "interval_ms":  10000,
 *   "timestamp":    "2026-02-22T10:30:00Z"
 * }
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 */

#pragma once

#include <Arduino.h>
#include <ArduinoJson.h>
#include "config.h"

#ifdef SENSOR_CONFIG_DHT22_PMS5003
  #include "sensors/dht22.h"
  #include "sensors/pms5003.h"
#endif

#ifdef SENSOR_CONFIG_BME680
  #include "sensors/bme680.h"
#endif


// ─── Payload Builder ──────────────────────────────────────────────────────────
class PayloadBuilder {
public:
    /**
     * Build DHT22 + PMS5003 JSON sensor payload.
     *
     * @param dht       Valid DHT22Reading (must have .valid == true)
     * @param pms       Valid PMS5003Reading (must have .valid == true)
     * @param timestamp ISO 8601 UTC string — e.g. "2026-02-22T10:30:00Z"
     * @param buf       Output buffer
     * @param len       Buffer size (recommend >= 400 bytes)
     * @return true if serialization succeeded
     */
#ifdef SENSOR_CONFIG_DHT22_PMS5003
    static bool buildDHT22PMS5003(const DHT22Reading&  dht,
                                   const PMS5003Reading& pms,
                                   const char*           timestamp,
                                   char*                 buf,
                                   size_t                len);
#endif

    /**
     * Build BME680 JSON sensor payload.
     *
     * @param bme       Valid BME680Reading (must have .valid == true)
     * @param timestamp ISO 8601 UTC string
     * @param buf       Output buffer
     * @param len       Buffer size (recommend >= 300 bytes)
     * @return true if serialization succeeded
     */
#ifdef SENSOR_CONFIG_BME680
    static bool buildBME680(const BME680Reading& bme,
                             const char*          timestamp,
                             char*                buf,
                             size_t               len);
#endif

    /**
     * Build device status heartbeat JSON.
     *
     * @param ipAddress   Current IP string
     * @param isDisabled  Whether DISABLE command is active
     * @param intervalMs  Current report interval
     * @param timestamp   ISO 8601 UTC string
     * @param buf         Output buffer
     * @param len         Buffer size (recommend >= 256 bytes)
     * @return true if serialization succeeded
     */
    static bool buildStatus(const char* ipAddress,
                             bool        isDisabled,
                             uint32_t    intervalMs,
                             const char* timestamp,
                             char*       buf,
                             size_t      len);
};
