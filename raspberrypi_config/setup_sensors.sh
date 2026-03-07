#!/bin/bash
#
# Setup script for BME688 + PMS5003 sensors on Raspberry Pi
# This script installs dependencies, fixes permissions, and sets up the service
#

set -e

echo "=========================================="
echo "Pi Sensor Setup - BME688 + PMS5003"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}Please run as regular user (pi), not root${NC}"
   exit 1
fi

echo "Step 1: Installing dependencies..."
pip3 install --user bme680 pyserial paho-mqtt smbus2
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

echo "Step 2: Enabling I2C interface..."
sudo raspi-config nonint do_i2c 0
echo -e "${GREEN}✅ I2C enabled${NC}"
echo ""

echo "Step 3: Enabling UART interface..."
sudo raspi-config nonint do_serial 1  # Disable console, enable UART
echo -e "${GREEN}✅ UART enabled${NC}"
echo ""

echo "Step 4: Fixing PMS5003 serial permissions..."
# Stop serial console from using the port
sudo systemctl stop serial-getty@ttyS0.service 2>/dev/null || true
sudo systemctl disable serial-getty@ttyS0.service 2>/dev/null || true

# Add pi user to tty group
sudo usermod -a -G tty pi

# Fix device permissions
sudo chmod 666 /dev/ttyS0 2>/dev/null || true
echo -e "${GREEN}✅ Serial permissions fixed${NC}"
echo ""

echo "Step 5: Creating sensor script..."
mkdir -p /home/pi/wifi-portal
cat > /home/pi/wifi-portal/pi_sensor_mqtt.py << 'EOF'
#!/usr/bin/env python3
"""Pi Sensor MQTT Publisher - BME688 + PMS5003"""

import time
import ssl
import json
import serial
import paho.mqtt.client as mqtt
import bme680
from smbus2 import SMBus
from datetime import datetime, UTC

# Configuration
MQTT_BROKER = 'c4cb4d2b4a3e432c9d61b8b56ee359af.s1.eu.hivemq.cloud'
MQTT_PORT = 8883
MQTT_USER = 'ppf_backend'
MQTT_PASS = 'PPF@Mqtt2026!secure'
DEVICE_ID = 'PIWIFI-01'
LICENSE_KEY = 'LIC-RG-STUDIO-2026'
WORKSHOP_ID = 2
PIT_ID = 3
TOPIC = f'workshop/{WORKSHOP_ID}/pit/{PIT_ID}/sensors'

# Initialize PMS5003
print('Initializing PMS5003...')
ser = None
try:
    ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1.5)
    print('✅ PMS5003 ready')
except Exception as e:
    print(f'⚠️ PMS5003 skipped: {e}')

def read_pms5003(ser):
    if ser is None: return None
    try:
        data = ser.read(32)
        if len(data) < 32: return None
        if data[0] != 0x42 or data[1] != 0x4d:
            ser.flushInput()
            return None
        pm1 = (data[10] << 8) | data[11]
        pm25 = (data[12] << 8) | data[13]
        pm10 = (data[14] << 8) | data[15]
        return {'pm1': pm1, 'pm25': pm25, 'pm10': pm10}
    except:
        return None

# Initialize BME688 with retries
print('Initializing BME688...')
bme = None
for attempt in range(5):
    try:
        bus = SMBus(1)
        bme = bme680.BME680(i2c_addr=0x76, i2c_device=bus)
        bme.set_humidity_oversample(bme680.OS_2X)
        bme.set_pressure_oversample(bme680.OS_4X)
        bme.set_temperature_oversample(bme680.OS_8X)
        bme.set_filter(bme680.FILTER_SIZE_3)
        print(f'✅ BME688 ready (attempt {attempt+1})')
        break
    except Exception as e:
        print(f'  Attempt {attempt+1} failed: {e}')
        time.sleep(1)

if bme is None:
    print('⚠️ BME688 not available')

def read_bme688(bme):
    if bme is None: return None
    try:
        if bme.get_sensor_data():
            return {
                'temperature': round(bme.data.temperature, 2),
                'humidity': round(bme.data.humidity, 2),
                'pressure': round(bme.data.pressure, 2)
            }
    except:
        pass
    return None

# MQTT Setup
print(f'Connecting to MQTT: {MQTT_BROKER}...')
client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id=f'pi-sensor-{DEVICE_ID}'
)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print('✅ Connected to MQTT!')
    else:
        print(f'❌ Connection failed: {rc}')

client.on_connect = on_connect
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.tls_set()

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
except Exception as e:
    print(f'❌ MQTT Error: {e}')
    exit(1)

# Main Loop
print('Starting sensor data stream...')
time.sleep(2)

while True:
    try:
        pms_data = read_pms5003(ser)
        bme_data = read_bme688(bme)
        
        payload = {
            'device_id': DEVICE_ID,
            'license_key': LICENSE_KEY,
            'timestamp': datetime.now(UTC).isoformat(),
            'sensor_type': 'PIWIFI-01'
        }
        
        if pms_data:
            payload.update(pms_data)
        if bme_data:
            payload.update(bme_data)
        
        if pms_data or bme_data:
            client.publish(TOPIC, json.dumps(payload))
            temp = bme_data['temperature'] if bme_data else 'N/A'
            hum = bme_data['humidity'] if bme_data else 'N/A'
            pm25 = pms_data['pm25'] if pms_data else 'N/A'
            print(f'Published: T={temp}°C, H={hum}%, PM2.5={pm25}')
        
        time.sleep(10)
    except Exception as e:
        print(f'Loop error: {e}')
        time.sleep(10)
EOF

chmod +x /home/pi/wifi-portal/pi_sensor_mqtt.py
echo -e "${GREEN}✅ Sensor script created${NC}"
echo ""

echo "Step 6: Creating systemd service..."
sudo tee /etc/systemd/system/pi-sensors.service > /dev/null << EOF
[Unit]
Description=Pi Sensor Data to MQTT
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/wifi-portal
ExecStart=/usr/bin/python3 /home/pi/wifi-portal/pi_sensor_mqtt.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Service file created${NC}"
echo ""

echo "Step 7: Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable pi-sensors
sudo systemctl start pi-sensors
echo -e "${GREEN}✅ Service started${NC}"
echo ""

echo "Step 8: Testing sensors..."
sleep 3
echo "Checking I2C (BME688):"
sudo i2cdetect -y 1 | grep -E "76|77" && echo -e "${GREEN}✅ BME688 detected${NC}" || echo -e "${YELLOW}⚠️ BME688 not found on I2C${NC}"

echo ""
echo "Checking serial (PMS5003):"
ls -la /dev/serial0
ls -la /dev/ttyS0 | grep "rw-rw-rw-" && echo -e "${GREEN}✅ Serial permissions OK${NC}" || echo -e "${YELLOW}⚠️ Serial permissions need fix${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}Setup complete!${NC}"
echo "=========================================="
echo ""
echo "Check service status:"
echo "  sudo systemctl status pi-sensors"
echo ""
echo "View logs:"
echo "  sudo journalctl -u pi-sensors -f"
echo ""
echo "Test manually:"
echo "  python3 /home/pi/wifi-portal/pi_sensor_mqtt.py"
echo ""
