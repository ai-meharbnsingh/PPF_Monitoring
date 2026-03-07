# Raspberry Pi Sensor Wiring Guide (Updated 2026-03-06)

This document describes the wiring for the **BME688** (I2C) and **PMS5003** (UART) sensors connected directly to the Raspberry Pi GPIO header, replacing the previous ESP32 setup.

## 1. Pin Layout Summary

| Component | Function | Raspberry Pi Pin | GPIO Number |
|-----------|----------|------------------|-------------|
| **BME688** | VCC (3.3V)| Pin 1            | -           |
| **BME688** | SDA      | Pin 3            | GPIO 2      |
| **BME688** | SCL      | Pin 5            | GPIO 3      |
| **BME688** | GND      | Pin 9            | -           |
| **PMS5003**| VCC (5V) | Pin 4            | -           |
| **PMS5003**| GND      | Pin 6            | -           |
| **PMS5003**| RX (Input)| Pin 8            | GPIO 14 (TX)|
| **PMS5003**| TX (Output)| Pin 10           | GPIO 15 (RX)|

---

## 2. Software Configuration (On Pi)

### I2C Configuration
The BME688 uses **Hardware I2C** (Bus 1) on pins 3 and 5.
- **Config file:** `/boot/firmware/config.txt`
- **Ensure Line is present:** `dtparam=i2c_arm=on`
- **Device Node:** `/dev/i2c-1`

### Serial Setup
The PMS5003 uses the hardware UART.
- **Device Node:** `/dev/serial0` (linked to `/dev/ttyS0`)
- **Config:** `enable_uart=1` in `config.txt`

### Background Service
The data is read and published to MQTT via a systemd service.
- **Service:** `pi-sensors.service`
- **Script:** `/home/pi/wifi-portal/pi_sensor_mqtt.py`
- **MQTT Topic:** `workshop/1/pit/1/sensors`
- **Device ID:** `PIWIFI-01`

---

## 3. Management Commands

```bash
# Check if sensors are running
sudo systemctl status pi-sensors

# View live sensor logs
sudo journalctl -u pi-sensors -f

# Scan for BME688 on the hardware bus
sudo i2cdetect -y 1

# Restart the sensor service
sudo systemctl restart pi-sensors
```

---

## 4. Database Integration
The script mimics the ESP32 JSON payload format. The backend `mqtt_service.py` processes this data automatically and stores it in the `sensor_data` table.

**Example Payload:**
```json
{
    "device_id": "PIWIFI-01",
    "license_key": "LIC-MOCK-PI-2026",
    "sensor_type": "BME688+PMS5003",
    "temperature": 24.50,
    "humidity": 55.20,
    "pm25": 12,
    "timestamp": "2026-03-06T16:53:45Z"
}
```
