#!/bin/bash
# Cloud Relay Setup - Push camera stream to cloud server
# This allows accessing camera from web app without Tailscale

set -e

echo "========================================"
echo "Cloud Relay Setup for Camera Streaming"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration - UPDATE THESE!
CLOUD_HOST="${CLOUD_HOST:-ppf-streams.fly.dev}"  # Your cloud MediaMTX server
CLOUD_PORT="${CLOUD_PORT:-8554}"
CAMERA_IP="${CAMERA_IP:-192.168.29.64}"
CAMERA_USER="${CAMERA_USER:-admin}"
CAMERA_PASS="${CAMERA_PASS:-Hik@12345}"

echo -e "${YELLOW}Configuration:${NC}"
echo "  Cloud Host: $CLOUD_HOST"
echo "  Camera IP: $CAMERA_IP"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}Please do NOT run as root${NC}"
   exit 1
fi

echo -e "${YELLOW}Step 1: Installing FFmpeg...${NC}"

if ! command -v ffmpeg &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y ffmpeg
    echo -e "${GREEN}✓ FFmpeg installed${NC}"
else
    echo -e "${GREEN}✓ FFmpeg already installed${NC}"
fi

echo ""
echo -e "${YELLOW}Step 2: Testing connection to cloud...${NC}"

if ping -c 1 $CLOUD_HOST &> /dev/null; then
    echo -e "${GREEN}✓ Cloud server reachable${NC}"
else
    echo -e "${YELLOW}⚠ Cloud server may not be reachable yet${NC}"
fi

echo ""
echo -e "${YELLOW}Step 3: Testing camera stream...${NC}"

# Test if we can access camera
if ffmpeg -rtsp_transport tcp -i "rtsp://$CAMERA_USER:$CAMERA_PASS@$CAMERA_IP:554/Streaming/Channels/101" -t 1 -f null - &>/dev/null; then
    echo -e "${GREEN}✓ Camera accessible${NC}"
else
    echo -e "${RED}✗ Cannot access camera at $CAMERA_IP${NC}"
    echo "Please check camera IP and credentials"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 4: Creating cloud relay service...${NC}"

# Create systemd service
cat > /tmp/camera-cloud-relay.service << EOF
[Unit]
Description=Camera Cloud Relay to $CLOUD_HOST
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/ffmpeg \
  -hide_banner \
  -loglevel error \
  -rtsp_transport tcp \
  -i "rtsp://$CAMERA_USER:$CAMERA_PASS@$CAMERA_IP:554/Streaming/Channels/101" \
  -c copy \
  -f rtsp \
  -rtsp_transport tcp \
  "rtsp://$CLOUD_HOST:$CLOUD_PORT/cam1"
Restart=always
RestartSec=30
StartLimitInterval=60s
StartLimitBurst=3

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/camera-cloud-relay.service /etc/systemd/system/
sudo systemctl daemon-reload

echo -e "${GREEN}✓ Service created${NC}"

echo ""
echo -e "${YELLOW}Step 5: Creating camera registration with cloud URLs...${NC}"

cat > ~/camera_register_cloud.py << 'PYTHON_EOF'
#!/usr/bin/env python3
"""Register camera with cloud relay URLs"""
import json
import os
from datetime import datetime
import paho.mqtt.client as mqtt

# Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', '192.168.29.173')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', 'ppf_backend')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')
WORKSHOP_ID = os.getenv('WORKSHOP_ID', '1')
CAMERA_ID = os.getenv('CAMERA_ID', 'pi_camera_01')
CAMERA_NAME = os.getenv('CAMERA_NAME', 'Raspberry Pi Camera 1')

# CLOUD CONFIG
CLOUD_HOST = os.getenv('CLOUD_HOST', 'ppf-streams.fly.dev')

def get_stream_urls():
    """Generate cloud stream URLs"""
    return {
        'webrtc': {
            'main': f'https://{CLOUD_HOST}/cam1/whep',
            'sub': f'https://{CLOUD_HOST}/cam1-sub/whep'
        },
        'hls': {
            'main': f'https://{CLOUD_HOST}/cam1/index.m3u8',
            'sub': f'https://{CLOUD_HOST}/cam1-sub/index.m3u8'
        },
        'rtsp': {
            'main': f'rtsp://{CLOUD_HOST}:8554/cam1',
            'sub': f'rtsp://{CLOUD_HOST}:8554/cam1-sub'
        },
        'note': f'via cloud relay {CLOUD_HOST}'
    }

def main():
    client = mqtt.Client(client_id=f'camera_{CAMERA_ID}')
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    stream_urls = get_stream_urls()
    
    camera_info = {
        'device_id': CAMERA_ID,
        'name': CAMERA_NAME,
        'camera_type': 'raspberry_pi_cloud',
        'ip_address': '127.0.0.1',  # Local only, cloud handles external
        'workshop_id': WORKSHOP_ID,
        'status': 'online',
        'is_online': True,
        'stream_urls': stream_urls,
        'capabilities': {
            'resolutions': ['1920x1080', '640x360'],
            'protocols': ['webrtc', 'hls', 'rtsp'],
            'has_audio': False,
            'has_ptz': False
        },
        'access_type': 'cloud_relay',
        'cloud_host': CLOUD_HOST,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    print(f"Connecting to MQTT at {MQTT_BROKER}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    topic = f'workshop/{WORKSHOP_ID}/cameras/register'
    client.publish(topic, json.dumps(camera_info), qos=1)
    
    print(f"✅ Camera registered with cloud URLs!")
    print(f"   WebRTC: {stream_urls['webrtc']['main']}")
    print(f"   HLS: {stream_urls['hls']['main']}")
    print(f"   Cloud Host: {CLOUD_HOST}")
    
    client.disconnect()

if __name__ == '__main__':
    main()
PYTHON_EOF

chmod +x ~/camera_register_cloud.py

echo -e "${GREEN}✓ Registration script created${NC}"

echo ""
echo -e "${YELLOW}Step 6: Starting services...${NC}"

# Start cloud relay
sudo systemctl enable camera-cloud-relay
sudo systemctl start camera-cloud-relay

echo -e "${GREEN}✓ Cloud relay service started${NC}"

echo ""
echo "========================================"
echo -e "${GREEN}SETUP COMPLETE!${NC}"
echo "========================================"
echo ""
echo -e "Cloud Host: ${BLUE}$CLOUD_HOST${NC}"
echo ""
echo "Stream URLs (accessible from anywhere):"
echo "  WebRTC: https://$CLOUD_HOST/cam1/whep"
echo "  HLS:    https://$CLOUD_HOST/cam1/index.m3u8"
echo ""
echo "Status Commands:"
echo "  sudo systemctl status camera-cloud-relay"
echo "  sudo journalctl -u camera-cloud-relay -f"
echo ""
echo "To register camera with backend:"
echo "  python3 ~/camera_register_cloud.py"
echo ""
