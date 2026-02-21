/**
 * main.cpp
 * PPF Workshop Monitoring System — ESP32 Firmware Entry Point
 *
 * Hardware: Olimex ESP32-GATEWAY (ESP32 + LAN8720A Ethernet)
 * Sensors:  DHT22 (temperature + humidity) + PMS5003 (particulate matter)
 *           OR BME680 (temperature + humidity + pressure + IAQ)
 *
 * Flow:
 *   setup():
 *     1. Serial debug output
 *     2. Configure hardware watchdog
 *     3. Initialise sensors
 *     4. Connect to Ethernet / WiFi
 *     5. Sync NTP time
 *     6. Connect to MQTT broker
 *     7. Toggle status LED to signal ready
 *
 *   loop():
 *     1. Feed watchdog
 *     2. Ensure network is up
 *     3. Ensure MQTT is connected; call client.loop()
 *     4. Sync NTP
 *     5. Every REPORT_INTERVAL_MS: read sensors → build JSON → publish
 *     6. Every STATUS_PUBLISH_MS:  build status JSON → publish
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 * Version: 1.0.0
 */

#include <Arduino.h>
#include <esp_task_wdt.h>

#include "config.h"
#include "connectivity/net_manager.h"
#include "connectivity/mqtt_handler.h"
#include "utils/ntp_sync.h"
#include "utils/payload_builder.h"

#ifdef SENSOR_CONFIG_DHT22_PMS5003
  #include "sensors/dht22.h"
  #include "sensors/pms5003.h"
#endif

#ifdef SENSOR_CONFIG_BME680
  #include "sensors/bme680.h"
#endif


// ─────────────────────────────────────────────────────────────────────────────
// Global objects
// ─────────────────────────────────────────────────────────────────────────────
NetManager  net;
MQTTHandler mqtt;
NTPSync     ntp;

#ifdef SENSOR_CONFIG_DHT22_PMS5003
  DHT22Sensor  dhtSensor(PIN_DHT22);
  PMS5003Sensor pmsSensor(PIN_PMS5003_RX, PIN_PMS5003_TX);
#endif

#ifdef SENSOR_CONFIG_BME680
  BME680Sensor bmeSensor(PIN_I2C_SDA, PIN_I2C_SCL, BME680_I2C_ADDR);
#endif

// ─── Timing ───────────────────────────────────────────────────────────────────
static uint32_t _lastSensorPublishMs  = 0;
static uint32_t _lastStatusPublishMs  = 0;

// ─── JSON payload buffers ────────────────────────────────────────────────────
static char _sensorBuf[400];
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
    DEBUG_PRINTF( "║  Device:    %-32s║\n", DEVICE_ID);
    DEBUG_PRINTF( "║  Workshop:  %-32d║\n", WORKSHOP_ID);
    DEBUG_PRINTF( "║  Pit:       %-32d║\n", PIT_ID);
#ifdef SENSOR_CONFIG_DHT22_PMS5003
    DEBUG_PRINTLN("║  Sensors:   DHT22 + PMS5003                  ║");
#endif
#ifdef SENSOR_CONFIG_BME680
    DEBUG_PRINTLN("║  Sensors:   BME680                           ║");
#endif
    DEBUG_PRINTF( "║  Network:   %-32s║\n", NetManager::interfaceType());
    DEBUG_PRINTLN("╚══════════════════════════════════════════════╝");
    DEBUG_PRINTLN();
}


// ─────────────────────────────────────────────────────────────────────────────
// setup()
// ─────────────────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(SERIAL_BAUD);
    delay(500);   // Let Serial settle
    printBanner();

    // ── Status LED ────────────────────────────────────────────────────────
    pinMode(PIN_STATUS_LED, OUTPUT);
    digitalWrite(PIN_STATUS_LED, LOW);

    // ── Watchdog ──────────────────────────────────────────────────────────
    esp_task_wdt_init(WATCHDOG_TIMEOUT_SEC, true);
    esp_task_wdt_add(NULL);
    DEBUG_PRINTF("[WDT] Watchdog armed: %d s\n", WATCHDOG_TIMEOUT_SEC);

    // ── Sensor initialisation ─────────────────────────────────────────────
    DEBUG_PRINTLN("[MAIN] Initialising sensors…");

#ifdef SENSOR_CONFIG_DHT22_PMS5003
    dhtSensor.begin();
    pmsSensor.begin();   // includes 30 s warmup — watchdog is already fed
#endif

#ifdef SENSOR_CONFIG_BME680
    if (!bmeSensor.begin()) {
        DEBUG_PRINTLN("[MAIN] FATAL: BME680 not found. Halting.");
        blinkLed(10, 500);
        ESP.restart();
    }
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

    // ── MQTT ──────────────────────────────────────────────────────────────
    DEBUG_PRINTLN("[MAIN] Starting MQTT…");
    mqtt.begin();
    mqtt.ensureConnected();

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
