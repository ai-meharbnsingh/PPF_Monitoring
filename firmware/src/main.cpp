/**
 * main.cpp
 * PPF Workshop Monitoring System — ESP32 Firmware Entry Point
 *
 * Hardware: Olimex ESP32-GATEWAY (ESP32 + LAN8720A Ethernet)
 * Sensors:  DHT22 (temperature + humidity) + PMS5003 (particulate matter)
 *           OR BME680 (temperature + humidity + pressure + IAQ)
 *
 * Boot Flow:
 *   1. Initialise hardware (Serial, LED, watchdog, sensors, network, NTP)
 *   2. Load NVS config (device_config)
 *   3. If NOT provisioned → PROVISIONING MODE (announce via MQTT, wait for license)
 *   4. If provisioned → NORMAL MODE (sensor loop, MQTT publish, OTA)
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 * Version: 2.0.0
 */

#include <Arduino.h>
#include <esp_task_wdt.h>

#include "config.h"
#include "connectivity/net_manager.h"
#include "connectivity/mqtt_handler.h"
#include "ota/ota_manager.h"
#include "utils/ntp_sync.h"
#include "utils/payload_builder.h"
#include "utils/device_config.h"

#ifdef SENSOR_CONFIG_DHT22_PMS5003
  #include "sensors/dht22.h"
  #include "sensors/pms5003.h"
#endif

#ifdef SENSOR_CONFIG_DHT22
  #include "sensors/dht22.h"
#endif

#ifdef SENSOR_CONFIG_BME680
  #include "sensors/bme680.h"
#endif

#ifdef SENSOR_CONFIG_BME688_DHT_FALLBACK
  #include "sensors/bme680.h"
  #include "sensors/dht22.h"
#endif

#ifdef SENSOR_CONFIG_BME688_PMS5003
  #include "sensors/bme680.h"
  #include "sensors/pms5003.h"
#endif


// ─────────────────────────────────────────────────────────────────────────────
// Global objects
// ─────────────────────────────────────────────────────────────────────────────
NetManager  net;
MQTTHandler mqtt;
NTPSync     ntp;
OTAManager  ota;

#ifdef SENSOR_CONFIG_DHT22_PMS5003
  DHT22Sensor  dhtSensor(PIN_DHT22);
  PMS5003Sensor pmsSensor(PIN_PMS5003_RX, PIN_PMS5003_TX);
#endif

#ifdef SENSOR_CONFIG_DHT22
  DHT22Sensor dhtSensor(PIN_DHT22);
#endif

#ifdef SENSOR_CONFIG_BME680
  BME680Sensor bmeSensor(PIN_I2C_SDA, PIN_I2C_SCL, BME680_I2C_ADDR);
#endif

#ifdef SENSOR_CONFIG_BME688_DHT_FALLBACK
  BME680Sensor bmeSensor(PIN_I2C_SDA, PIN_I2C_SCL, BME680_I2C_ADDR);
  DHT22Sensor  dhtSensor(PIN_DHT22);
  static bool  _bmeAvailable = false;
#endif

#ifdef SENSOR_CONFIG_BME688_PMS5003
  BME680Sensor  bmeSensor(PIN_I2C_SDA, PIN_I2C_SCL, BME680_I2C_ADDR);
  PMS5003Sensor pmsSensor(PIN_PMS5003_RX, PIN_PMS5003_TX);
#endif

// ─── Timing ───────────────────────────────────────────────────────────────────
static uint32_t _lastSensorPublishMs  = 0;
static uint32_t _lastStatusPublishMs  = 0;

// ─── JSON payload buffers ────────────────────────────────────────────────────
static char _sensorBuf[640];
static char _statusBuf[256];
static char _tsBuf[24];   // "2026-02-22T10:30:00Z\0" = 21 bytes


// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

/** Blink the status LED n times with on/off period of intervalMs each. */
static void blinkLed(uint8_t n, uint32_t intervalMs = 150) {
    for (uint8_t i = 0; i < n; i++) {
        digitalWrite(PIN_STATUS_LED, HIGH);
        delay(intervalMs);
        digitalWrite(PIN_STATUS_LED, LOW);
        delay(intervalMs);
    }
}

/** Print a banner to Serial at startup. */
static void printBanner() {
    DEBUG_PRINTLN();
    DEBUG_PRINTLN("╔══════════════════════════════════════════════╗");
    DEBUG_PRINTLN("║  PPF Workshop Monitoring System              ║");
    DEBUG_PRINTF( "║  Firmware v%-34s║\n", FIRMWARE_VER);
    DEBUG_PRINTLN("╠══════════════════════════════════════════════╣");
    DEBUG_PRINTF( "║  Device:    %-32s║\n", deviceConfig.getDeviceId());
    DEBUG_PRINTF( "║  MAC:       %-32s║\n", deviceConfig.getMacAddress());
    if (deviceConfig.isProvisioned()) {
        DEBUG_PRINTF( "║  Workshop:  %-32d║\n", deviceConfig.getWorkshopId());
        DEBUG_PRINTF( "║  Pit:       %-32d║\n", deviceConfig.getPitId());
    } else {
        DEBUG_PRINTLN("║  Status:    AWAITING PROVISIONING            ║");
    }
#ifdef SENSOR_CONFIG_DHT22_PMS5003
    DEBUG_PRINTLN("║  Sensors:   DHT22 + PMS5003                  ║");
#endif
#ifdef SENSOR_CONFIG_DHT22
    DEBUG_PRINTLN("║  Sensors:   DHT22 only (testing)             ║");
#endif
#ifdef SENSOR_CONFIG_BME680
    DEBUG_PRINTLN("║  Sensors:   BME680                           ║");
#endif
#ifdef SENSOR_CONFIG_BME688_DHT_FALLBACK
    DEBUG_PRINTLN("║  Sensors:   BME688 + DHT11 fallback          ║");
#endif
#ifdef SENSOR_CONFIG_BME688_PMS5003
    DEBUG_PRINTLN("║  Sensors:   BME688 + PMS5003                  ║");
#endif
    DEBUG_PRINTF( "║  Network:   %-32s║\n", NetManager::interfaceType());
    DEBUG_PRINTLN("╚══════════════════════════════════════════════╝");
    DEBUG_PRINTLN();
}


// ─────────────────────────────────────────────────────────────────────────────
// Provisioning Mode
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Enter the provisioning loop. Blocks until admin approves and sends config.
 * The PROVISION command handler in mqtt_handler.cpp saves to NVS and reboots.
 */
static void enterProvisioningLoop() {
    DEBUG_PRINTLN();
    DEBUG_PRINTLN("═══════════════════════════════════════════════");
    DEBUG_PRINTLN("  PROVISIONING MODE — No license key in NVS");
    DEBUG_PRINTLN("  Waiting for admin approval via MQTT…");
    DEBUG_PRINTLN("═══════════════════════════════════════════════");
    DEBUG_PRINTLN();

    // Wait for network and MQTT before starting provisioning loop
    DEBUG_PRINTLN("[PROV] Waiting for network connection…");
    while (!net.ensureConnected()) {
        delay(500);
        esp_task_wdt_reset();
    }
    DEBUG_PRINTLN("[PROV] Network connected.");
    
    // Wait for DHCP to assign IP address
    delay(1000);
    DEBUG_PRINTF("[PROV] IP Address: %s\n", net.getIPAddress().c_str());
    
    mqtt.ensureConnected();

    uint32_t lastAnnounce = 0;
    uint32_t lastLedToggle = 0;
    bool ledState = false;

    // Build the announce payload AFTER network is connected
    StaticJsonDocument<256> doc;
    doc["device_id"]        = deviceConfig.getDeviceId();
    doc["mac"]              = deviceConfig.getMacAddress();
    doc["firmware_version"] = FIRMWARE_VER;
    // Must store String in variable - .c_str() on temporary is dangling!
    String ipStr = net.getIPAddress();
    doc["ip"]               = ipStr.c_str();
    char announceBuf[256];
    serializeJson(doc, announceBuf, sizeof(announceBuf));

    while (true) {
        esp_task_wdt_reset();

        // Ensure network + MQTT
        if (!net.ensureConnected()) { delay(500); continue; }
        mqtt.ensureConnected();
        mqtt.client().loop();

        uint32_t now = millis();

        // Announce periodically
        if (now - lastAnnounce >= PROV_ANNOUNCE_INTERVAL_MS) {
            lastAnnounce = now;
            // Update IP in case it changed (store String to avoid dangling pointer)
            String currentIp = net.getIPAddress();
            doc["ip"] = currentIp.c_str();
            serializeJson(doc, announceBuf, sizeof(announceBuf));
            mqtt.publishAnnounce(announceBuf);
            DEBUG_PRINTF("[PROV] Announced: %s\n", announceBuf);
        }

        // Fast LED blink to indicate provisioning
        if (now - lastLedToggle >= PROV_LED_BLINK_MS) {
            lastLedToggle = now;
            ledState = !ledState;
            digitalWrite(PIN_STATUS_LED, ledState ? HIGH : LOW);
        }

        delay(10);
    }
    // Never reaches here — PROVISION command handler calls ESP.restart()
}


// ─────────────────────────────────────────────────────────────────────────────
// setup()
// ─────────────────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(SERIAL_BAUD);
    delay(500);   // Let Serial settle

    // ── Status LED ────────────────────────────────────────────────────────
    pinMode(PIN_STATUS_LED, OUTPUT);
    digitalWrite(PIN_STATUS_LED, LOW);

    // ── Watchdog ──────────────────────────────────────────────────────────
    esp_task_wdt_init(WATCHDOG_TIMEOUT_SEC, true);
    esp_task_wdt_add(NULL);
    DEBUG_PRINTF("[WDT] Watchdog armed: %d s\n", WATCHDOG_TIMEOUT_SEC);

    // ── Load NVS config + generate device ID from MAC ─────────────────────
    deviceConfig.begin();

    // Print banner (after config loaded so device ID is available)
    printBanner();

    // ── Sensor initialisation ─────────────────────────────────────────────
    DEBUG_PRINTLN("[MAIN] Initialising sensors…");

#ifdef SENSOR_CONFIG_DHT22_PMS5003
    dhtSensor.begin();
    pmsSensor.begin();   // includes 30 s warmup — watchdog is already fed
#endif

#ifdef SENSOR_CONFIG_DHT22
    dhtSensor.begin();   // no PMS5003 warmup — boots in ~2 s
#endif

#ifdef SENSOR_CONFIG_BME680
    if (!bmeSensor.begin()) {
        DEBUG_PRINTLN("[MAIN] FATAL: BME680 not found. Halting.");
        blinkLed(10, 500);
        ESP.restart();
    }
#endif

#ifdef SENSOR_CONFIG_BME688_DHT_FALLBACK
    // Try BME688 first (I2C)
    _bmeAvailable = bmeSensor.begin();
    if (_bmeAvailable) {
        DEBUG_PRINTLN("[MAIN] BME688 initialized — primary sensor OK");
    } else {
        DEBUG_PRINTLN("[MAIN] WARNING — BME688 not found, using DHT11 fallback");
    }
    // Always init DHT11 as fallback
    dhtSensor.begin();
#endif

#ifdef SENSOR_CONFIG_BME688_PMS5003
    if (!bmeSensor.begin()) {
        DEBUG_PRINTLN("[MAIN] WARNING — BME688 not found on I2C");
        blinkLed(5, 300);
    } else {
        DEBUG_PRINTLN("[MAIN] BME688 initialized — I2C OK");
    }
    pmsSensor.begin();   // includes 30 s warmup
#endif

    // ── Network ───────────────────────────────────────────────────────────
    DEBUG_PRINTLN("[MAIN] Starting network…");
    esp_task_wdt_reset();   // feed watchdog before potentially long operations
    net.begin();

    // ── NTP ───────────────────────────────────────────────────────────────
    if (net.isConnected()) {
        DEBUG_PRINTLN("[MAIN] Syncing NTP…");
        ntp.begin();
    } else {
        DEBUG_PRINTLN("[MAIN] WARN — Network not up yet; NTP sync deferred");
    }

    // ═════════════════════════════════════════════════════════════════════════
    // PROVISIONING CHECK — if no license key, enter provisioning mode
    // ═════════════════════════════════════════════════════════════════════════
    if (!deviceConfig.isProvisioned()) {
        mqtt.beginProvisioning(deviceConfig.getDeviceId());
        enterProvisioningLoop();  // Blocks forever until provisioned + reboot
        return;  // Never reached
    }

    // ═════════════════════════════════════════════════════════════════════════
    // NORMAL MODE — device is provisioned
    // ═════════════════════════════════════════════════════════════════════════
    DEBUG_PRINTLN("[MAIN] Starting MQTT (normal mode)…");
    mqtt.begin(deviceConfig);
    mqtt.ensureConnected();

    // ── OTA ────────────────────────────────────────────────────────────────
    DEBUG_PRINTLN("[MAIN] Starting OTA manager…");
    ota.begin(&mqtt.client());
    mqtt.setOTAManager(&ota);

    // ── Ready ─────────────────────────────────────────────────────────────
    blinkLed(3);   // 3 quick blinks = ready
    DEBUG_PRINTLN("[MAIN] Setup complete — entering main loop");
    DEBUG_PRINTLN();
}


// ─────────────────────────────────────────────────────────────────────────────
// loop()
// ─────────────────────────────────────────────────────────────────────────────
void loop() {
    uint32_t now = millis();

    // ── Feed watchdog ─────────────────────────────────────────────────────
    esp_task_wdt_reset();

    // ── Network ───────────────────────────────────────────────────────────
    if (!net.ensureConnected()) {
        delay(500);
        return;   // Nothing to do without network
    }

    // ── NTP update ────────────────────────────────────────────────────────
    ntp.update();

    // ── OTA ──────────────────────────────────────────────────────────────
    // Must run before MQTT check — OTA only needs WiFi, not MQTT.
    ota.loop();             // Service ArduinoOTA + WebServer

    // ── MQTT ─────────────────────────────────────────────────────────────
    // ensureConnected() handles reconnect with back-off
    if (!mqtt.ensureConnected()) {
        delay(500);
        return;
    }
    mqtt.client().loop();   // Process incoming messages (commands)

    // ── Sensor reading & publish ──────────────────────────────────────────
    uint32_t reportInterval = mqtt.getReportIntervalMs();
    if (now - _lastSensorPublishMs >= reportInterval) {
        _lastSensorPublishMs = now;

        // Get timestamp; fall back to placeholder if NTP not synced
        if (!ntp.getTimestamp(_tsBuf, sizeof(_tsBuf))) {
            strncpy(_tsBuf, "1970-01-01T00:00:00Z", sizeof(_tsBuf));
            DEBUG_PRINTLN("[MAIN] WARN — NTP not synced, using epoch placeholder");
        }

#ifdef SENSOR_CONFIG_DHT22_PMS5003

        DHT22Reading  dhtData = dhtSensor.read();
        PMS5003Reading pmsData = pmsSensor.read();

        if (!dhtData.valid || !pmsData.valid) {
            DEBUG_PRINTF("[MAIN] Sensor read failed — DHT22=%s  PMS5003=%s\n",
                         dhtData.valid ? "OK" : "FAIL",
                         pmsData.valid ? "OK" : "FAIL");
            blinkLed(2, 80);   // 2 rapid blinks = sensor error
        } else {
            if (PayloadBuilder::buildDHT22PMS5003(dhtData, pmsData,
                                                   _tsBuf, _sensorBuf,
                                                   sizeof(_sensorBuf))) {
                if (mqtt.publishSensorData(_sensorBuf)) {
                    digitalWrite(PIN_STATUS_LED, HIGH);
                    delay(50);
                    digitalWrite(PIN_STATUS_LED, LOW);
                }
            }
        }

#endif  // SENSOR_CONFIG_DHT22_PMS5003

#ifdef SENSOR_CONFIG_DHT22

        DHT22Reading dhtData = dhtSensor.read();

        if (!dhtData.valid) {
            DEBUG_PRINTLN("[MAIN] DHT22 read failed");
            blinkLed(2, 80);
        } else {
            if (PayloadBuilder::buildDHT22Only(dhtData, _tsBuf,
                                               _sensorBuf, sizeof(_sensorBuf))) {
                if (mqtt.publishSensorData(_sensorBuf)) {
                    digitalWrite(PIN_STATUS_LED, HIGH);
                    delay(50);
                    digitalWrite(PIN_STATUS_LED, LOW);
                }
            }
        }

#endif  // SENSOR_CONFIG_DHT22

#ifdef SENSOR_CONFIG_BME680

        BME680Reading bmeData = bmeSensor.read();

        if (!bmeData.valid) {
            DEBUG_PRINTLN("[MAIN] BME680 read failed");
            blinkLed(2, 80);
        } else {
            if (PayloadBuilder::buildBME680(bmeData, _tsBuf,
                                             _sensorBuf, sizeof(_sensorBuf))) {
                if (mqtt.publishSensorData(_sensorBuf)) {
                    digitalWrite(PIN_STATUS_LED, HIGH);
                    delay(50);
                    digitalWrite(PIN_STATUS_LED, LOW);
                }
            }
        }

#endif  // SENSOR_CONFIG_BME680

#ifdef SENSOR_CONFIG_BME688_PMS5003

        BME680Reading  bmeData = bmeSensor.read();
        PMS5003Reading pmsData = pmsSensor.read();

        if (!bmeData.valid && !pmsData.valid) {
            DEBUG_PRINTLN("[MAIN] Both BME688 and PMS5003 read failed");
            blinkLed(4, 80);
        } else {
            if (PayloadBuilder::buildBME688PMS5003(bmeData, pmsData,
                                                    _tsBuf, _sensorBuf,
                                                    sizeof(_sensorBuf))) {
                if (mqtt.publishSensorData(_sensorBuf)) {
                    digitalWrite(PIN_STATUS_LED, HIGH);
                    delay(50);
                    digitalWrite(PIN_STATUS_LED, LOW);
                }
            }
        }

#endif  // SENSOR_CONFIG_BME688_PMS5003

#ifdef SENSOR_CONFIG_BME688_DHT_FALLBACK

        BME680Reading bmeData = {};
        DHT22Reading  dhtData = {};
        bool bmeFailed = true;

        if (_bmeAvailable) {
            bmeData = bmeSensor.read();
            bmeFailed = !bmeData.valid;
            if (bmeFailed) {
                DEBUG_PRINTLN("[MAIN] BME688 read failed — trying DHT11 fallback");
            }
        }

        if (bmeFailed) {
            dhtData = dhtSensor.read();
            if (!dhtData.valid) {
                DEBUG_PRINTLN("[MAIN] Both BME688 and DHT11 read failed");
                blinkLed(4, 80);   // 4 rapid blinks = both sensors failed
            }
        }

        // Publish if we have any valid data
        bool hasData = (!bmeFailed) || (bmeFailed && dhtData.valid);
        if (hasData) {
            if (PayloadBuilder::buildBME688WithFallback(
                    bmeData, dhtData, bmeFailed,
                    _tsBuf, _sensorBuf, sizeof(_sensorBuf))) {
                if (mqtt.publishSensorData(_sensorBuf)) {
                    digitalWrite(PIN_STATUS_LED, HIGH);
                    delay(50);
                    digitalWrite(PIN_STATUS_LED, LOW);
                }
            }
        }

#endif  // SENSOR_CONFIG_BME688_DHT_FALLBACK
    }


    // ── Status heartbeat ──────────────────────────────────────────────────
    if (now - _lastStatusPublishMs >= STATUS_PUBLISH_MS) {
        _lastStatusPublishMs = now;

        if (!ntp.getTimestamp(_tsBuf, sizeof(_tsBuf))) {
            strncpy(_tsBuf, "1970-01-01T00:00:00Z", sizeof(_tsBuf));
        }

        if (PayloadBuilder::buildStatus(net.getIPAddress().c_str(),
                                         mqtt.isDisabled(),
                                         mqtt.getReportIntervalMs(),
                                         _tsBuf,
                                         _statusBuf,
                                         sizeof(_statusBuf))) {
            mqtt.publishStatus(_statusBuf);
        }
    }

    // Small yield to keep the RTOS scheduler happy
    delay(10);
}
