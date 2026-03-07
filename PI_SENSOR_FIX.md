# 🔧 Pi Sensor Fix - Physical Action Required

## Current Status
- ✅ Pi is ONLINE (192.168.29.115)
- ✅ Sensor service is running
- ❌ NO DATA being published to MQTT

## Problem
The sensor script is hanging/stuck when trying to read sensors.

---

## 🔧 PHYSICAL FIX (Do This)

### Step 1: SSH into Pi
Open terminal on your computer:

```bash
ssh pi@192.168.29.115
# Password: raspberry
```

### Step 2: Stop the Service
```bash
sudo systemctl stop pi-sensors
```

### Step 3: Test Sensors Manually
```bash
cd /home/pi/wifi-portal

# Test BME688
python3 -c "
import smbus
import bme680
print('Testing BME688...')
bus = smbus.SMBus(3)
bme = bme680.BME680(i2c_device=bus)
print('BME688 initialized')
if bme.get_sensor_data():
    print(f'OK: Temp={bme.data.temperature}C, Humidity={bme.data.humidity}%')
else:
    print('No data - sensor not ready')
"
```

**Does this show temperature?**

### Step 4: If No Data, Check Wiring

**BME688 (4 wires):**
```
Pi Pin 17 (3.3V)  → BME688 VCC (Red)
Pi Pin 19 (GPIO10) → BME688 SDA (Yellow)
Pi Pin 21 (GPIO9)  → BME688 SCL (Blue)
Pi Pin 25 (GND)    → BME688 GND (Black)
```

**Unplug and replug all 4 wires!**

### Step 5: Restart Service
```bash
sudo systemctl restart pi-sensors
sudo systemctl status pi-sensors
```

### Step 6: Watch Logs
```bash
sudo journalctl -u pi-sensors -f
```

You should see: "Published: {\"device_id\": \"PIWIFI-01\", ...}"

---

## Quick Alternative: Reboot Pi

If above doesn't work:
```bash
sudo reboot
```

Wait 2 minutes, then check if data appears on dashboard.

---

## Verify Data is Flowing

Once fixed, verify at:
- Dashboard: https://ppf-monitoring.vercel.app
- Or run: `curl https://ppf-backend-w0aq.onrender.com/api/v1/workshops/2/pits/3/sensors/latest`
