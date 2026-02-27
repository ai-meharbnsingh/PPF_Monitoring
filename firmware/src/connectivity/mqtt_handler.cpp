/**
 * mqtt_handler.cpp
 * MQTT Handler — Implementation
 *
 * Supports both NORMAL and PROVISIONING modes.
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 */

#include "mqtt_handler.h"
#include "ota/ota_manager.h"
#include "utils/device_config.h"

// ─────────────────────────────────────────────────────────────────────────────
// Static callback bridge (PubSubClient requires a plain function)
// ─────────────────────────────────────────────────────────────────────────────
static MQTTHandler* _globalHandler = nullptr;

static void _mqttCallbackBridge(char* topic, byte* payload, unsigned int length) {
    if (_globalHandler) {
        _globalHandler->handleMessage(topic,
                                      reinterpret_cast<const uint8_t*>(payload),
                                      length);
    }
}


// ─── Constructor ──────────────────────────────────────────────────────────────
MQTTHandler::MQTTHandler()
#ifdef USE_ETHERNET
    : _client(_ethClient)
#else
    : _client(_wifiClient)
#endif
    , _disabled(false)
    , _provisioningMode(false)
    , _reportIntervalMs(REPORT_INTERVAL_MS)
    , _lastConnectAttemptMs(0)
{
    _topicSensors[0]      = '\0';
    _topicStatus[0]       = '\0';
    _topicCommand[0]      = '\0';
    _topicProvAnnounce[0] = '\0';
    _topicProvConfig[0]   = '\0';
    _cachedDeviceId[0]    = '\0';
    _globalHandler        = this;
}


// ─── _setupClient() — shared TLS + server + callback config ─────────────────
void MQTTHandler::_setupClient() {
#if MQTT_USE_TLS && !defined(USE_ETHERNET)
    _wifiClient.setInsecure();  // Skip CA verification (accepts any valid TLS cert)
    DEBUG_PRINTLN("[MQTT] TLS enabled (insecure mode — no CA pinning)");
#endif

    _client.setServer(MQTT_BROKER_HOST, MQTT_BROKER_PORT);
    _client.setKeepAlive(MQTT_KEEPALIVE_SEC);
    _client.setCallback(_mqttCallbackBridge);
    _client.setBufferSize(512);
}


// ─── begin() — NORMAL MODE ──────────────────────────────────────────────────
void MQTTHandler::begin(DeviceConfig& config) {
    _provisioningMode = false;

    // Cache device ID
    strncpy(_cachedDeviceId, config.getDeviceId(), sizeof(_cachedDeviceId) - 1);
    _cachedDeviceId[sizeof(_cachedDeviceId) - 1] = '\0';

    // Build topics from NVS config — format must match backend constants.py EXACTLY
    snprintf(_topicSensors, sizeof(_topicSensors),
             "workshop/%d/pit/%d/sensors", config.getWorkshopId(), config.getPitId());
    snprintf(_topicStatus, sizeof(_topicStatus),
             "workshop/%d/device/%s/status", config.getWorkshopId(), config.getDeviceId());
    snprintf(_topicCommand, sizeof(_topicCommand),
             "workshop/%d/device/%s/command", config.getWorkshopId(), config.getDeviceId());

    DEBUG_PRINTLN("[MQTT] Normal mode — topics:");
    DEBUG_PRINTF("[MQTT]   Publish sensors → %s\n", _topicSensors);
    DEBUG_PRINTF("[MQTT]   Publish status  → %s\n", _topicStatus);
    DEBUG_PRINTF("[MQTT]   Subscribe cmd   ← %s\n", _topicCommand);

    _setupClient();
}


// ─── beginProvisioning() — PROVISIONING MODE ────────────────────────────────
void MQTTHandler::beginProvisioning(const char* deviceId) {
    _provisioningMode = true;

    // Cache device ID
    strncpy(_cachedDeviceId, deviceId, sizeof(_cachedDeviceId) - 1);
    _cachedDeviceId[sizeof(_cachedDeviceId) - 1] = '\0';

    // Build provisioning topics
    strncpy(_topicProvAnnounce, "provisioning/announce", sizeof(_topicProvAnnounce));
    snprintf(_topicProvConfig, sizeof(_topicProvConfig),
             "provisioning/%s/config", deviceId);

    DEBUG_PRINTLN("[MQTT] Provisioning mode — topics:");
    DEBUG_PRINTF("[MQTT]   Publish announce → %s\n", _topicProvAnnounce);
    DEBUG_PRINTF("[MQTT]   Subscribe config ← %s\n", _topicProvConfig);

    _setupClient();
}


// ─── ensureConnected() ───────────────────────────────────────────────────────
bool MQTTHandler::ensureConnected() {
    if (_client.connected()) return true;

    uint32_t now = millis();
    if (now - _lastConnectAttemptMs < MQTT_RECONNECT_DELAY_MS) {
        return false;
    }
    _lastConnectAttemptMs = now;

    DEBUG_PRINTF("[MQTT] Connecting to %s:%d…\n",
                 MQTT_BROKER_HOST, MQTT_BROKER_PORT);
    return _connect();
}


// ─── _connect() ──────────────────────────────────────────────────────────────
bool MQTTHandler::_connect() {
    String clientId = _buildClientId();

    if (_provisioningMode) {
        // Provisioning mode — simple connect, no LWT
        bool ok = _client.connect(
            clientId.c_str(),
            MQTT_USERNAME,
            MQTT_PASSWORD
        );

        if (ok) {
            DEBUG_PRINTF("[MQTT] Connected as %s (provisioning)\n", clientId.c_str());
            if (_client.subscribe(_topicProvConfig, MQTT_QOS)) {
                DEBUG_PRINTF("[MQTT] Subscribed to %s\n", _topicProvConfig);
            } else {
                DEBUG_PRINTLN("[MQTT] WARN — Failed to subscribe to provisioning config topic");
            }
        } else {
            DEBUG_PRINTF("[MQTT] Connection failed — rc=%d\n", _client.state());
        }
        return ok;
    }

    // Normal mode — connect with LWT
    StaticJsonDocument<128> lwtDoc;
    lwtDoc["device_id"]  = _cachedDeviceId;
    lwtDoc["status"]     = "offline";
    lwtDoc["fw_version"] = FIRMWARE_VER;
    char lwtBuf[128];
    serializeJson(lwtDoc, lwtBuf, sizeof(lwtBuf));

    bool ok = _client.connect(
        clientId.c_str(),
        MQTT_USERNAME,
        MQTT_PASSWORD,
        _topicStatus,           // LWT topic
        MQTT_QOS,               // LWT QoS
        true,                   // LWT retain
        lwtBuf                  // LWT payload
    );

    if (ok) {
        DEBUG_PRINTF("[MQTT] Connected as %s\n", clientId.c_str());
        // Subscribe to command topic
        if (_client.subscribe(_topicCommand, MQTT_QOS)) {
            DEBUG_PRINTF("[MQTT] Subscribed to %s\n", _topicCommand);
        } else {
            DEBUG_PRINTLN("[MQTT] WARN — Failed to subscribe to command topic");
        }
        // Publish online status immediately
        StaticJsonDocument<128> onlineDoc;
        onlineDoc["device_id"]  = _cachedDeviceId;
        onlineDoc["status"]     = "online";
        onlineDoc["fw_version"] = FIRMWARE_VER;
        onlineDoc["ip"]         = "connecting";
        char onlineBuf[128];
        serializeJson(onlineDoc, onlineBuf, sizeof(onlineBuf));
        _client.publish(_topicStatus, onlineBuf, true);

    } else {
        DEBUG_PRINTF("[MQTT] Connection failed — rc=%d\n", _client.state());
    }
    return ok;
}


// ─── publishSensorData() ─────────────────────────────────────────────────────
bool MQTTHandler::publishSensorData(const char* jsonPayload) {
    if (!_client.connected()) {
        DEBUG_PRINTLN("[MQTT] Cannot publish — not connected");
        return false;
    }
    if (_disabled) {
        DEBUG_PRINTLN("[MQTT] Device DISABLED — skipping publish");
        return false;
    }

    bool ok = _client.publish(_topicSensors, jsonPayload, false);
    if (ok) {
        DEBUG_PRINTF("[MQTT] Published %d bytes to %s\n",
                     strlen(jsonPayload), _topicSensors);
    } else {
        DEBUG_PRINTLN("[MQTT] ERROR — publish failed");
    }
    return ok;
}


// ─── publishStatus() ─────────────────────────────────────────────────────────
bool MQTTHandler::publishStatus(const char* statusJson) {
    if (!_client.connected()) return false;
    bool ok = _client.publish(_topicStatus, statusJson, true);  // retained=true
    if (ok) {
        DEBUG_PRINTF("[MQTT] Status published → %s\n", _topicStatus);
    }
    return ok;
}


// ─── publishAnnounce() — PROVISIONING MODE ──────────────────────────────────
bool MQTTHandler::publishAnnounce(const char* announceJson) {
    if (!_client.connected()) return false;
    bool ok = _client.publish(_topicProvAnnounce, announceJson, false);
    if (ok) {
        DEBUG_PRINTF("[MQTT] Announce published → %s\n", _topicProvAnnounce);
    }
    return ok;
}


// ─── handleMessage() ─────────────────────────────────────────────────────────
void MQTTHandler::handleMessage(const char* topic,
                                const uint8_t* payload,
                                unsigned int length)
{
    // Copy payload to a null-terminated buffer
    char buf[256];
    if (length >= sizeof(buf)) length = sizeof(buf) - 1;
    memcpy(buf, payload, length);
    buf[length] = '\0';

    DEBUG_PRINTF("[MQTT] Message received on %s ← %s\n", topic, buf);

    // Parse JSON
    StaticJsonDocument<256> doc;
    DeserializationError err = deserializeJson(doc, buf);
    if (err) {
        DEBUG_PRINTF("[MQTT] Bad JSON: %s\n", err.c_str());
        return;
    }

    const char* command = doc["command"] | "";

    // ── PROVISION (provisioning mode) ────────────────────────────────────────
    if (strcmp(command, "PROVISION") == 0) {
        const char* licKey = doc["license_key"];
        int wsId  = doc["workshop_id"] | 0;
        int pitId = doc["pit_id"] | 0;
        if (licKey && strlen(licKey) > 0 && wsId > 0) {
            DEBUG_PRINTF("[MQTT] PROVISION: license=%s workshop=%d pit=%d\n", licKey, wsId, pitId);
            deviceConfig.saveLicenseKey(licKey);
            deviceConfig.saveWorkshopId(wsId);
            if (pitId > 0) deviceConfig.savePitId(pitId);
            DEBUG_PRINTLN("[MQTT] Provisioned! Rebooting in 1s…");
            delay(1000);
            ESP.restart();
        } else {
            DEBUG_PRINTLN("[MQTT] PROVISION — missing license_key or workshop_id");
        }
        return;
    }

    // ── ASSIGN (pit/workshop reassignment) ──────────────────────────────────
    if (strcmp(command, "ASSIGN") == 0) {
        int wsId  = doc["workshop_id"] | 0;
        int pitId = doc["pit_id"] | 0;
        if (wsId > 0 && pitId > 0) {
            DEBUG_PRINTF("[MQTT] ASSIGN: workshop=%d pit=%d\n", wsId, pitId);
            deviceConfig.saveWorkshopId(wsId);
            deviceConfig.savePitId(pitId);
            DEBUG_PRINTLN("[MQTT] Reassigned! Rebooting to update topics…");
            delay(1000);
            ESP.restart();
        } else {
            DEBUG_PRINTLN("[MQTT] ASSIGN — missing workshop_id or pit_id");
        }
        return;
    }

    // Normal mode commands — only process if on our command topic
    if (_provisioningMode) return;
    if (strcmp(topic, _topicCommand) != 0) return;

    // ── DISABLE ─────────────────────────────────────────────────────────────
    if (strcmp(command, "DISABLE") == 0) {
        _disabled = true;
        DEBUG_PRINTLN("[MQTT] Command: DISABLE — sensor publishing stopped");
    }

    // ── ENABLE ──────────────────────────────────────────────────────────────
    else if (strcmp(command, "ENABLE") == 0) {
        _disabled = false;
        DEBUG_PRINTLN("[MQTT] Command: ENABLE — sensor publishing resumed");
    }

    // ── RESTART ─────────────────────────────────────────────────────────────
    else if (strcmp(command, "RESTART") == 0) {
        DEBUG_PRINTLN("[MQTT] Command: RESTART — rebooting in 2 s…");
        delay(2000);
        ESP.restart();
    }

    // ── SET_INTERVAL ─────────────────────────────────────────────────────────
    else if (strcmp(command, "SET_INTERVAL") == 0) {
        uint32_t newInterval = doc["payload"]["interval_ms"] | 0;
        if (newInterval >= MIN_INTERVAL_MS && newInterval <= MAX_INTERVAL_MS) {
            _reportIntervalMs = newInterval;
            DEBUG_PRINTF("[MQTT] Command: SET_INTERVAL → %u ms\n", _reportIntervalMs);
        } else {
            DEBUG_PRINTF("[MQTT] SET_INTERVAL rejected: %u ms out of range [%u, %u]\n",
                         newInterval, MIN_INTERVAL_MS, MAX_INTERVAL_MS);
        }
    }

    // ── UPDATE_FIRMWARE ──────────────────────────────────────────────────────
    else if (strcmp(command, "UPDATE_FIRMWARE") == 0) {
        const char* url = doc["url"];
        if (url && strlen(url) > 0) {
            DEBUG_PRINTF("[MQTT] Command: UPDATE_FIRMWARE → %s\n", url);
            if (_otaManager) {
                _otaManager->startRemoteUpdate(url);
            } else {
                DEBUG_PRINTLN("[MQTT] ERROR — OTA manager not attached");
            }
        } else {
            DEBUG_PRINTLN("[MQTT] UPDATE_FIRMWARE missing 'url' field");
        }
    }

    else {
        DEBUG_PRINTF("[MQTT] Unknown command: %s\n", command);
    }
}


// ─── _buildClientId() ────────────────────────────────────────────────────────
String MQTTHandler::_buildClientId() {
    // Unique client ID: "ppf-" + device_id + "-" + last 4 hex of chip ID
    uint64_t chipId = ESP.getEfuseMac();
    char suffix[8];
    snprintf(suffix, sizeof(suffix), "%04X", (uint16_t)(chipId & 0xFFFF));
    return String("ppf-") + _cachedDeviceId + "-" + suffix;
}
