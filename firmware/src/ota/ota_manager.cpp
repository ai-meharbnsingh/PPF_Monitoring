/**
 * ota_manager.cpp
 * OTA (Over-the-Air) Update Manager — Implementation
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-25
 */

#include "ota_manager.h"
#include <ArduinoJson.h>
#include "utils/device_config.h"

// HTML for the browser upload page (served at http://<ip>:8080)
static const char OTA_UPLOAD_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>PPF ESP32 OTA Update</title>
  <style>
    body { font-family: -apple-system, sans-serif; max-width: 480px; margin: 40px auto; padding: 0 20px; background: #1a1a2e; color: #e0e0e0; }
    h1 { color: #00f0ff; font-size: 1.4em; }
    .info { background: #16213e; padding: 12px; border-radius: 8px; margin: 16px 0; font-size: 0.9em; }
    .info span { color: #00f0ff; }
    form { margin-top: 24px; }
    input[type=file] { display: block; margin: 12px 0; padding: 8px; background: #0f3460; border: 1px solid #00f0ff33; border-radius: 6px; color: #e0e0e0; width: 100%; box-sizing: border-box; }
    input[type=submit] { background: #00f0ff; color: #1a1a2e; border: none; padding: 12px 32px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 1em; }
    input[type=submit]:hover { background: #00d4e6; }
    #progress { display: none; margin-top: 16px; }
    .bar { height: 24px; background: #0f3460; border-radius: 12px; overflow: hidden; }
    .bar-fill { height: 100%; background: #00f0ff; width: 0%; transition: width 0.3s; border-radius: 12px; }
  </style>
</head>
<body>
  <h1>PPF ESP32 — Firmware Update</h1>
  <div class="info">
    <div>Device: <span>%DEVICE_ID%</span></div>
    <div>Current FW: <span>%FW_VERSION%</span></div>
    <div>Free heap: <span>%FREE_HEAP% bytes</span></div>
  </div>
  <form method="POST" action="/update" enctype="multipart/form-data" id="upload-form">
    <input type="file" name="firmware" accept=".bin" required>
    <input type="submit" value="Upload & Flash">
  </form>
  <div id="progress">
    <div class="bar"><div class="bar-fill" id="bar-fill"></div></div>
    <p id="status-text">Uploading...</p>
  </div>
  <script>
    document.getElementById('upload-form').addEventListener('submit', function(e) {
      document.getElementById('progress').style.display = 'block';
      var bar = document.getElementById('bar-fill');
      var status = document.getElementById('status-text');
      var interval = setInterval(function() {
        var w = parseInt(bar.style.width) || 0;
        if (w < 90) bar.style.width = (w + 5) + '%';
      }, 500);
    });
  </script>
</body>
</html>
)rawliteral";


// ─── Constructor ──────────────────────────────────────────────────────────────
OTAManager::OTAManager()
    : _mqtt(nullptr)
    , _webServer(OTA_WEB_PORT)
    , _updating(false)
{
    _otaStatusTopic[0] = '\0';
}


// ─── begin() ──────────────────────────────────────────────────────────────────
void OTAManager::begin(PubSubClient* mqttClient) {
    _mqtt = mqttClient;

    // Build OTA status topic
    snprintf(_otaStatusTopic, sizeof(_otaStatusTopic),
             "workshop/%d/pit/%d/ota/status", deviceConfig.getWorkshopId(), deviceConfig.getPitId());

    DEBUG_PRINTLN("[OTA] Initialising OTA Manager…");
    DEBUG_PRINTF("[OTA]   Status topic → %s\n", _otaStatusTopic);
    DEBUG_PRINTF("[OTA]   Web upload   → http://<ip>:%d\n", OTA_WEB_PORT);

    _setupArduinoOTA();
    _setupWebUpload();

    DEBUG_PRINTLN("[OTA] Ready — ArduinoOTA + Web Upload active");
}


// ─── loop() ───────────────────────────────────────────────────────────────────
void OTAManager::loop() {
    ArduinoOTA.handle();
    _webServer.handleClient();
}


// ─── startRemoteUpdate() ─────────────────────────────────────────────────────
void OTAManager::startRemoteUpdate(const char* url) {
    if (_updating) {
        DEBUG_PRINTLN("[OTA] Update already in progress — ignoring");
        return;
    }

    _updating = true;
    DEBUG_PRINTF("[OTA] Starting remote update from: %s\n", url);
    _publishOtaStatus("downloading", 0, FIRMWARE_VER);

    WiFiClient client;
    httpUpdate.setLedPin(PIN_STATUS_LED, LOW);

    // Follow redirects
    httpUpdate.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);

    t_httpUpdate_return ret = httpUpdate.update(client, url);

    switch (ret) {
        case HTTP_UPDATE_FAILED:
            DEBUG_PRINTF("[OTA] Remote update FAILED: %s (err %d)\n",
                         httpUpdate.getLastErrorString().c_str(),
                         httpUpdate.getLastError());
            _publishOtaStatus("failed", 0, FIRMWARE_VER);
            _updating = false;
            break;

        case HTTP_UPDATE_NO_UPDATES:
            DEBUG_PRINTLN("[OTA] No update available (server returned 304)");
            _publishOtaStatus("no_update", 0, FIRMWARE_VER);
            _updating = false;
            break;

        case HTTP_UPDATE_OK:
            DEBUG_PRINTLN("[OTA] Remote update SUCCESS — rebooting…");
            _publishOtaStatus("success", 100, FIRMWARE_VER);
            delay(1000);
            ESP.restart();
            break;
    }
}


// ─── _setupArduinoOTA() ─────────────────────────────────────────────────────
void OTAManager::_setupArduinoOTA() {
    ArduinoOTA.setHostname(OTA_HOSTNAME);
    ArduinoOTA.setPassword(OTA_PASSWORD);

    ArduinoOTA.onStart([this]() {
        _updating = true;
        String type = (ArduinoOTA.getCommand() == U_FLASH) ? "firmware" : "filesystem";
        DEBUG_PRINTF("[OTA] ArduinoOTA start — type: %s\n", type.c_str());
        _publishOtaStatus("applying", 0, FIRMWARE_VER);
    });

    ArduinoOTA.onEnd([this]() {
        DEBUG_PRINTLN("\n[OTA] ArduinoOTA complete!");
        _publishOtaStatus("success", 100, FIRMWARE_VER);
    });

    ArduinoOTA.onProgress([this](unsigned int progress, unsigned int total) {
        int pct = (progress / (total / 100));
        DEBUG_PRINTF("[OTA] Progress: %d%%\r", pct);
        // Publish every 10%
        if (pct % 10 == 0) {
            _publishOtaStatus("applying", pct, FIRMWARE_VER);
        }
    });

    ArduinoOTA.onError([this](ota_error_t error) {
        DEBUG_PRINTF("[OTA] ArduinoOTA error [%u]: ", error);
        if      (error == OTA_AUTH_ERROR)    DEBUG_PRINTLN("Auth Failed");
        else if (error == OTA_BEGIN_ERROR)   DEBUG_PRINTLN("Begin Failed");
        else if (error == OTA_CONNECT_ERROR) DEBUG_PRINTLN("Connect Failed");
        else if (error == OTA_RECEIVE_ERROR) DEBUG_PRINTLN("Receive Failed");
        else if (error == OTA_END_ERROR)     DEBUG_PRINTLN("End Failed");
        _publishOtaStatus("failed", 0, FIRMWARE_VER);
        _updating = false;
    });

    ArduinoOTA.begin();
    DEBUG_PRINTLN("[OTA] ArduinoOTA initialised");
}


// ─── _setupWebUpload() ─────────────────────────────────────────────────────
void OTAManager::_setupWebUpload() {
    _webServer.on("/", HTTP_GET, [this]() { _handleWebRoot(); });
    _webServer.on("/update", HTTP_POST,
        [this]() { _handleWebUpdate(); },
        [this]() { _handleWebUpdateUpload(); }
    );
    _webServer.begin();
    DEBUG_PRINTF("[OTA] Web upload server on port %d\n", OTA_WEB_PORT);
}


// ─── _handleWebRoot() ──────────────────────────────────────────────────────
void OTAManager::_handleWebRoot() {
    String html = FPSTR(OTA_UPLOAD_HTML);
    html.replace("%DEVICE_ID%", deviceConfig.getDeviceId());
    html.replace("%FW_VERSION%", FIRMWARE_VER);
    html.replace("%FREE_HEAP%", String(ESP.getFreeHeap()));
    _webServer.send(200, "text/html", html);
}


// ─── _handleWebUpdate() — called after upload completes ────────────────────
void OTAManager::_handleWebUpdate() {
    bool success = !Update.hasError();
    String msg = success
        ? "<h1 style='color:#00f0ff'>Update Successful!</h1><p>Rebooting in 3 seconds…</p>"
        : "<h1 style='color:#ff4444'>Update Failed!</h1><p>Check serial output for details.</p>";

    _webServer.sendHeader("Connection", "close");
    _webServer.send(200, "text/html",
        "<html><body style='background:#1a1a2e;color:#e0e0e0;font-family:sans-serif;text-align:center;padding-top:60px'>"
        + msg + "</body></html>");

    if (success) {
        _publishOtaStatus("success", 100, FIRMWARE_VER);
        delay(3000);
        ESP.restart();
    } else {
        _publishOtaStatus("failed", 0, FIRMWARE_VER);
        _updating = false;
    }
}


// ─── _handleWebUpdateUpload() — streaming upload handler ───────────────────
void OTAManager::_handleWebUpdateUpload() {
    HTTPUpload& upload = _webServer.upload();

    if (upload.status == UPLOAD_FILE_START) {
        _updating = true;
        DEBUG_PRINTF("[OTA] Web upload start: %s\n", upload.filename.c_str());
        _publishOtaStatus("applying", 0, FIRMWARE_VER);

        if (!Update.begin(UPDATE_SIZE_UNKNOWN)) {
            DEBUG_PRINTF("[OTA] Update.begin() failed: %s\n",
                         Update.errorString());
            _publishOtaStatus("failed", 0, FIRMWARE_VER);
        }
    }
    else if (upload.status == UPLOAD_FILE_WRITE) {
        if (Update.write(upload.buf, upload.currentSize) != upload.currentSize) {
            DEBUG_PRINTF("[OTA] Update.write() failed: %s\n",
                         Update.errorString());
        }
        // Report progress (approximate — we don't know total size upfront)
        DEBUG_PRINTF("[OTA] Written: %u bytes\r", upload.totalSize + upload.currentSize);
    }
    else if (upload.status == UPLOAD_FILE_END) {
        if (Update.end(true)) {
            DEBUG_PRINTF("\n[OTA] Web upload complete: %u bytes\n", upload.totalSize);
            _publishOtaStatus("success", 100, FIRMWARE_VER);
        } else {
            DEBUG_PRINTF("[OTA] Update.end() failed: %s\n",
                         Update.errorString());
            _publishOtaStatus("failed", 0, FIRMWARE_VER);
        }
    }
}


// ─── _publishOtaStatus() ──────────────────────────────────────────────────
void OTAManager::_publishOtaStatus(const char* state, int progress, const char* version) {
    if (!_mqtt || !_mqtt->connected()) return;

    StaticJsonDocument<200> doc;
    doc["device_id"] = deviceConfig.getDeviceId();
    doc["state"]     = state;
    doc["progress"]  = progress;
    doc["version"]   = version;

    char buf[200];
    serializeJson(doc, buf, sizeof(buf));
    _mqtt->publish(_otaStatusTopic, buf, false);

    DEBUG_PRINTF("[OTA] Status → %s: %s (%d%%)\n", _otaStatusTopic, state, progress);
}
