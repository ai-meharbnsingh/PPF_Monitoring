# Hardware Setup Guide — PPF Workshop Monitoring System

This guide covers wiring the sensors to the Olimex ESP32-GATEWAY board and flashing the firmware using PlatformIO.

---

## Hardware Requirements

| Component | Model | Purpose |
|-----------|-------|---------|
| Microcontroller | **Olimex ESP32-GATEWAY** | Main board — Ethernet + WiFi capable |
| Temperature/Humidity | **DHT22 (AM2302)** | Primary sensor — ±0.5°C / ±2-5% RH |
| Air Quality (optional) | **PMS5003** (Plantower) | PM1.0 / PM2.5 / PM10 particle count |
| Power | 5V DC 1A adapter | via USB or screw terminal |
| Network | RJ45 Ethernet cable | LAN connection to router |

---

## Wiring Diagram

### DHT22 → ESP32-GATEWAY

```
DHT22 Pin  │  ESP32-GATEWAY Pin
───────────┼──────────────────
VCC (+)    │  3.3V
DATA       │  GPIO 4  (+ 10kΩ pull-up resistor to 3.3V)
NC         │  (not connected)
GND (-)    │  GND
```

> **Important:** Always use a 10kΩ pull-up resistor between DATA and 3.3V.
> Without it, the DHT22 will produce intermittent read errors.

### PMS5003 → ESP32-GATEWAY (optional)

```
PMS5003 Pin  │  ESP32-GATEWAY Pin
─────────────┼──────────────────
VCC (5V)     │  5V (use external 5V supply — ESP32 3.3V is insufficient)
GND          │  GND
TX           │  GPIO 32  (ESP32 RX — receives PM data)
RX           │  GPIO 33  (ESP32 TX — sends wake/sleep commands)
SET          │  3.3V     (always ON mode)
RESET        │  3.3V     (not reset)
```

> **Note:** PMS5003 needs 5V input but its TX is 3.3V-compatible.
> Do NOT connect PMS5003 VCC to ESP32's 3.3V pin.

### Olimex ESP32-GATEWAY Reserved Pins (DO NOT USE)

The Ethernet controller (LAN8720A) uses these pins internally:

| GPIO | Function |
|------|----------|
| 17 | ETH_CLK |
| 18 | ETH_MDIO |
| 19 | ETH_TXD0 |
| 21 | ETH_TXEN |
| 22 | ETH_TXD1 |
| 23 | ETH_MDC |
| 25 | ETH_RXD0 |
| 26 | ETH_RXD1 |
| 27 | ETH_CRSDV |

---

## Firmware Configuration

### Step 1: Install PlatformIO

```bash
# Via pip
pip install platformio

# Or install PlatformIO IDE extension in VS Code
```

### Step 2: Register device in backend

Before flashing, register the device to get a license key:

```http
POST http://localhost:8000/api/v1/workshops/{workshop_id}/devices
Authorization: Bearer <super_admin_token>
Content-Type: application/json

{
  "device_id": "ESP32-PLACEHOLDER",
  "pit_id": <pit_id>,
  "primary_sensor_code": "DHT22"
}
```

Response includes `license_key` — copy it for the next step.

### Step 3: Update config.h

Edit `firmware/include/config.h`:

```c
// Device identity — from backend registration
#define DEVICE_ID       "ESP32-PLACEHOLDER"      // Update after first flash with real MAC
#define LICENSE_KEY     "LIC-XXXX-YYYY-ZZZZ"     // From backend response
#define WORKSHOP_ID     9                         // Your workshop ID
#define PIT_ID          7                         // Your pit ID

// MQTT broker — use your machine's LAN IP (run ipconfig on Windows / ip addr on Linux)
#define MQTT_BROKER_HOST    "192.168.29.173"      // Your server LAN IP
#define MQTT_BROKER_PORT    1883
#define MQTT_USERNAME       "mqtt_user"
#define MQTT_PASSWORD       "Ppf@Mqtt2026"        // Match docker/mosquitto/passwd
```

> **WiFi vs Ethernet:** The default `platformio.ini` uses `USE_ETHERNET`.
> If you need WiFi instead, comment out `-DUSE_ETHERNET` and uncomment `-DUSE_WIFI`,
> then also fill `WIFI_SSID` and `WIFI_PASSWORD` in `config.h`.

### Step 4: Set upload port

In `firmware/platformio.ini`, update the upload port:

```ini
upload_port = COM3    # Windows: check Device Manager
# upload_port = /dev/ttyUSB0    # Linux
```

To find the correct port:
- **Windows:** Device Manager → Ports (COM & LPT) — look for "Silicon Labs CP210x" or "CH340"
- **Linux:** `ls /dev/ttyUSB*` or `ls /dev/ttyACM*`

### Step 5: Flash the firmware

```bash
cd firmware

# Build and upload
pio run --target upload

# Monitor serial output
pio device monitor --baud 115200
```

Expected serial output on successful start:

```
[BOOT] PPF Monitor v1.0.0 starting...
[ETH]  Ethernet connected. IP: 192.168.29.xxx
[MQTT] Connecting to 192.168.29.173:1883...
[MQTT] Connected as mqtt_user
[DHT]  Reading: temp=24.5°C humidity=52.3%
[MQTT] Published: workshop/9/pit/7/sensors
[STATUS] Published device status: workshop/9/device/ESP32-.../status
```

### Step 6: Update DEVICE_ID with real MAC

The serial output shows the actual device ID (MAC-based). Update `config.h` and re-register:

```
[BOOT] Device ID: ESP32-A4CF12345678
```

```c
// Update config.h
#define DEVICE_ID "ESP32-A4CF12345678"
```

Then update in backend:
```http
PATCH /api/v1/devices/ESP32-PLACEHOLDER
{"device_id": "ESP32-A4CF12345678"}
```

---

## Verifying the Pipeline

After the device is flashing:

### 1. Backend logs

```bash
# Watch for sensor readings
tail -f backend/logs/ppf_backend.log | grep "Stored sensor"
```

Expected:
```
Stored sensor reading: pit_id=7 temp=24.5 humidity=52.3
```

### 2. Mosquitto logs

```bash
docker logs -f ppf_mosquitto | grep "workshop"
```

Expected:
```
New client connected from 192.168.x.x ... as ESP32-... (u'mqtt_user')
```

### 3. Frontend dashboard

Open `http://localhost:5173` and log in. The pit card for "Bay 1" in "Final Smoke WS" should show:
- Live temperature tile (updates every 10 seconds)
- Live humidity tile
- Green "Online" badge on the device

### 4. WebSocket check (browser console)

```javascript
// Run in browser DevTools console on the dashboard
// You should see incoming sensor_update events
```

---

## Sensor Calibration

### DHT22 temperature offset

If the sensor reads high due to self-heating, apply an offset in `config.h`:

```c
// (Not currently used — would need to be added to firmware read logic)
// Typical offset: -2.0 to -3.0°C in enclosed enclosures
```

### Alert thresholds

Default alert thresholds are configured per-workshop in the backend. To change them:
- Go to `Workshop Settings → Alert Configuration` in the dashboard
- Or use `POST /api/v1/workshops/{id}/alert-config`

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| No serial output | Wrong baud rate | Set to 115200 |
| `ETH: Failed` | No Ethernet cable | Plug in RJ45 cable |
| `MQTT: Connection refused` | Wrong broker IP or port | Check `MQTT_BROKER_HOST` in config.h — must be LAN IP, not localhost |
| `MQTT: Bad username/password` | Wrong MQTT credentials | Match `MQTT_PASSWORD` with `docker/mosquitto/passwd` |
| `License INVALID` | Wrong license key | Re-register device, copy new `license_key` |
| DHT22 reads `nan` | Missing pull-up resistor | Add 10kΩ between DATA and 3.3V |
| DHT22 reads `nan` | Too fast polling | Minimum 2 seconds between reads (firmware enforces this) |
| PMS5003 no data | Needs warmup | Wait 30 seconds after power-on |

---

*PPF Monitoring Team — 2026*
