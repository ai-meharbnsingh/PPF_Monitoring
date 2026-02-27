/**
 * payload_builder.cpp
 * JSON Payload Builder — Implementation
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 */

#include "payload_builder.h"


// ─────────────────────────────────────────────────────────────────────────────
// DHT22 + PMS5003 payload
// ─────────────────────────────────────────────────────────────────────────────
#ifdef SENSOR_CONFIG_DHT22_PMS5003

bool PayloadBuilder::buildDHT22PMS5003(const DHT22Reading&  dht,
                                        const PMS5003Reading& pms,
                                        const char*           timestamp,
                                        char*                 buf,
                                        size_t                len)
{
    // 384 bytes is sufficient for this payload structure
    StaticJsonDocument<384> doc;

    // ── Identity ──────────────────────────────────────────────────────────
    doc["device_id"]   = DEVICE_ID;
    doc["license_key"] = LICENSE_KEY;
    doc["sensor_type"] = "DHT22+PMS5003";

    // ── DHT22 fields ──────────────────────────────────────────────────────
    // Round to 1 decimal place to match sensor precision
    doc["temperature"] = serialized(String(dht.temperature, 1));
    doc["humidity"]    = serialized(String(dht.humidity,    1));

    // ── PMS5003 fields ────────────────────────────────────────────────────
    // PM concentrations as floats (1 decimal) matching backend schema
    doc["pm1"]  = serialized(String((float)pms.pm1,  1));
    doc["pm25"] = serialized(String((float)pms.pm25, 1));
    doc["pm10"] = serialized(String((float)pms.pm10, 1));

    // Particle counts are integers
    doc["particles_03um"]  = pms.particles_03um;
    doc["particles_05um"]  = pms.particles_05um;
    doc["particles_10um"]  = pms.particles_10um;
    doc["particles_25um"]  = pms.particles_25um;
    doc["particles_50um"]  = pms.particles_50um;
    doc["particles_100um"] = pms.particles_100um;

    // ── Timestamp ─────────────────────────────────────────────────────────
    doc["timestamp"] = timestamp;

    size_t written = serializeJson(doc, buf, len);
    if (written == 0 || written >= len) {
        DEBUG_PRINTLN("[PAYLOAD] ERROR — DHT22+PMS5003 serialization failed (buffer too small?)");
        return false;
    }

    DEBUG_PRINTF("[PAYLOAD] DHT22+PMS5003 JSON (%d bytes): %s\n", written, buf);
    return true;
}

#endif  // SENSOR_CONFIG_DHT22_PMS5003


// ─────────────────────────────────────────────────────────────────────────────
// DHT22-only payload (testing — no PMS5003)
// ─────────────────────────────────────────────────────────────────────────────
#ifdef SENSOR_CONFIG_DHT22

bool PayloadBuilder::buildDHT22Only(const DHT22Reading& dht,
                                     const char*         timestamp,
                                     char*               buf,
                                     size_t              len)
{
    StaticJsonDocument<192> doc;

    doc["device_id"]   = DEVICE_ID;
    doc["license_key"] = LICENSE_KEY;
    doc["sensor_type"] = "DHT11";   // Confirmed DHT11 by auto-detect test (5/5 valid, DHT22 0/5)
    doc["temperature"] = serialized(String(dht.temperature, 1));
    doc["humidity"]    = serialized(String(dht.humidity,    1));
    doc["timestamp"]   = timestamp;

    size_t written = serializeJson(doc, buf, len);
    if (written == 0 || written >= len) {
        DEBUG_PRINTLN("[PAYLOAD] ERROR — DHT11Only serialization failed");
        return false;
    }

    DEBUG_PRINTF("[PAYLOAD] DHT11Only JSON (%d bytes): %s\n", written, buf);
    return true;
}

#endif  // SENSOR_CONFIG_DHT22


// ─────────────────────────────────────────────────────────────────────────────
// BME680 payload
// ─────────────────────────────────────────────────────────────────────────────
#ifdef SENSOR_CONFIG_BME680

bool PayloadBuilder::buildBME680(const BME680Reading& bme,
                                  const char*          timestamp,
                                  char*                buf,
                                  size_t               len)
{
    StaticJsonDocument<256> doc;

    // ── Identity ──────────────────────────────────────────────────────────
    doc["device_id"]   = DEVICE_ID;
    doc["license_key"] = LICENSE_KEY;
    doc["sensor_type"] = "BME680";

    // ── BME680 fields ─────────────────────────────────────────────────────
    doc["temperature"]    = serialized(String(bme.temperature,    1));
    doc["humidity"]       = serialized(String(bme.humidity,       1));
    doc["pressure"]       = serialized(String(bme.pressure,       1));
    doc["gas_resistance"] = serialized(String(bme.gas_resistance, 0));  // integer Ω
    doc["iaq"]            = serialized(String(bme.iaq,            1));
    doc["iaq_accuracy"]   = bme.iaq_accuracy;

    // ── Timestamp ─────────────────────────────────────────────────────────
    doc["timestamp"] = timestamp;

    size_t written = serializeJson(doc, buf, len);
    if (written == 0 || written >= len) {
        DEBUG_PRINTLN("[PAYLOAD] ERROR — BME680 serialization failed (buffer too small?)");
        return false;
    }

    DEBUG_PRINTF("[PAYLOAD] BME680 JSON (%d bytes): %s\n", written, buf);
    return true;
}

#endif  // SENSOR_CONFIG_BME680


// ─────────────────────────────────────────────────────────────────────────────
// BME688 primary + DHT11 fallback payload
// ─────────────────────────────────────────────────────────────────────────────
#ifdef SENSOR_CONFIG_BME688_DHT_FALLBACK

bool PayloadBuilder::buildBME688WithFallback(const BME680Reading& bme,
                                              const DHT22Reading&  dht,
                                              bool                 bmeFailed,
                                              const char*          timestamp,
                                              char*                buf,
                                              size_t               len)
{
    StaticJsonDocument<320> doc;

    doc["device_id"]   = DEVICE_ID;
    doc["license_key"] = LICENSE_KEY;
    doc["sensor_type"] = "BME688";

    if (!bmeFailed) {
        // BME688 primary data — full readings
        doc["temperature"]    = serialized(String(bme.temperature,    1));
        doc["humidity"]       = serialized(String(bme.humidity,       1));
        doc["pressure"]       = serialized(String(bme.pressure,       1));
        doc["gas_resistance"] = serialized(String(bme.gas_resistance, 0));
        doc["iaq"]            = serialized(String(bme.iaq,            1));
        doc["iaq_accuracy"]   = bme.iaq_accuracy;
        doc["fallback_active"] = false;
    } else {
        // DHT11 fallback — temp+humidity only
        doc["temperature"]     = serialized(String(dht.temperature, 1));
        doc["humidity"]        = serialized(String(dht.humidity,    1));
        doc["fallback_active"] = true;
    }

    doc["timestamp"] = timestamp;

    size_t written = serializeJson(doc, buf, len);
    if (written == 0 || written >= len) {
        DEBUG_PRINTLN("[PAYLOAD] ERROR — BME688 serialization failed");
        return false;
    }

    DEBUG_PRINTF("[PAYLOAD] BME688 JSON (%d bytes, fallback=%s): %s\n",
                 written, bmeFailed ? "YES" : "NO", buf);
    return true;
}

#endif  // SENSOR_CONFIG_BME688_DHT_FALLBACK


// ─────────────────────────────────────────────────────────────────────────────
// BME688 + PMS5003 payload (full sensor suite)
// ─────────────────────────────────────────────────────────────────────────────
#ifdef SENSOR_CONFIG_BME688_PMS5003

bool PayloadBuilder::buildBME688PMS5003(const BME680Reading&  bme,
                                         const PMS5003Reading& pms,
                                         const char*           timestamp,
                                         char*                 buf,
                                         size_t                len)
{
    // 512 bytes for combined BME688 + PMS5003 payload
    StaticJsonDocument<512> doc;

    // ── Identity ──────────────────────────────────────────────────────────
    doc["device_id"]   = DEVICE_ID;
    doc["license_key"] = LICENSE_KEY;
    doc["sensor_type"] = "BME688+PMS5003";

    // ── BME688 fields (included if valid) ────────────────────────────────
    if (bme.valid) {
        doc["temperature"]    = serialized(String(bme.temperature,    1));
        doc["humidity"]       = serialized(String(bme.humidity,       1));
        doc["pressure"]       = serialized(String(bme.pressure,       1));
        doc["gas_resistance"] = serialized(String(bme.gas_resistance, 0));
        doc["iaq"]            = serialized(String(bme.iaq,            1));
        doc["iaq_accuracy"]   = bme.iaq_accuracy;
    }

    // ── PMS5003 fields (included if valid) ───────────────────────────────
    if (pms.valid) {
        doc["pm1"]  = serialized(String((float)pms.pm1,  1));
        doc["pm25"] = serialized(String((float)pms.pm25, 1));
        doc["pm10"] = serialized(String((float)pms.pm10, 1));

        doc["particles_03um"]  = pms.particles_03um;
        doc["particles_05um"]  = pms.particles_05um;
        doc["particles_10um"]  = pms.particles_10um;
        doc["particles_25um"]  = pms.particles_25um;
        doc["particles_50um"]  = pms.particles_50um;
        doc["particles_100um"] = pms.particles_100um;
    }

    // ── Timestamp ─────────────────────────────────────────────────────────
    doc["timestamp"] = timestamp;

    size_t written = serializeJson(doc, buf, len);
    if (written == 0 || written >= len) {
        DEBUG_PRINTLN("[PAYLOAD] ERROR — BME688+PMS5003 serialization failed (buffer too small?)");
        return false;
    }

    DEBUG_PRINTF("[PAYLOAD] BME688+PMS5003 JSON (%d bytes, bme=%s pms=%s): %s\n",
                 written, bme.valid ? "OK" : "FAIL", pms.valid ? "OK" : "FAIL", buf);
    return true;
}

#endif  // SENSOR_CONFIG_BME688_PMS5003


// ─────────────────────────────────────────────────────────────────────────────
// Status heartbeat payload
// ─────────────────────────────────────────────────────────────────────────────
bool PayloadBuilder::buildStatus(const char* ipAddress,
                                  bool        isDisabled,
                                  uint32_t    intervalMs,
                                  const char* timestamp,
                                  char*       buf,
                                  size_t      len)
{
    StaticJsonDocument<256> doc;

    doc["device_id"]   = DEVICE_ID;
    doc["status"]      = isDisabled ? "disabled" : "online";
    doc["fw_version"]  = FIRMWARE_VER;
    doc["ip"]          = ipAddress;
    doc["uptime_ms"]   = millis();
    doc["heap_free"]   = (uint32_t)ESP.getFreeHeap();
    doc["disabled"]    = isDisabled;
    doc["interval_ms"] = intervalMs;
    doc["timestamp"]   = timestamp;

    size_t written = serializeJson(doc, buf, len);
    if (written == 0 || written >= len) {
        DEBUG_PRINTLN("[PAYLOAD] ERROR — Status serialization failed");
        return false;
    }

    DEBUG_PRINTF("[PAYLOAD] Status JSON (%d bytes)\n", written);
    return true;
}
