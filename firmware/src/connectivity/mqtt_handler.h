/**
 * mqtt_handler.h
 * MQTT Handler — Header
 *
 * Manages PubSubClient connection to the MQTT broker.
 * Supports two modes:
 *
 * NORMAL MODE (after provisioning):
 *   — Publish sensor readings to:
 *       workshop/{workshop_id}/pit/{pit_id}/sensors
 *   — Publish device status heartbeats to:
 *       workshop/{workshop_id}/device/{device_id}/status
 *   — Subscribe to and execute commands from:
 *       workshop/{workshop_id}/device/{device_id}/command
 *
 * PROVISIONING MODE (no license key in NVS):
 *   — Publish announcements to:
 *       provisioning/announce
 *   — Subscribe to config delivery on:
 *       provisioning/{device_id}/config
 *
 * Supported commands (from backend DeviceCommand enum):
 *   DISABLE        — Stop publishing sensor data
 *   ENABLE         — Resume publishing sensor data
 *   RESTART        — Reboot the ESP32
 *   SET_INTERVAL   — Change REPORT_INTERVAL_MS (payload: {"interval_ms": N})
 *   UPDATE_FIRMWARE — Trigger remote OTA via URL (payload: {"url": "http://..."})
 *   PROVISION      — Save license key + workshop config to NVS, reboot
 *   ASSIGN         — Update workshop/pit assignment in NVS, reboot
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 */

#pragma once

#include <Arduino.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "config.h"

// Forward declarations
class OTAManager;
class DeviceConfig;

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
     * Configure MQTT for NORMAL operation mode.
     * Builds topics from NVS-stored config (workshop_id, pit_id, device_id).
     * Call once from setup() after network is up and device is provisioned.
     */
    void begin(DeviceConfig& config);

    /**
     * Configure MQTT for PROVISIONING mode.
     * Subscribes to provisioning/{deviceId}/config for config delivery.
     * Call instead of begin() when device has no license key.
     */
    void beginProvisioning(const char* deviceId);

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

    /**
     * Publish a provisioning announcement.
     * Called every PROV_ANNOUNCE_INTERVAL_MS during provisioning mode.
     * @param announceJson  JSON with device_id, mac, firmware_version, ip
     * @return true on successful publish
     */
    bool publishAnnounce(const char* announceJson);

    /** @return true if device has been remotely disabled via DISABLE command */
    bool isDisabled() const { return _disabled; }

    /** @return current report interval in ms (may be changed by SET_INTERVAL) */
    uint32_t getReportIntervalMs() const { return _reportIntervalMs; }

    /** @return true if in provisioning mode (not normal operation) */
    bool isProvisioningMode() const { return _provisioningMode; }

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
    bool     _provisioningMode;
    uint32_t _reportIntervalMs;
    uint32_t _lastConnectAttemptMs;

    // Pre-built topic strings (computed once in begin() or beginProvisioning())
    char _topicSensors[80];
    char _topicStatus[80];
    char _topicCommand[80];

    // Provisioning-mode topics
    char _topicProvAnnounce[40];     // "provisioning/announce"
    char _topicProvConfig[80];       // "provisioning/{device_id}/config"

    // Cached device ID for LWT and client ID
    char _cachedDeviceId[24];

    /** Attempt one connection + subscribe. Returns true on success. */
    bool _connect();

    /** Configure TLS + server + callback (shared between begin modes) */
    void _setupClient();

    /** Build the client ID string */
    String _buildClientId();
};
