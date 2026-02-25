#!/bin/bash
###############################################################################
# run_camera.sh — Hikvision Camera Viewer for PPF Monitoring
#
# Camera: Hikvision DS-2CD @ 192.168.29.64 (static, same WiFi LAN)
# Credentials: admin / Hik@12345
#
# Usage:
#   ./scripts/run_camera.sh              # Interactive menu
#   ./scripts/run_camera.sh check        # Connectivity check only
#   ./scripts/run_camera.sh main         # View main stream (1080p)
#   ./scripts/run_camera.sh sub          # View sub stream (lower res)
#   ./scripts/run_camera.sh hls          # Start MediaMTX + open HLS in browser
#   ./scripts/run_camera.sh snapshot     # Grab a JPEG snapshot
#   ./scripts/run_camera.sh web          # Open camera web UI in browser
###############################################################################

set -euo pipefail

# ─── Camera Config ──────────────────────────────────────────────────────────
CAM_IP="192.168.29.64"
CAM_USER="admin"
CAM_PASS="Hik@12345"
CAM_PORT="554"

RTSP_MAIN="rtsp://${CAM_USER}:${CAM_PASS}@${CAM_IP}:${CAM_PORT}/Streaming/Channels/101"
RTSP_SUB="rtsp://${CAM_USER}:${CAM_PASS}@${CAM_IP}:${CAM_PORT}/Streaming/Channels/102"
SNAPSHOT_URL="http://${CAM_USER}:${CAM_PASS}@${CAM_IP}/ISAPI/Streaming/channels/101/picture"
WEB_UI="http://${CAM_IP}"

SNAPSHOT_DIR="$(cd "$(dirname "$0")/.." && pwd)/screenshots/camera"

# ─── Colors ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ─── Helpers ────────────────────────────────────────────────────────────────
info()    { echo -e "${CYAN}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail()    { echo -e "${RED}[FAIL]${NC} $*"; }

check_tool() {
    if command -v "$1" &>/dev/null; then
        return 0
    else
        return 1
    fi
}

# ─── 1. Connectivity Check ─────────────────────────────────────────────────
do_check() {
    echo ""
    echo "============================================"
    echo "  Hikvision Camera Connectivity Check"
    echo "  IP: ${CAM_IP}"
    echo "============================================"
    echo ""

    # Ping test
    info "Pinging camera at ${CAM_IP}..."
    if ping -c 2 -W 2 "${CAM_IP}" &>/dev/null; then
        success "Camera is reachable on the network"
    else
        fail "Camera not reachable at ${CAM_IP}"
        echo ""
        warn "Troubleshooting:"
        echo "  1. Make sure you're on the same WiFi (Airtel Modem: 192.168.29.1)"
        echo "  2. Check camera is powered on and LAN cable is connected"
        echo "  3. Try accessing http://${CAM_IP} in your browser"
        return 1
    fi

    # HTTP check (camera web UI)
    info "Checking camera web interface..."
    if curl -sf --connect-timeout 5 "http://${CAM_IP}" -o /dev/null 2>/dev/null; then
        success "Camera web UI is responding at http://${CAM_IP}"
    else
        warn "Camera web UI not responding (might need HTTPS or different port)"
    fi

    # RTSP check
    info "Checking RTSP stream..."
    if check_tool ffprobe; then
        if ffprobe -v error -rtsp_transport tcp -i "${RTSP_SUB}" -show_entries stream=codec_name,width,height -of csv=p=0 2>/dev/null; then
            success "RTSP stream is live!"
        else
            warn "RTSP stream not responding (camera may need a moment to start)"
        fi
    else
        warn "ffprobe not installed — install FFmpeg to test RTSP"
        echo "  brew install ffmpeg"
    fi

    # ISAPI snapshot check
    info "Checking ISAPI snapshot endpoint..."
    HTTP_CODE=$(curl -sf --connect-timeout 5 -o /dev/null -w "%{http_code}" \
        "http://${CAM_USER}:${CAM_PASS}@${CAM_IP}/ISAPI/System/deviceInfo" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        success "ISAPI is accessible — credentials are correct"
    elif [ "$HTTP_CODE" = "401" ]; then
        fail "ISAPI returned 401 — check credentials"
    else
        warn "ISAPI returned HTTP ${HTTP_CODE}"
    fi

    echo ""
    success "Connectivity check complete"
}

# ─── 2. View Main Stream (1080p) ───────────────────────────────────────────
do_main() {
    info "Opening MAIN stream (1080p) from ${CAM_IP}..."

    if check_tool ffplay; then
        info "Using ffplay..."
        ffplay -rtsp_transport tcp \
            -window_title "Hikvision Main Stream (1080p)" \
            -loglevel warning \
            "${RTSP_MAIN}"
    elif check_tool vlc; then
        info "Using VLC..."
        vlc --rtsp-tcp "${RTSP_MAIN}" &
    elif check_tool mpv; then
        info "Using mpv..."
        mpv --rtsp-transport=tcp "${RTSP_MAIN}"
    else
        fail "No video player found. Install one of:"
        echo "  brew install ffmpeg    (provides ffplay)"
        echo "  brew install --cask vlc"
        echo "  brew install mpv"
        return 1
    fi
}

# ─── 3. View Sub Stream (lower resolution) ─────────────────────────────────
do_sub() {
    info "Opening SUB stream (lower res, good for WebRTC) from ${CAM_IP}..."

    if check_tool ffplay; then
        info "Using ffplay..."
        ffplay -rtsp_transport tcp \
            -window_title "Hikvision Sub Stream" \
            -loglevel warning \
            "${RTSP_SUB}"
    elif check_tool vlc; then
        info "Using VLC..."
        vlc --rtsp-tcp "${RTSP_SUB}" &
    elif check_tool mpv; then
        info "Using mpv..."
        mpv --rtsp-transport=tcp "${RTSP_SUB}"
    else
        fail "No video player found. Install one of:"
        echo "  brew install ffmpeg    (provides ffplay)"
        echo "  brew install --cask vlc"
        echo "  brew install mpv"
        return 1
    fi
}

# ─── 4. HLS via MediaMTX (Docker) ──────────────────────────────────────────
do_hls() {
    PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

    info "Starting MediaMTX via Docker for HLS streaming..."

    # Check if MediaMTX container is already running
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "ppf_mediamtx"; then
        success "MediaMTX is already running"
    else
        info "Starting MediaMTX container..."
        docker compose -f "${PROJECT_ROOT}/docker-compose.yml" up -d mediamtx
        sleep 3
        if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "ppf_mediamtx"; then
            success "MediaMTX started"
        else
            fail "Failed to start MediaMTX"
            return 1
        fi
    fi

    echo ""
    success "Camera streams available at:"
    echo ""
    echo "  HLS (browser):    http://localhost:8888/workshop_1_pit_1/"
    echo "  WebRTC (browser): http://localhost:8889/workshop_1_pit_1/"
    echo "  RTSP (player):    rtsp://localhost:8554/workshop_1_pit_1"
    echo ""

    # Open HLS in default browser
    info "Opening HLS stream in browser..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "http://localhost:8889/workshop_1_pit_1/"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "http://localhost:8889/workshop_1_pit_1/" 2>/dev/null || echo "Open http://localhost:8889/workshop_1_pit_1/ in your browser"
    fi

    echo ""
    info "MediaMTX logs:"
    docker logs --tail 20 ppf_mediamtx 2>&1 | tail -10
}

# ─── 5. Grab a JPEG Snapshot ───────────────────────────────────────────────
do_snapshot() {
    mkdir -p "${SNAPSHOT_DIR}"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    OUTFILE="${SNAPSHOT_DIR}/snapshot_${TIMESTAMP}.jpg"

    info "Grabbing snapshot from camera..."

    # Try ISAPI endpoint first (fast, native JPEG)
    if curl -sf --connect-timeout 5 \
        -o "${OUTFILE}" \
        "${SNAPSHOT_URL}" 2>/dev/null; then
        success "Snapshot saved: ${OUTFILE}"
        # Open it
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open "${OUTFILE}"
        fi
        return 0
    fi

    # Fallback: grab a frame from RTSP via ffmpeg
    if check_tool ffmpeg; then
        info "ISAPI snapshot failed, trying ffmpeg RTSP grab..."
        ffmpeg -rtsp_transport tcp -i "${RTSP_MAIN}" \
            -frames:v 1 -y \
            -loglevel warning \
            "${OUTFILE}" 2>/dev/null
        if [ -f "${OUTFILE}" ]; then
            success "Snapshot saved: ${OUTFILE}"
            if [[ "$OSTYPE" == "darwin"* ]]; then
                open "${OUTFILE}"
            fi
            return 0
        fi
    fi

    fail "Could not grab snapshot"
    return 1
}

# ─── 6. Open Camera Web UI ─────────────────────────────────────────────────
do_web() {
    info "Opening camera web UI at ${WEB_UI}..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "${WEB_UI}"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "${WEB_UI}" 2>/dev/null
    fi
    echo ""
    echo "  Credentials: ${CAM_USER} / ${CAM_PASS}"
}

# ─── Interactive Menu ───────────────────────────────────────────────────────
do_menu() {
    echo ""
    echo "============================================"
    echo "  Hikvision Camera — PPF Monitoring"
    echo "  Camera IP: ${CAM_IP}"
    echo "============================================"
    echo ""
    echo "  1) Check connectivity"
    echo "  2) View MAIN stream (1080p via ffplay/VLC)"
    echo "  3) View SUB stream (lower res via ffplay/VLC)"
    echo "  4) Start MediaMTX + open in browser (HLS/WebRTC)"
    echo "  5) Grab a JPEG snapshot"
    echo "  6) Open camera web UI in browser"
    echo "  q) Quit"
    echo ""
    read -rp "Choose [1-6, q]: " choice
    case "$choice" in
        1) do_check ;;
        2) do_main ;;
        3) do_sub ;;
        4) do_hls ;;
        5) do_snapshot ;;
        6) do_web ;;
        q|Q) echo "Bye!"; exit 0 ;;
        *) fail "Invalid choice"; do_menu ;;
    esac
}

# ─── Main ───────────────────────────────────────────────────────────────────
case "${1:-menu}" in
    check)    do_check ;;
    main)     do_main ;;
    sub)      do_sub ;;
    hls)      do_hls ;;
    snapshot) do_snapshot ;;
    web)      do_web ;;
    menu)     do_menu ;;
    *)
        echo "Usage: $0 {check|main|sub|hls|snapshot|web|menu}"
        exit 1
        ;;
esac
