#!/bin/bash
# Simple Hikvision Camera Viewer
# Usage: ./view_camera_simple.sh [IP_ADDRESS] [PASSWORD]

# Default settings
IP="${1:-192.168.1.64}"
PASSWORD="${2:-}"
USERNAME="admin"
CHANNEL="101"  # 101=main, 102=sub

echo "=============================================="
echo "🎥 Hikvision Camera Viewer"
echo "=============================================="
echo "IP: $IP"
echo "Username: $USERNAME"
echo "Channel: $CHANNEL"
echo "=============================================="
echo ""

# Build RTSP URL
if [ -z "$PASSWORD" ]; then
    URL="rtsp://${USERNAME}@${IP}:554/Streaming/Channels/${CHANNEL}"
else
    URL="rtsp://${USERNAME}:${PASSWORD}@${IP}:554/Streaming/Channels/${CHANNEL}"
fi

echo "Connecting to: $URL"
echo "Press Q to quit, F for fullscreen"
echo ""

# Launch ffplay
ffplay -rtsp_transport tcp -i "$URL" -window_title "Hikvision Camera $IP" -vf "scale=1280:720"
