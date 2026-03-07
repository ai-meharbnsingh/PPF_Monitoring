# 🔍 Raspberry Pi Diagnostic Report

**Device:** piwifi (192.168.29.115)  
**Time:** 2026-03-07  
**Status:** ⚠️ Online but sensor service status unknown

---

## Network Connectivity

| Test | Status | Details |
|------|--------|---------|
| Ping | ✅ **ONLINE** | 0% packet loss, ~8ms avg latency |
| SSH (port 22) | ✅ Open | Port responding |
| WiFi Portal (8080) | ✅ **RUNNING** | HTTP 200 OK |
| MediaMTX HLS (8888) | ⚠️ 404 | Service running but no stream configured |
| mDNS (piwifi.local) | ✅ **WORKING** | Resolves to 192.168.29.115 |

---

## MQTT Data Status

| Test | Status | Details |
|------|--------|---------|
| MQTT Broker Connection | ✅ Connected | Successfully connected to HiveMQ Cloud |
| Sensor Messages | ❌ **NO DATA** | No sensor data received in 5-second window |

---

## Summary

### ✅ What's Working
- Pi is **online and network-accessible**
- WiFi Portal service is **running**
- MediaMTX streaming service is **running**
- MQTT broker connection is **working**

### ⚠️ What's Not Working
- **No sensor data being published**
- **SSH authentication failed** (need correct password)

---

## Possible Causes

1. **Sensor service not running**
   - The `pi-sensors` systemd service may be stopped
   - Python script may have crashed

2. **Sensor hardware issue**
   - BME688 or PMS5003 not connected properly
   - I2C/UART not configured

3. **MQTT configuration issue**
   - Wrong credentials in sensor script
   - Topic mismatch

---

## Next Steps (Manual Check Required)

### Option 1: Check via SSH (Recommended)

SSH into the Pi with the correct password:

```bash
ssh pi@192.168.29.115
# Password: raspberry (or your custom password)

# Check sensor service status
sudo systemctl status pi-sensors

# View recent logs
sudo journalctl -u pi-sensors -f

# Restart sensor service if needed
sudo systemctl restart pi-sensors

# Check if sensors are connected
sudo i2cdetect -y 3  # Should show 76 or 77 for BME688
```

### Option 2: Physical Check

If SSH doesn't work:
1. Connect a monitor/keyboard to the Pi
2. Login with username: `pi`, password: `raspberry`
3. Run the commands above

### Option 3: Web Portal Check

The WiFi portal is running at:
- http://192.168.29.115:8080

Check if there's any status information there.

---

## Quick Fixes to Try

### Restart Sensor Service
```bash
ssh pi@192.168.29.115
sudo systemctl restart pi-sensors
sudo systemctl status pi-sensors
```

### Check Sensor Script Manually
```bash
ssh pi@192.168.29.115
cd /home/pi/wifi-portal
sudo python3 pi_sensor_mqtt.py
```

### Verify Sensor Wiring
Check your PI_MASTER_CONFIG.md Section 6:
- BME688 should be on I2C bus 3 (pins GPIO10/SDA, GPIO9/SCL)
- PMS5003 should be on UART (pins GPIO14/TX, GPIO15/RX)

---

## Expected Data Flow

```
Pi (192.168.29.115)
  Reads BME688 + PMS5003 sensors
  Publishes to MQTT (workshop/2/pit/3/sensors)
  HiveMQ Cloud Broker
  Backend receives and stores data
  Dashboard displays live readings
```

---

## Verification Commands

Once fixed, verify with:

```bash
# Check backend is receiving data
curl https://ppf-backend-w0aq.onrender.com/api/v1/workshops/2/pits/3/sensors/latest
```

---

## Current Status

🔴 **Pi is ONLINE but NOT generating sensor data**

**Action required:** Check sensor service via SSH or physically connect to the Pi.
