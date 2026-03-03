#!/bin/bash
# Tailscale Status Checker
# Shows current status and camera URLs

echo "========================================"
echo "Tailscale & Camera Status"
echo "========================================"
echo ""

# Check if Tailscale is installed
if ! command -v tailscale &> /dev/null; then
    echo "❌ Tailscale NOT installed"
    echo ""
    echo "Install with:"
    echo "  curl -fsSL https://tailscale.com/install.sh | sh"
    exit 1
fi

# Check Tailscale status
echo -n "Tailscale Status: "
if sudo tailscale status &>/dev/null; then
    echo "✅ Running"
else
    echo "❌ Not running"
    echo ""
    echo "Start with: sudo tailscale up"
    exit 1
fi

# Get Tailscale IP
TAILSCALE_IP=$(tailscale ip -4 2>/dev/null)
if [ -z "$TAILSCALE_IP" ]; then
    echo "❌ Could not get Tailscale IP"
    exit 1
fi

echo ""
echo "========================================"
echo "📡 YOUR CAMERA URLs (Share these!)"
echo "========================================"
echo ""
echo "Tailscale IP: $TAILSCALE_IP"
echo ""
echo "🎥 LIVE STREAM URLs:"
echo "--------------------"
echo ""
echo "WebRTC (Best for browser):"
echo "  http://$TAILSCALE_IP:8889/cam1/whep"
echo ""
echo "HLS (Most compatible):"
echo "  http://$TAILSCALE_IP:8888/cam1/index.m3u8"
echo ""
echo "RTSP (For VLC/apps):"
echo "  rtsp://$TAILSCALE_IP:8554/cam1"
echo ""
echo "📊 WiFi Portal:"
echo "  http://$TAILSCALE_IP:8080"
echo ""
echo "========================================"
echo ""

# Check if MediaMTX is running
echo -n "MediaMTX Status: "
if pgrep -f "mediamtx" > /dev/null; then
    echo "✅ Running"
else
    echo "❌ Not running"
    echo "  Start: cd ~/mediamtx-server && ./mediamtx ./mediamtx.yml &"
fi

# Check if camera registration is running
echo -n "Camera Registration: "
if pgrep -f "camera_register" > /dev/null; then
    echo "✅ Running"
else
    echo "❌ Not running"
    echo "  Start: cd ~/wifi-portal && python3 camera_register_external.py"
fi

echo ""
echo "========================================"
echo "📱 To Access From Your Devices:"
echo "========================================"
echo ""
echo "1. Install Tailscale on your device"
echo "   https://tailscale.com/download"
echo ""
echo "2. Login with SAME account as Pi"
echo ""
echo "3. Open browser and go to:"
echo "   http://$TAILSCALE_IP:8889/cam1/whep"
echo ""
echo "========================================"
echo ""
echo "Connected Devices:"
sudo tailscale status | grep -v "^#" | head -10
echo ""
