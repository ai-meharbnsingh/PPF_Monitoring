/**
 * ota_manager.h
 * OTA (Over-the-Air) Update Manager — Header
 *
 * Provides three OTA update methods for the ESP32:
 *   A) ArduinoOTA  — PlatformIO LAN upload (pio run -t upload --upload-port <IP>)
 *   B) WebServer   — Browser-based .bin upload at http://<ip>:8080
 *   C) HTTPUpdate  — Remote pull from backend, triggered via MQTT command
 *
 * All methods report status via MQTT to:
 *   workshop/{WORKSHOP_ID}/pit/{PIT_ID}/ota/status
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-25
 */

#pragma once

#include <Arduino.h>
#include <ArduinoOTA.h>
#include <WebServer.h>
#include <Update.h>
#include <HTTPUpdate.h>
#include <PubSubClient.h>
#include "config.h"

class OTAManager {
public:
    OTAManager();

    /**
     * Initialise all OTA methods.
     * Call once from setup(), after WiFi and MQTT are connected.
     * @param mqttClient  Pointer to the PubSubClient for status reporting
     */
    void begin(PubSubClient* mqttClient);

    /**
     * Service ArduinoOTA and WebServer in the main loop.
     * Call from loop() on every iteration.
     */
    void loop();

    /**
     * Start a remote firmware update by pulling .bin from a URL.
     * Typically triggered by MQTT command UPDATE_FIRMWARE.
     * @param url  Full URL to the firmware .bin file
     */
    void startRemoteUpdate(const char* url);

    /** @return true if an OTA update is currently in progress */
    bool isUpdating() const { return _updating; }

private:
    PubSubClient* _mqtt;
    WebServer     _webServer;
    bool          _updating;
    char          _otaStatusTopic[80];

    void _setupArduinoOTA();
    void _setupWebUpload();
    void _publishOtaStatus(const char* state, int progress, const char* version);
    void _handleWebRoot();
    void _handleWebUpdate();
    void _handleWebUpdateUpload();
};
