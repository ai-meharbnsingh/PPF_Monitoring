#!/bin/bash
# Raspberry Pi Configuration Restore Script
# This script restores the WiFi Portal and MediaMTX setup on a Raspberry Pi

set -e

echo "=========================================="
echo "Raspberry Pi Configuration Restore"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PI_IP="${1:-192.168.29.115}"
PI_USER="${2:-pi}"
PI_PASS="${3:-raspberry}"

echo -e "${BLUE}Target Pi: $PI_USER@$PI_IP${NC}"
echo ""

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo -e "${YELLOW}Installing sshpass...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install sshpass
    else
        sudo apt-get install -y sshpass
    fi
fi

# Function to run commands on Pi
run_on_pi() {
    sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $PI_USER@$PI_IP "$1"
}

# Function to copy files to Pi
copy_to_pi() {
    local src=$1
    local dest=$2
    sshpass -p "$PI_PASS" scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$src" $PI_USER@$PI_IP:"$dest"
}

echo -e "${YELLOW}Step 1: Testing connection to Pi...${NC}"
if ! run_on_pi "echo 'Connection successful'" > /dev/null 2>&1; then
    echo -e "${RED}Failed to connect to Pi at $PI_IP${NC}"
    echo "Please check:"
    echo "  - Pi is powered on"
    echo "  - Pi is on the same network"
    echo "  - IP address is correct"
    exit 1
fi
echo -e "${GREEN}✓ Connected to Pi${NC}"
echo ""

# ============================================
# Setup WiFi Portal
# ============================================
echo -e "${YELLOW}Step 2: Setting up WiFi Portal...${NC}"

run_on_pi "mkdir -p ~/wifi-portal/templates"

# Copy files
echo "Copying WiFi portal files..."
sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $PI_USER@$PI_IP "cat > ~/wifi-portal/wifi_server.py" < wifi_server.py

# Install dependencies
echo "Installing dependencies..."
run_on_pi "sudo apt-get update -qq && sudo apt-get install -y -qq python3-pip python3-venv network-manager wireless-tools iw avahi-daemon 2>/dev/null || true"

# Create virtual environment
echo "Setting up Python virtual environment..."
run_on_pi "cd ~/wifi-portal && python3 -m venv venv 2>/dev/null || true"
run_on_pi "cd ~/wifi-portal && ./venv/bin/pip install -q flask flask-cors werkzeug 2>/dev/null || true"

# Set hostname for mDNS
echo "Configuring mDNS hostname..."
run_on_pi "sudo hostnamectl set-hostname piwifi 2>/dev/null || true"
run_on_pi "sudo systemctl enable avahi-daemon 2>/dev/null || true"
run_on_pi "sudo systemctl restart avahi-daemon 2>/dev/null || true"

# Start server
echo "Starting WiFi portal server..."
run_on_pi "pkill -f wifi_server 2>/dev/null || true"
sleep 1
run_on_pi "cd ~/wifi-portal && nohup ./venv/bin/python wifi_server.py > server.log 2>&1 &"
sleep 3

# Check if running
if run_on_pi "pgrep -f wifi_server" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ WiFi Portal is running${NC}"
else
    echo -e "${RED}✗ WiFi Portal failed to start${NC}"
fi
echo ""

# ============================================
# Setup MediaMTX
# ============================================
echo -e "${YELLOW}Step 3: Setting up MediaMTX...${NC}"

run_on_pi "mkdir -p ~/mediamtx-server"

# Check if MediaMTX is already installed
if run_on_pi "test -f ~/mediamtx-server/mediamtx" > /dev/null 2>&1; then
    echo "MediaMTX already installed, updating config..."
else
    echo "Downloading MediaMTX..."
    run_on_pi "cd ~/mediamtx-server && wget -q https://github.com/bluenviron/mediamtx/releases/download/v1.11.3/mediamtx_v1.11.3_linux_arm64v8.tar.gz"
    run_on_pi "cd ~/mediamtx-server && tar -xzf mediamtx_*.tar.gz"
    echo -e "${GREEN}✓ MediaMTX downloaded${NC}"
fi

# Copy config
echo "Copying MediaMTX configuration..."
sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $PI_USER@$PI_IP "cat > ~/mediamtx-server/mediamtx.yml" < mediamtx.yml

# Start MediaMTX
echo "Starting MediaMTX..."
run_on_pi "pkill -f mediamtx 2>/dev/null || true"
sleep 1
run_on_pi "cd ~/mediamtx-server && nohup ./mediamtx ./mediamtx.yml > mediamtx.log 2>&1 &"
sleep 3

# Check if running
if run_on_pi "pgrep -f mediamtx" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ MediaMTX is running${NC}"
else
    echo -e "${RED}✗ MediaMTX failed to start${NC}"
fi
echo ""

# ============================================
# Summary
# ============================================
echo "=========================================="
echo -e "${GREEN}Restore Complete!${NC}"
echo "=========================================="
echo ""
echo -e "${BLUE}WiFi Portal:${NC}"
echo "  URL: http://$PI_IP:8080"
echo "  URL: http://piwifi.local:8080"
echo ""
echo -e "${BLUE}MediaMTX Stream:${NC}"
echo "  WebRTC: http://$PI_IP:8889/cam1/whep"
echo "  HLS:    http://$PI_IP:8888/cam1/index.m3u8"
echo "  RTSP:   rtsp://$PI_IP:8554/cam1"
echo ""
echo -e "${BLUE}Management Commands:${NC}"
echo "  SSH:    ssh pi@$PI_IP"
echo "  Reboot: ssh pi@$PI_IP 'sudo reboot'"
echo ""
echo "=========================================="
