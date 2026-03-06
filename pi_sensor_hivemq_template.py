#!/usr/bin/env python3
"""
PiWiFi Sensor Script - HiveMQ Cloud Version
Sends BME688 + PMS5003 data to cloud MQTT broker
"""

import json
import time
import ssl
import serial
import bme680
from smbus import SMBus
import paho.mqtt.client as mqtt
from datetime import datetime, timezone

# ==========================================
# UPDATE THESE VALUES FROM HIVEMQ DASHBOARD
# ==========================================
MQTT_BROKER = "YOUR_CLUSTER_URL.s1.eu.hivemq.cloud"  # e.g., "xxx.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "your-username"
MQTT_PASSWORD = "your-password"
USE_TLS = True

# Device Configuration
DEVICE_ID = 'PIWIFI-01'
LICENSE_KEY = 'LIC-RG-STUDIO-2026'
WORKSHOP_ID = 2
PIT_ID = 3  # Pit One
TOPIC = f'workshop/{WORKSHOP_ID}/pit/{PIT_ID}/sensors'

print(f"🔌 Connecting to HiveMQ Cloud: {MQTT_BROKER}:{MQTT_PORT}")
print(f"📡 Publishing to: {TOPIC}")

# Initialize BME688
try:
    bus = SMBus(1)
    bme = bme680.BME680(i2c_device=bus)
    bme.set_humidity_oversample(bme680.OS_2X)
    bme.set_pressure_oversample(bme680.OS_4X)
    bme.set_temperature_oversample(bme680.OS_8X)
    bme.set_gas_status(bme680.ENABLE_GAS_MEAS)
    print("✅ BME688 ready")
except Exception as e:
    print(f"❌ BME688: {e}")
    bme = None

# Initialize PMS5003
try:
    ser = serial.Serial('/dev/ttyS0', baudrate=9600, timeout=1.5)
    print("✅ PMS5003 ready")
except Exception as e:
    print(f"❌ PMS5003: {e}")
    ser = None

# MQTT Client with TLS
client = mqtt.Client(client_id=DEVICE_ID)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

if USE_TLS:
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

def on_connect(c, u, f, rc):
    if rc == 0:
        print("✅ Connected to HiveMQ Cloud!")
    else:
        print(f"❌ Connection failed: {rc}")

client.on_connect = on_connect

try:
    print(f"Connecting...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
except Exception as e:
    print(f"❌ MQTT connect failed: {e}")
    exit(1)

pms_data = {'pm1': None, 'pm25': None, 'pm10': None}

print("Starting sensor readings...")

while True:
    try:
        # Read BME688
        temp = humidity = pressure = gas = None
        if bme and bme.get_sensor_data():
            temp = bme.data.temperature
            humidity = bme.data.humidity
            pressure = bme.data.pressure
            gas = bme.data.gas_resistance
        
        # Read PMS5003
        if ser and ser.in_waiting >= 32:
            data = ser.read(32)
            if len(data) == 32 and data[0] == 0x42 and data[1] == 0x4D:
                pms_data = {
                    'pm1': (data[10] << 8) | data[11],
                    'pm25': (data[12] << 8) | data[13],
                    'pm10': (data[14] << 8) | data[15]
                }
        
        # Publish to HiveMQ
        payload = {
            'device_id': DEVICE_ID,
            'license_key': LICENSE_KEY,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'temperature': temp,
            'humidity': humidity,
            'pressure': pressure,
            'gas_resistance': gas,
            'pm1': pms_data['pm1'],
            'pm25': pms_data['pm25'],
            'pm10': pms_data['pm10']
        }
        
        client.publish(TOPIC, json.dumps(payload))
        print(f"✅ Sent: T={temp:.1f}°C, H={humidity:.1f}%, PM2.5={pms_data['pm25']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    time.sleep(10)
