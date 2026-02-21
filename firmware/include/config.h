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
// Uncomment ONE configuration:

#define SENSOR_CONFIG_DHT22_PMS5003   // Primary: DHT22 + PMS5003
// #define SENSOR_CONFIG_BME680       // Alternative: BME680 standalone


// ─── DEVICE IDENTITY (from backend admin panel) ───────────────────────────────
// After registering the device via POST /api/v1/workshops/{id}/devices,
// copy the device_id and license_key here.

#define DEVICE_ID       "ESP32-A1B2C3D4E5F6"   // Replace with your MAC-based ID
#define LICENSE_KEY     "LIC-XXXX-YYYY-ZZZZ"   // Replace with your license key
#define WORKSHOP_ID     1                        // Your workshop ID (integer)
#define PIT_ID          1                        // This device's pit ID (integer)
#define FIRMWARE_VER    "1.0.0"


// ─── NETWORK: WiFi (used when USE_WIFI is set in platformio.ini) ──────────────
#define WIFI_SSID       "YourWiFiSSID"
#define WIFI_PASSWORD   "YourWiFiPassword"
#define WIFI_TIMEOUT_MS 15000                    // 15 seconds


// ─── MQTT BROKER ──────────────────────────────────────────────────────────────
#define MQTT_BROKER_HOST    "192.168.1.100"      // Your MQTT broker IP
#define MQTT_BROKER_PORT    1883
#define MQTT_USERNAME       "mqtt_user"          // Match Mosquitto config
#define MQTT_PASSWORD       "mqtt_password"      // Match Mosquitto config
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
#define PIN_DHT22           4     // DHT22 DATA → GPIO4 (10kΩ pull-up to 3.3V)
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


// ─── DHT22 SETTINGS ───────────────────────────────────────────────────────────
#define DHT_TYPE            DHT22
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
#define WATCHDOG_TIMEOUT_SEC  30   // Reboot if loop stalls this long


// ─── DEBUG SERIAL ─────────────────────────────────────────────────────────────
#define SERIAL_BAUD         115200
#define DEBUG_PRINT(x)      Serial.print(x)
#define DEBUG_PRINTLN(x)    Serial.println(x)
#define DEBUG_PRINTF(...)   Serial.printf(__VA_ARGS__)
