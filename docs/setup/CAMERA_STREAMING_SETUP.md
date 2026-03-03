# Camera Streaming Setup Guide

> Complete guide for setting up camera streaming from Hikvision → Raspberry Pi → Frontend

---

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR NETWORK                             │
│                                                                 │
│  ┌──────────────┐      RTSP       ┌──────────────┐             │
│  │   Hikvision  │ ───────────────→ │  Raspberry   │             │
│  │   Camera     │   Port 554       │     Pi       │             │
│  │ 192.168.29.64│                  │192.168.29.115│             │
│  └──────────────┘                  └──────┬───────┘             │
│                                           │                     │
│                                           │ WebRTC/HLS/RTSP     │
│                                           ↓                     │
│                                    ┌──────────────┐             │
│                                    │   MediaMTX   │             │
│                                    │   Port 8889  │             │
│                                    └──────┬───────┘             │
│                                           │                     │
└───────────────────────────────────────────┼─────────────────────┘
                                            │ WebRTC/HLS
                                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND BROWSER                            │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Video Player                          │   │
│  │         http://192.168.29.115:8889/cam1/whep           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Step-by-Step Setup

### Step 1: Verify Camera is Online

From your laptop or Pi:
```bash
# Ping the camera
ping 192.168.29.64

# Test RTSP stream with VLC or ffplay
vlc rtsp://admin:Hik@12345@192.168.29.64:554/Streaming/Channels/101
```

### Step 2: Configure MediaMTX on Raspberry Pi

The Pi should already have MediaMTX installed. Verify the config:

```bash
ssh pi@192.168.29.115
cat ~/mediamtx-server/mediamtx.yml
```

**Expected config:**
```yaml
paths:
  cam1:
    source: rtsp://admin:Hik@12345@192.168.29.64:554/Streaming/Channels/101
    sourceProtocol: tcp
    sourceOnDemand: yes
  
  cam1-sub:
    source: rtsp://admin:Hik@12345@192.168.29.64:554/Streaming/Channels/102
    sourceProtocol: tcp
    sourceOnDemand: yes
```

### Step 3: Start MediaMTX

```bash
# On the Pi
cd ~/mediamtx-server

# Kill any existing instance
pkill -f mediamtx

# Start MediaMTX
nohup ./mediamtx ./mediamtx.yml > mediamtx.log 2>&1 &

# Verify it's running
ps aux | grep mediamtx
cat mediamtx.log
```

### Step 4: Test Streams

**WebRTC (Lowest latency):**
```
http://192.168.29.115:8889/cam1/whep
```

**HLS (Most compatible):**
```
http://192.168.29.115:8888/cam1/index.m3u8
```

**RTSP (For other players):**
```
rtsp://192.168.29.115:8554/cam1
```

Test in browser:
```
http://localhost:8080/camera-viewer.html
```

---

## 📡 How Camera Registration Works

When Pi connects to WiFi and runs `camera_register.py`:

1. **Pi sends MQTT message** to backend:
```json
{
  "device_id": "pi_camera_01",
  "name": "Raspberry Pi Camera 1",
  "ip_address": "192.168.29.115",
  "workshop_id": 1,
  "stream_urls": {
    "webrtc": {
      "main": "http://192.168.29.115:8889/cam1/whep",
      "sub": "http://192.168.29.115:8889/cam1-sub/whep"
    },
    "hls": {
      "main": "http://192.168.29.115:8888/cam1/index.m3u8",
      "sub": "http://192.168.29.115:8888/cam1-sub/index.m3u8"
    },
    "rtsp": {
      "main": "rtsp://192.168.29.115:8554/cam1",
      "sub": "rtsp://192.168.29.115:8554/cam1-sub"
    }
  }
}
```

2. **Backend stores camera** with these stream URLs

3. **Frontend displays camera** in CamerasPage

4. **User assigns camera to pit** → Stream available in PitDetailPage

---

## 🎥 Stream URL Format in Database

The `stream_urls` JSON field stores:

```json
{
  "webrtc": {
    "main": "http://192.168.29.115:8889/cam1/whep",
    "sub": "http://192.168.29.115:8889/cam1-sub/whep"
  },
  "hls": {
    "main": "http://192.168.29.115:8888/cam1/index.m3u8",
    "sub": "http://192.168.29.115:8888/cam1-sub/index.m3u8"
  },
  "rtsp": {
    "main": "rtsp://192.168.29.115:8554/cam1",
    "sub": "rtsp://192.168.29.115:8554/cam1-sub"
  }
}
```

---

## 🔌 Protocol Comparison

| Protocol | URL | Latency | Browser Support | Use Case |
|----------|-----|---------|-----------------|----------|
| **WebRTC** | `/cam1/whep` | ~500ms | Chrome, Firefox, Safari | Primary - lowest latency |
| **HLS** | `/cam1/index.m3u8` | ~3-5s | All browsers | Fallback - best compatibility |
| **RTSP** | `rtsp://...` | ~1s | VLC, native players | External players |
| **RTMP** | `rtmp://...` | ~2s | Flash, OBS | Legacy support |

---

## 🚀 Quick Start Checklist

### On Raspberry Pi:
```bash
# 1. Connect to WiFi (use the portal)
http://192.168.29.115:8080

# 2. Start MediaMTX
cd ~/mediamtx-server
./mediamtx ./mediamtx.yml &

# 3. Start camera registration
python3 ~/wifi-portal/camera_register.py
```

### On Your Laptop:
```bash
# 1. Run database migration
psql -U ppf_user -d ppf_db -f backend/database/migrations/003_add_cameras_table.sql

# 2. Start backend
cd backend
python -m src.main

# 3. Start frontend
cd frontend
npm run dev

# 4. Open camera viewer
http://localhost:5173/admin/cameras
```

---

## 🔄 Automatic Startup (Make it Permanent)

### MediaMTX Auto-Start:
```bash
# On Pi
sudo tee /etc/systemd/system/mediamtx.service << 'EOF'
[Unit]
Description=MediaMTX Camera Streaming Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/mediamtx-server
ExecStart=/home/pi/mediamtx-server/mediamtx /home/pi/mediamtx-server/mediamtx.yml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable mediamtx
sudo systemctl start mediamtx
```

### Camera Registration Auto-Start:
```bash
sudo tee /etc/systemd/system/camera-register.service << 'EOF'
[Unit]
Description=Camera MQTT Registration Service
After=network.target mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/wifi-portal
ExecStart=/home/pi/wifi-portal/venv/bin/python /home/pi/wifi-portal/camera_register.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable camera-register
sudo systemctl start camera-register
```

---

## 🐛 Troubleshooting

### Camera not streaming?
```bash
# Check MediaMTX logs
tail -f ~/mediamtx-server/mediamtx.log

# Check if camera is reachable from Pi
ping 192.168.29.64

# Test RTSP from Pi
ffplay rtsp://admin:Hik@12345@192.168.29.64:554/Streaming/Channels/101
```

### Stream not loading in browser?
```bash
# Check if ports are open
ss -tlnp | grep -E '8888|8889'

# Check MediaMTX is running
ps aux | grep mediamtx

# Test WebRTC endpoint
curl http://192.168.29.115:8889/cam1/whep
```

### Camera not registering?
```bash
# Check MQTT connection on Pi
tail -f ~/wifi-portal/camera_register.log

# Check backend MQTT logs
# (check your backend console)
```

---

## 📱 Access Points

| Service | URL |
|---------|-----|
| Camera Management | `http://localhost:5173/admin/cameras` |
| WiFi Portal | `http://192.168.29.115:8080` |
| WebRTC Stream | `http://192.168.29.115:8889/cam1/whep` |
| HLS Stream | `http://192.168.29.115:8888/cam1/index.m3u8` |
| MediaMTX API | `http://192.168.29.115:9997` |

---

## 🎯 Summary

1. **Camera** → RTSP → **Pi MediaMTX** (pulls stream)
2. **MediaMTX** → WebRTC/HLS → **Frontend** (serves stream)
3. **Pi** → MQTT → **Backend** (registers camera)
4. **Backend** → WebSocket → **Frontend** (notifies user)
5. **User** assigns camera to pit → Stream appears in pit detail

The owner sees the camera in the Cameras page once the Pi registers it via MQTT! 🎉
