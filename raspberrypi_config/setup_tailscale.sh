#!/bin/bash
# Tailscale Setup Script for Raspberry Pi Camera Streaming
# This sets up Tailscale VPN so camera is accessible from anywhere

set -e

echo "=========================================="
echo "Tailscale VPN Setup for Camera Streaming"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}Please do NOT run as root${NC}"
   exit 1
fi

echo -e "${YELLOW}Step 1: Installing Tailscale...${NC}"

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

echo -e "${GREEN}✓ Tailscale installed${NC}"
echo ""

echo -e "${YELLOW}Step 2: Starting Tailscale...${NC}"
echo ""
echo -e "${BLUE}IMPORTANT:${NC} You'll see a login URL."
echo -e "${BLUE}IMPORTANT:${NC} Open it in your browser to authenticate."
echo ""
echo "Press Enter to continue..."
read

# Start Tailscale
sudo tailscale up

echo ""
echo -e "${YELLOW}Step 3: Getting Tailscale IP...${NC}"

# Get Tailscale IP
TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "")

if [ -z "$TAILSCALE_IP" ]; then
    echo -e "${RED}Failed to get Tailscale IP. Is Tailscale running?${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Your Tailscale IP: $TAILSCALE_IP${NC}"
echo ""

echo -e "${YELLOW}Step 4: Configuring firewall...${NC}"

# Allow Tailscale traffic
sudo iptables -I INPUT -i tailscale0 -j ACCEPT 2>/dev/null || true
sudo iptables -I FORWARD -i tailscale0 -j ACCEPT 2>/dev/null || true

echo -e "${GREEN}✓ Firewall configured${NC}"
echo ""

echo -e "${YELLOW}Step 5: Setting up camera registration with Tailscale...${NC}"

# Create systemd service for camera registration with Tailscale
cat > /tmp/camera-register-tailscale.service << EOF
[Unit]
Description=Camera MQTT Registration (Tailscale)
After=network.target tailscaled.service
Requires=tailscaled.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/wifi-portal
Environment="USE_TAILSCALE=true"
Environment="TAILSCALE_IP=$TAILSCALE_IP"
Environment="MQTT_BROKER=192.168.29.173"
Environment="MQTT_PORT=1883"
Environment="MQTT_USERNAME=ppf_backend"
Environment="MQTT_PASSWORD=your_mqtt_password"
Environment="WORKSHOP_ID=1"
Environment="CAMERA_ID=pi_camera_01"
Environment="CAMERA_NAME=Raspberry Pi Camera 1"
ExecStart=/home/pi/wifi-portal/venv/bin/python /home/pi/wifi-portal/camera_register_external.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/camera-register-tailscale.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable camera-register-tailscale

echo -e "${GREEN}✓ Service created${NC}"
echo ""

echo -e "${YELLOW}Step 6: Creating access info file...${NC}"

cat > ~/TAILSCALE_ACCESS_INFO.txt << EOF
========================================
TAILSCALE CAMERA ACCESS INFORMATION
========================================

Your Pi Tailscale IP: $TAILSCALE_IP

STREAM URLs (Accessible from anywhere with Tailscale):
--------------------------------------------------------
WebRTC (Primary):
  http://$TAILSCALE_IP:8889/cam1/whep
  http://$TAILSCALE_IP:8889/cam1-sub/whep

HLS (Fallback):
  http://$TAILSCALE_IP:8888/cam1/index.m3u8
  http://$TAILSCALE_IP:8888/cam1-sub/index.m3u8

RTSP:
  rtsp://$TAILSCALE_IP:8554/cam1
  rtsp://$TAILSCALE_IP:8554/cam1-sub

ACCESS FROM ANY DEVICE:
-----------------------
1. Install Tailscale on your device
   - Windows/Mac: https://tailscale.com/download
   - iOS/Android: App Store
   - Linux: curl -fsSL https://tailscale.com/install.sh | sh

2. Login with same account as Pi

3. Access camera at:
   http://$TAILSCALE_IP:8889/cam1/whep

Or open in your app:
   http://$TAILSCALE_IP:8080 (WiFi Portal)

========================================
EOF

cat ~/TAILSCALE_ACCESS_INFO.txt

echo ""
echo -e "${GREEN}✓ Access info saved to ~/TAILSCALE_ACCESS_INFO.txt${NC}"
echo ""

echo -e "${YELLOW}Step 7: Installing Tailscale on your laptop/phone...${NC}"
echo ""
echo "Please install Tailscale on devices you want to access the camera from:"
echo ""
echo "  Windows/Mac: https://tailscale.com/download"
echo "  iOS: App Store search 'Tailscale'"
echo "  Android: Play Store search 'Tailscale'"
echo "  Linux: curl -fsSL https://tailscale.com/install.sh | sh"
echo ""
echo "Use the SAME login/account as you used for the Pi!"
echo ""

echo -e "${YELLOW}Step 8: Starting services...${NC}"

# Start camera registration service
sudo systemctl start camera-register-tailscale

echo -e "${GREEN}✓ Camera registration service started${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}SETUP COMPLETE!${NC}"
echo "=========================================="
echo ""
echo "Your camera is now accessible from ANYWHERE"
echo "via Tailscale VPN!"
echo ""
echo -e "Tailscale IP: ${BLUE}$TAILSCALE_IP${NC}"
echo ""
echo "To check status:"
echo "  sudo tailscale status"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u camera-register-tailscale -f"
echo ""
echo "Stream URL:"
echo "  http://$TAILSCALE_IP:8889/cam1/whep"
echo ""
echo "=========================================="
