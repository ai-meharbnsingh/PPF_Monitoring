/**
 * mqtt_handler.h
 * MQTT Handler — Header
 *
 * Manages PubSubClient connection to the Mosquitto broker.
 * Handles:
 *   — Publish sensor readings to:
 *       workshop/{WORKSHOP_ID}/pit/{PIT_ID}/sensors
 *   — Publish device status heartbeats to:
 *       workshop/{WORKSHOP_ID}/device/{DEVICE_ID}/status
 *   — Subscribe to and execute commands from:
 *       workshop/{WORKSHOP_ID}/device/{DEVICE_ID}/command
 *
 * Supported commands (from backend DeviceCommand enum):
 *   DISABLE        — Stop publishing sensor data
 *   ENABLE         — Resume publishing sensor data
 *   RESTART        — Reboot the ESP32
 *   SET_INTERVAL   — Change REPORT_INTERVAL_MS (payload: {"interval_ms": N})
 *   UPDATE_FIRMWARE — Trigger remote OTA via URL (payload: {"url": "http://..."})
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 */

#pragma once

#include <Arduino.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "config.h"

// Forward declaration — avoids circular include
class OTAManager;

#ifdef USE_ETHERNET
  #include <ETH.h>
#else
  #include <WiFi.h>
#endif

#if MQTT_USE_TLS
  #include <WiFiClientSecure.h>
#endif


// ─── MQTT Handler ─────────────────────────────────────────────────────────────
class MQTTHandler {
public:
    MQTTHandler();

    /**
     * Configure the MQTT client with broker settings.
     * Call once from setup(), after network is up.
     */
    void begin();

    /**
     * Ensure MQTT is connected; reconnect if needed.
     * Call at the top of every loop() iteration.
     * @return true if connected and ready to publish
     */
    bool ensureConnected();

    /**
     * Publish a JSON payload string to the sensor topic.
     * @param jsonPayload  Null-terminated JSON string
     * @return true on successful publish
     */
    bool publishSensorData(const char* jsonPayload);

    /**
     * Publish a status heartbeat JSON to the status topic.
     * Called every STATUS_PUBLISH_MS milliseconds.
     */
    bool publishStatus(const char* statusJson);

    /** @return true if device has been remotely disabled via DISABLE command */
    bool isDisabled() const { return _disabled; }

    /** @return current report interval in ms (may be changed by SET_INTERVAL) */
    uint32_t getReportIntervalMs() const { return _reportIntervalMs; }

    /** Process incoming MQTT messages — called internally by callback */
    void handleMessage(const char* topic, const uint8_t* payload, unsigned int length);

    /** Expose underlying client for main loop's client.loop() call */
    PubSubClient& client() { return _client; }

    /** Attach OTA manager for UPDATE_FIRMWARE command handling */
    void setOTAManager(OTAManager* ota) { _otaManager = ota; }

private:
    OTAManager* _otaManager = nullptr;
#ifdef USE_ETHERNET
    WiFiClient      _ethClient;
    PubSubClient    _client;
#else
  #if MQTT_USE_TLS
    WiFiClientSecure _wifiClient;
  #else
    WiFiClient       _wifiClient;
  #endif
    PubSubClient    _client;
#endif

    bool     _disabled;
    uint32_t _reportIntervalMs;
    uint32_t _lastConnectAttemptMs;

    // Pre-built topic strings (computed once in begin())
    char _topicSensors[80];
    char _topicStatus[80];
    char _topicCommand[80];

    /** Attempt one connection + subscribe. Returns true on success. */
    bool _connect();

    /** Build the client ID string */
    static String _buildClientId();
};
