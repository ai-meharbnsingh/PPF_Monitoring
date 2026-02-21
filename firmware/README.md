# PPF Workshop Monitoring — ESP32 Firmware

Firmware for the **Olimex ESP32-GATEWAY** board that reads air quality
sensors and publishes JSON payloads to an MQTT broker.

---

## Hardware Required

| Component             | Purpose                              | Interface       |
|-----------------------|--------------------------------------|-----------------|
| Olimex ESP32-GATEWAY  | Main controller + Ethernet           | —               |
| DHT22                 | Temperature & Humidity               | GPIO (1-wire)   |
| PMS5003               | PM1.0 / PM2.5 / PM10 dust particles  | UART            |
| BME680 *(optional)*   | Temp / Humidity / Pressure / IAQ     | I2C             |

---

## Wiring Diagrams

### Primary Config: DHT22 + PMS5003

```
Olimex ESP32-GATEWAY                      DHT22
─────────────────────                     ─────────────────
3.3V ──────────────────────────────────── Pin 1 (VCC)
GPIO4 ─────────── 10kΩ pull-up ─────────── Pin 2 (DATA)
(pull-up resistor between VCC and DATA)
GND ───────────────────────────────────── Pin 4 (GND)
                                          (Pin 3 not connected)


Olimex ESP32-GATEWAY                      PMS5003
─────────────────────                     ─────────────────
5V  ───────────────────────────────────── Pin 1 (VCC)   ← Must be 5V!
GND ───────────────────────────────────── Pin 2 (GND)
GPIO32 (Serial2 RX) ───────────────────── Pin 4 (TX)
GPIO33 (Serial2 TX) ───────────────────── Pin 5 (RX)
                                          Pin 3 (SET) → leave open (active HIGH)
                                          Pin 6 (RESET) → leave open
```

> **PMS5003 voltage**: The sensor VCC is 5V but its TX logic level is 3.3V,
> so no level shifter is required for the data line.

---

### Alternative Config: BME680 (Ethernet mode — use GPIO 13/14)

```
Olimex ESP32-GATEWAY                      BME680
─────────────────────                     ─────────────────
3.3V ──────────────────────────────────── VCC
GND ───────────────────────────────────── GND
GPIO13 ─────────────────────────────────── SDA
GPIO14 ─────────────────────────────────── SCL
GND ───────────────────────────────────── SDO   (address = 0x76)
  OR
3.3V ──────────────────────────────────── SDO   (address = 0x77) ← default
                                          CSB → 3.3V (force I2C mode)
```

> When using **WiFi mode** (no Ethernet), use GPIO21 (SDA) and GPIO22 (SCL)
> instead — standard ESP32 I2C pins.

---

## Reserved GPIO — Do NOT Connect Sensors Here

The LAN8720A Ethernet PHY on the Olimex ESP32-GATEWAY occupies:

| GPIO | Ethernet Function | Status         |
|------|-------------------|----------------|
| 17   | ETH_CLK (output)  | ⛔ RESERVED    |
| 18   | ETH_MDIO          | ⛔ RESERVED    |
| 19   | ETH_TXD0          | ⛔ RESERVED    |
| 21   | ETH_TX_EN         | ⛔ RESERVED    |
| 22   | ETH_TXD1          | ⛔ RESERVED    |
| 23   | ETH_MDC           | ⛔ RESERVED    |
| 25   | ETH_RXD0          | ⛔ RESERVED    |
| 26   | ETH_RXD1          | ⛔ RESERVED    |
| 27   | ETH_CRS_DV        | ⛔ RESERVED    |

---

## Project Structure

```
firmware/
├── platformio.ini              ← PlatformIO project config
├── include/
│   └── config.h                ← All user settings (edit before flash)
├── src/
│   ├── main.cpp                ← setup() and loop()
│   ├── sensors/
│   │   ├── dht22.h / .cpp      ← DHT22 driver (retry, validation)
│   │   ├── pms5003.h / .cpp    ← PMS5003 UART frame parser
│   │   └── bme680.h / .cpp     ← BME680 I2C driver (provision)
│   ├── connectivity/
│   │   ├── net_manager.h / .cpp  ← Ethernet / WiFi connection
│   │   └── mqtt_handler.h / .cpp ← PubSubClient wrapper + command handler
│   └── utils/
│       ├── ntp_sync.h / .cpp    ← NTP time sync + ISO 8601 timestamp
│       └── payload_builder.h / .cpp  ← JSON payload assembly
└── README.md                   ← This file
```

---

## Quick Start

### 1. Install PlatformIO

```bash
pip install platformio
# or install the VS Code PlatformIO IDE extension
```

### 2. Edit `include/config.h`

Fill in your values:

```cpp
#define DEVICE_ID       "ESP32-AABBCCDDEEFF"   // From backend admin panel
#define LICENSE_KEY     "LIC-XXXX-YYYY-ZZZZ"   // From backend admin panel
#define WORKSHOP_ID     1
#define PIT_ID          1

#define MQTT_BROKER_HOST  "192.168.1.100"
#define MQTT_USERNAME     "mqtt_user"
#define MQTT_PASSWORD     "mqtt_password"
```

For WiFi mode, also set:
```cpp
#define WIFI_SSID       "YourSSID"
#define WIFI_PASSWORD   "YourPassword"
```

### 3. Select sensor configuration

In `config.h`, uncomment ONE line:
```cpp
#define SENSOR_CONFIG_DHT22_PMS5003   // Default — DHT22 + PMS5003
// #define SENSOR_CONFIG_BME680       // Alternative — BME680 only
```

### 4. Select network environment

In `platformio.ini`, the default environment uses Ethernet:
```ini
[platformio]
default_envs = esp32-gateway-eth    ; ← Ethernet (default)
```

To use WiFi instead:
```ini
default_envs = esp32-wifi
```

### 5. Build and flash

```bash
cd firmware/

# Build for Ethernet (default)
pio run

# Flash
pio run --target upload

# Monitor serial output
pio device monitor --baud 115200
```

---

## MQTT Topics

| Direction | Topic                                              | Purpose                  |
|-----------|----------------------------------------------------|--------------------------|
| Publish   | `workshop/{id}/pit/{id}/sensors`                   | Sensor readings (JSON)   |
| Publish   | `workshop/{id}/device/{device_id}/status`          | Heartbeat + online/LWT   |
| Subscribe | `workshop/{id}/device/{device_id}/command`         | Backend commands         |

---

## Commands (received via MQTT)

The backend can send these commands via the command topic:

```json
{"command": "DISABLE"}
{"command": "ENABLE"}
{"command": "RESTART"}
{"command": "SET_INTERVAL", "payload": {"interval_ms": 30000}}
{"command": "UPDATE_FIRMWARE"}
```

| Command          | Effect                                              |
|------------------|-----------------------------------------------------|
| `DISABLE`        | Stops publishing sensor data (stays connected)      |
| `ENABLE`         | Resumes publishing after DISABLE                    |
| `RESTART`        | Reboots the ESP32 after 2 s delay                  |
| `SET_INTERVAL`   | Changes publish interval (min 5 s, max 1 hour)     |
| `UPDATE_FIRMWARE`| Logged — OTA not implemented in v1                  |

---

## Sensor Payload Examples

### DHT22 + PMS5003

```json
{
  "device_id":       "ESP32-A1B2C3D4E5F6",
  "license_key":     "LIC-XXXX-YYYY-ZZZZ",
  "sensor_type":     "DHT22+PMS5003",
  "temperature":     24.5,
  "humidity":        58.2,
  "pm1":             8.2,
  "pm25":            14.6,
  "pm10":            22.1,
  "particles_03um":  1200,
  "particles_05um":  800,
  "particles_10um":  400,
  "particles_25um":  150,
  "particles_50um":  50,
  "particles_100um": 10,
  "timestamp":       "2026-02-22T10:30:00Z"
}
```

### BME680

```json
{
  "device_id":      "ESP32-A1B2C3D4E5F6",
  "license_key":    "LIC-XXXX-YYYY-ZZZZ",
  "sensor_type":    "BME680",
  "temperature":    24.5,
  "humidity":       58.2,
  "pressure":       1013.2,
  "gas_resistance": 95000,
  "iaq":            82.4,
  "iaq_accuracy":   1,
  "timestamp":      "2026-02-22T10:30:00Z"
}
```

---

## Troubleshooting

| Symptom                          | Likely Cause & Fix                                             |
|----------------------------------|----------------------------------------------------------------|
| `[DHT22] ERROR — All read attempts failed` | Check pull-up resistor (10kΩ VCC→DATA); check GPIO4 wiring |
| `[PMS5003] Timeout waiting for start bytes` | Check TX/RX are not swapped; check 5V supply; wait 30s warmup |
| `[BME680] ERROR — Sensor not found` | Check SDA/SCL pins; check I2C address (SDO → GND=0x76, 3.3V=0x77) |
| `[MQTT] Connection failed — rc=-4` | MQTT broker unreachable; check IP, port, firewall |
| `[MQTT] Connection failed — rc=4` | Wrong MQTT username/password in config.h |
| `[MQTT] Connection failed — rc=5` | Device not authorized; check LICENSE_KEY in backend |
| `[NET] Ethernet not ready within timeout` | Check Ethernet cable; check router DHCP |
| Device not publishing after DISABLE | Normal — send ENABLE command from backend admin panel |
| Timestamp shows `1970-01-01T00:00:00Z` | NTP not synced; check network + NTP_SERVER reachability |

---

## Status LED (GPIO2)

| Pattern                     | Meaning                        |
|-----------------------------|--------------------------------|
| 3 quick blinks at boot      | Setup complete, ready          |
| 1 short blink per publish   | Sensor data published OK       |
| 2 rapid blinks              | Sensor read error              |
| 10 slow blinks then restart | Fatal error (BME680 not found) |
| Off (steady)                | Normal idle between readings   |

---

## Library Dependencies (auto-installed by PlatformIO)

| Library                     | Version | Purpose                     |
|-----------------------------|---------|-----------------------------|
| adafruit/DHT sensor library | ^1.4.6  | DHT22 reading               |
| adafruit/Adafruit Unified Sensor | ^1.1.14 | Sensor abstraction     |
| adafruit/Adafruit BME680 Library | ^2.0.4  | BME680 reading         |
| knolleary/PubSubClient      | ^2.8    | MQTT client                 |
| bblanchon/ArduinoJson       | ^6.21   | JSON serialization          |
| arduino-libraries/NTPClient | ^3.2.1  | NTP time sync               |

---

## Notes

- **IAQ on BME680**: The firmware uses a simplified IAQ estimation from raw
  gas resistance. For calibrated IAQ (iaq_accuracy = 3), integrate the
  Bosch BSEC library (closed-source blob, separate license required).

- **PMS5003 warmup**: The sensor requires ~30 seconds after power-on before
  readings are stable. The driver handles this in `begin()`. Do not cut power
  to the PMS5003 between readings — it can run continuously.

- **DHT22 max read rate**: The sensor has a 0.5 Hz maximum sample rate
  (one reading every 2 seconds). The firmware reads once per
  `REPORT_INTERVAL_MS` (default 10 s), which is well within the limit.

- **Ethernet priority**: For reliable 24/7 operation in a workshop environment,
  use the Ethernet port rather than WiFi. Ethernet is the default build
  environment.
