/**
 * config.h
 * PPF Workshop Monitoring System — ESP32 Firmware Configuration
 *
 * All user-configurable values are here.
 * DO NOT put credentials in any other file.
 *
 * Board: Olimex ESP32-GATEWAY
 * Sensors: DHT22 (temp+humidity) + PMS5003 (dust) [default]
 *          BME680 (all-in-one)                    [alternative]
 *
 * Author: PPF Monitoring Team
 * Created: 2026-02-22
 */

#pragma once

// ─── SENSOR HARDWARE SELECTION ───────────────────────────────────────────────
// Set via platformio.ini build_flags:
//   -DSENSOR_DHT22_ONLY   → DHT22 only (no PMS5003 warmup — use for testing)
//   (default)             → DHT22 + PMS5003 (production kit)
// OR uncomment SENSOR_CONFIG_BME680 below for BME680-based kit.

#ifdef SENSOR_DHT22_ONLY
  #define SENSOR_CONFIG_DHT22         // DHT22 only — no PMS5003, no 30s warmup
#else
  #define SENSOR_CONFIG_DHT22_PMS5003 // Production: DHT22 + PMS5003
#endif
// #define SENSOR_CONFIG_BME680       // Alternative: BME680 standalone


// ─── DEVICE IDENTITY (from backend admin panel) ───────────────────────────────
// After registering the device via POST /api/v1/workshops/{id}/devices,
// copy the device_id and license_key here.

#define DEVICE_ID       "ESP32-083AF2A9F084"     // Real MAC: 08:3A:F2:A9:F0:84
#define LICENSE_KEY     "LIC-1RL0-5S1U-KHNA"    // Registered license key
#define WORKSHOP_ID     15                       // PP Monitoring Workshop
#define PIT_ID          10                       // Main Pit
#define FIRMWARE_VER    "1.0.0"


// ─── NETWORK: WiFi (used when USE_WIFI is set in platformio.ini) ──────────────
// These are the FALLBACK credentials used when no credentials are saved in NVS.
// On first boot (or after wm.resetSettings()), the device opens a captive portal
// instead — connect to the AP below and enter your WiFi password via browser.
#define WIFI_SSID       "Jas_Mehar"              // 2.4GHz WiFi (ESP32 only supports 2.4GHz)
#define WIFI_PASSWORD   "airtel2730"             // WiFi password
#define WIFI_TIMEOUT_MS 15000                    // 15 seconds connect attempt before portal

// ─── CAPTIVE PORTAL (WiFiManager) ─────────────────────────────────────────────
// On first boot (no NVS creds) the ESP32 broadcasts a soft-AP:
//   SSID:     PROV_AP_NAME  (e.g. "PPF-Monitor")
//   Password: PROV_AP_PASSWORD  ("" = open/no password)
// Connect your phone/laptop to that AP → browser opens to 192.168.4.1
// Enter your factory WiFi SSID + password → saved to NVS flash.
// All future boots auto-connect with those saved credentials.
#define PROV_AP_NAME        "PPF-Monitor"    // Portal AP SSID (MAC suffix appended automatically)
#define PROV_AP_PASSWORD    ""               // Leave empty for open portal (no password needed)
#define PROV_TIMEOUT_SEC    120              // Portal auto-closes after 120 s if nobody saves creds


// ─── MQTT BROKER ──────────────────────────────────────────────────────────────
#define MQTT_BROKER_HOST    "192.168.29.16"      // Mac on Jas_Mehar WiFi
#define MQTT_BROKER_PORT    1884                 // socat forwards 1884 → Docker Mosquitto 1883
#define MQTT_USERNAME       "ppf_backend"         // Must match backend .env MQTT_USERNAME
#define MQTT_PASSWORD       "BsW0mmVr5CoDAzW21ibADB7t-kM" // Must match backend .env MQTT_PASSWORD
#define MQTT_KEEPALIVE_SEC  60
#define MQTT_QOS            1
#define MQTT_RECONNECT_DELAY_MS  5000


// ─── MQTT TOPICS (do NOT change — must match backend constants.py) ────────────
// Published by device:
//   workshop/{WORKSHOP_ID}/pit/{PIT_ID}/sensors
//   workshop/{WORKSHOP_ID}/device/{DEVICE_ID}/status
// Subscribed by device:
//   workshop/{WORKSHOP_ID}/device/{DEVICE_ID}/command


// ─── REPORTING ────────────────────────────────────────────────────────────────
#define REPORT_INTERVAL_MS      10000    // 10 seconds between readings
#define STATUS_PUBLISH_MS       30000    // 30 seconds between status heartbeats
#define MIN_INTERVAL_MS         5000     // Minimum allowed interval (safety floor)
#define MAX_INTERVAL_MS         3600000  // Maximum 1 hour


// ─── GPIO PIN ASSIGNMENTS ─────────────────────────────────────────────────────
//
// Olimex ESP32-GATEWAY Ethernet uses (DO NOT touch these):
//   GPIO17: ETH_CLK   GPIO18: ETH_MDIO  GPIO19: ETH_TXD0
//   GPIO21: ETH_TXEN  GPIO22: ETH_TXD1  GPIO23: ETH_MDC
//   GPIO25: ETH_RXD0  GPIO26: ETH_RXD1  GPIO27: ETH_CRSDV
//
// SAFE GPIO for sensors:
#define PIN_DHT22           5     // DHT22 DATA → GPIO5 (testing PCB) — change to 4 on final kit
#define PIN_PMS5003_RX      32    // PMS5003 TX → GPIO32 (ESP32 receives)
#define PIN_PMS5003_TX      33    // PMS5003 RX → GPIO33 (ESP32 transmits)
#define PIN_STATUS_LED      2     // On-board blue LED (GPIO2)

// BME680 I2C — use alternate pins when Ethernet mode (GPIO21/22 reserved)
#if defined(USE_ETHERNET)
  #define PIN_I2C_SDA       13   // BME680 SDA → GPIO13
  #define PIN_I2C_SCL       14   // BME680 SCL → GPIO14
#else
  #define PIN_I2C_SDA       21   // Standard I2C SDA
  #define PIN_I2C_SCL       22   // Standard I2C SCL
#endif


// ─── DHT SETTINGS ─────────────────────────────────────────────────────────────
// Confirmed DHT11 by sensor auto-detect test (GPIO5, 5/5 valid reads)
// DHT22/AM2305B on same pin returned 0/5 — sensor is definitively DHT11
#define DHT_TYPE            DHT11
#define DHT_READ_RETRY      3     // Retry attempts on read failure
#define DHT_READ_DELAY_MS   500   // Delay between retries


// ─── PMS5003 SETTINGS ─────────────────────────────────────────────────────────
#define PMS5003_BAUD        9600
#define PMS5003_WARMUP_MS   30000  // 30s warmup after power-on
#define PMS5003_TIMEOUT_MS  2000   // Timeout waiting for frame


// ─── BME680 SETTINGS ──────────────────────────────────────────────────────────
#define BME680_I2C_ADDR     0x77   // Default address (0x76 if SDO=GND)
#define BME680_TEMP_OFFSET  0.0f   // Calibration offset in °C


// ─── NTP TIME SYNC ────────────────────────────────────────────────────────────
#define NTP_SERVER          "pool.ntp.org"
#define NTP_OFFSET_SEC      19800   // IST = UTC+5:30 = 19800 seconds
#define NTP_UPDATE_MS       3600000 // Re-sync every 1 hour


// ─── WATCHDOG ─────────────────────────────────────────────────────────────────
#define WATCHDOG_TIMEOUT_SEC  90   // Must be > PMS5003_WARMUP_MS/1000 (30s) + Ethernet DHCP + MQTT connect
                                   // 30s warmup + ~15s DHCP + ~5s MQTT = ~50s worst case → 90s is safe


// ─── DEBUG SERIAL ─────────────────────────────────────────────────────────────
#define SERIAL_BAUD         115200
// Guard against redefinition: DHT.h also defines DEBUG_PRINT / DEBUG_PRINTLN
#ifndef DEBUG_PRINT
  #define DEBUG_PRINT(x)    Serial.print(x)
#endif
#ifndef DEBUG_PRINTLN
  #define DEBUG_PRINTLN(x)  Serial.println(x)
#endif
#ifndef DEBUG_PRINTF
  #define DEBUG_PRINTF(...) Serial.printf(__VA_ARGS__)
#endif
