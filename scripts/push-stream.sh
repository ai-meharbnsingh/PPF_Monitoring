#!/bin/bash
###############################################################################
# push-stream.sh
#
# Runs on the WORKSHOP MACHINE (the PC/laptop at the workshop).
# Pulls the RTSP stream from the local Hikvision camera and
# pushes it to the Fly.io MediaMTX server continuously.
#
# Requirements:
#   - ffmpeg installed  (brew install ffmpeg  OR  apt install ffmpeg)
#   - Network access to 192.168.29.64 (local camera)
#   - Network access to ppf-mediamtx.fly.dev (internet)
#
# Usage:
#   chmod +x push-stream.sh
#   ./push-stream.sh
#
# To run in background (auto-restart on crash):
#   nohup ./push-stream.sh >> /tmp/ppf-stream.log 2>&1 &
###############################################################################

# ── Configuration ─────────────────────────────────────────────────────────────
CAMERA_IP="192.168.29.64"
CAMERA_USER="admin"
CAMERA_PASS="Hik@12345"
CAMERA_CHANNEL="102"       # 102 = sub-stream (lower res, better latency)

CLOUD_HOST="ppf-mediamtx.fly.dev"
CLOUD_PORT="8554"
STREAM_PATH="workshop_3_pit_1"

# ── Derived URLs ──────────────────────────────────────────────────────────────
CAMERA_URL="rtsp://${CAMERA_USER}:${CAMERA_PASS}@${CAMERA_IP}:554/Streaming/Channels/${CAMERA_CHANNEL}"
DEST_URL="rtsp://${CLOUD_HOST}:${CLOUD_PORT}/${STREAM_PATH}"

echo "=================================================="
echo "  PPF Workshop Camera → Fly.io MediaMTX Pusher"
echo "=================================================="
echo "  Camera  : ${CAMERA_URL}"
echo "  Pushing : ${DEST_URL}"
echo "  Press Ctrl+C to stop"
echo "=================================================="
echo ""

# ── Auto-restart loop ─────────────────────────────────────────────────────────
while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting stream push..."

    ffmpeg \
        -rtsp_transport tcp \
        -i "${CAMERA_URL}" \
        -c copy \
        -f rtsp \
        -rtsp_transport tcp \
        "${DEST_URL}"

    EXIT_CODE=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ffmpeg exited with code ${EXIT_CODE}. Restarting in 5s..."
    sleep 5
done
