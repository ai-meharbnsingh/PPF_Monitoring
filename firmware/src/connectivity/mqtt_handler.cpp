/**
 * mqtt_handler.cpp
 * MQTT Handler — Implementation
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 */

#include "mqtt_handler.h"

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
    , _reportIntervalMs(REPORT_INTERVAL_MS)
    , _lastConnectAttemptMs(0)
{
    _topicSensors[0]  = '\0';
    _topicStatus[0]   = '\0';
    _topicCommand[0]  = '\0';
    _globalHandler    = this;
}


// ─── begin() ─────────────────────────────────────────────────────────────────
void MQTTHandler::begin() {
    // Build topics once — format must match backend constants.py EXACTLY
    snprintf(_topicSensors, sizeof(_topicSensors),
             "workshop/%d/pit/%d/sensors", WORKSHOP_ID, PIT_ID);
    snprintf(_topicStatus, sizeof(_topicStatus),
             "workshop/%d/device/%s/status", WORKSHOP_ID, DEVICE_ID);
    snprintf(_topicCommand, sizeof(_topicCommand),
             "workshop/%d/device/%s/command", WORKSHOP_ID, DEVICE_ID);

    DEBUG_PRINTF("[MQTT] Topics:\n");
    DEBUG_PRINTF("[MQTT]   Publish sensors → %s\n", _topicSensors);
    DEBUG_PRINTF("[MQTT]   Publish status  → %s\n", _topicStatus);
    DEBUG_PRINTF("[MQTT]   Subscribe cmd   ← %s\n", _topicCommand);

    _client.setServer(MQTT_BROKER_HOST, MQTT_BROKER_PORT);
    _client.setKeepAlive(MQTT_KEEPALIVE_SEC);
    _client.setCallback(_mqttCallbackBridge);
    // Increase buffer for JSON payloads (default is 256 bytes — too small)
    _client.setBufferSize(512);
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

    // Build LWT (Last Will and Testament) payload
    StaticJsonDocument<128> lwtDoc;
    lwtDoc["device_id"]  = DEVICE_ID;
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
        onlineDoc["device_id"]  = DEVICE_ID;
        onlineDoc["status"]     = "online";
        onlineDoc["fw_version"] = FIRMWARE_VER;
        onlineDoc["ip"]         = "connecting";
        char onlineBuf[128];
        serializeJson(onlineDoc, onlineBuf, sizeof(onlineBuf));
        _client.publish(_topicStatus, onlineBuf, true);

    } else {
        DEBUG_PRINTF("[MQTT] Connection failed — rc=%d\n", _client.state());
        // rc codes: -4=TIMEOUT, -3=CONN_LOST, -2=CONN_FAILED,
        //           -1=DISCONNECTED, 1=BAD_PROTOCOL, 2=ID_REJECTED,
        //           3=UNAVAIL, 4=BAD_CREDENTIALS, 5=UNAUTHORIZED
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


// ─── handleMessage() ─────────────────────────────────────────────────────────
void MQTTHandler::handleMessage(const char* topic,
                                const uint8_t* payload,
                                unsigned int length)
{
    // Guard: only handle our command topic
    if (strcmp(topic, _topicCommand) != 0) return;

    // Copy payload to a null-terminated buffer
    char buf[256];
    if (length >= sizeof(buf)) length = sizeof(buf) - 1;
    memcpy(buf, payload, length);
    buf[length] = '\0';

    DEBUG_PRINTF("[MQTT] Command received ← %s\n", buf);

    // Parse JSON
    StaticJsonDocument<256> doc;
    DeserializationError err = deserializeJson(doc, buf);
    if (err) {
        DEBUG_PRINTF("[MQTT] Bad command JSON: %s\n", err.c_str());
        return;
    }

    const char* command = doc["command"] | "";

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
        DEBUG_PRINTLN("[MQTT] Command: UPDATE_FIRMWARE — OTA not implemented in v1");
        // TODO: implement OTA via ArduinoOTA or HTTPUpdate in a future version
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
    return String("ppf-") + DEVICE_ID + "-" + suffix;
}
