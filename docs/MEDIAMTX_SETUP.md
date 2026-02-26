# MediaMTX Video Streaming — Setup Guide

This document covers deploying [MediaMTX](https://github.com/bluenviron/mediamtx) for RTSP-to-WebRTC video streaming in the PPF Monitoring System.

## Architecture

```
IP Camera (RTSP) → MediaMTX (VPS) → WebRTC → Browser (PitDetailPage)
ESP32-CAM (RTSP) ↗
```

The backend (`streams.py`) generates short-lived JWT tokens for stream authentication. The frontend `StreamTokenLoader` component connects to MediaMTX's WebRTC endpoint.

---

## VPS Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 vCPU | 4 vCPU |
| RAM | 2 GB | 4 GB |
| Bandwidth | 10 Mbps per stream | 20 Mbps per stream |
| OS | Ubuntu 22.04+ | Ubuntu 24.04 |

### Required Ports

| Port | Protocol | Purpose |
|------|----------|---------|
| 8554 | TCP | RTSP (inbound camera feeds) |
| 8889 | TCP | WebRTC (browser playback) |
| 8888 | TCP | HLS fallback |
| 443 | TCP | HTTPS reverse proxy |

---

## Installation

```bash
# Download latest release
MEDIAMTX_VERSION=v1.9.3
wget https://github.com/bluenviron/mediamtx/releases/download/${MEDIAMTX_VERSION}/mediamtx_${MEDIAMTX_VERSION}_linux_amd64.tar.gz
tar -xzf mediamtx_${MEDIAMTX_VERSION}_linux_amd64.tar.gz
sudo mv mediamtx /usr/local/bin/
sudo mv mediamtx.yml /etc/mediamtx/
```

---

## Configuration (`/etc/mediamtx/mediamtx.yml`)

```yaml
# General
logLevel: info
logDestinations: [stdout]

# RTSP server (cameras push streams here)
rtsp: yes
rtspAddress: :8554
protocols: [tcp]

# WebRTC (browser playback)
webrtc: yes
webrtcAddress: :8889

# HLS fallback
hls: yes
hlsAddress: :8888

# Authentication (JWT-based, validated by our backend)
# externalAuthenticationURL: https://your-api.example.com/api/v1/streams/validate-token

# Per-path configuration
paths:
  # Pattern: workshop-{id}/pit-{number}
  workshop~1~d+/pit~1~d+:
    source: publisher
    sourceOnDemand: yes
    sourceOnDemandStartTimeout: 10s
    sourceOnDemandCloseAfter: 30s
```

---

## Camera Configuration

### IP Camera (RTSP Source)

Add the camera's RTSP URL to the pit config in the admin panel:
- **Camera IP**: `192.168.29.64`
- **RTSP URL**: `rtsp://admin:password@192.168.29.64:554/stream1`

### ESP32-CAM

Configure the ESP32-CAM to push its stream to MediaMTX:
```
RTSP Target: rtsp://<mediamtx-host>:8554/workshop-1/pit-1
```

---

## Backend Environment Variables

Add these to your backend `.env`:

```bash
MEDIAMTX_HOST=stream.your-domain.com
MEDIAMTX_RTSP_PORT=8554
MEDIAMTX_WEBRTC_PORT=8889
MEDIAMTX_API_PORT=9997
STREAM_TOKEN_SECRET=your-jwt-secret-here
```

---

## Nginx Reverse Proxy (TLS)

```nginx
server {
    listen 443 ssl http2;
    server_name stream.your-domain.com;

    ssl_certificate     /etc/letsencrypt/live/stream.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/stream.your-domain.com/privkey.pem;

    # WebRTC endpoint
    location /webrtc/ {
        proxy_pass http://127.0.0.1:8889/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # HLS fallback
    location /hls/ {
        proxy_pass http://127.0.0.1:8888/;
    }
}
```

---

## Systemd Service

```ini
# /etc/systemd/system/mediamtx.service
[Unit]
Description=MediaMTX RTSP Server
After=network.target

[Service]
ExecStart=/usr/local/bin/mediamtx /etc/mediamtx/mediamtx.yml
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable mediamtx
sudo systemctl start mediamtx
sudo systemctl status mediamtx
```

---

## Testing

### VLC
```
vlc rtsp://<mediamtx-host>:8554/workshop-1/pit-1
```

### Browser (WebRTC)
Navigate to a pit detail page in the PPF dashboard. The `StreamTokenLoader` component will automatically request a token from the backend and connect to the WebRTC endpoint.

### API Test
```bash
curl -X POST https://your-api.example.com/api/v1/streams/token \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{"pit_id": 1}'
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No video in browser | Check WebRTC port 8889 is open, camera is pushing to correct path |
| Stream lag > 3s | Reduce camera resolution/bitrate, check VPS bandwidth |
| Camera disconnects | Set `sourceOnDemandStartTimeout` higher in mediamtx.yml |
| CORS errors | Ensure nginx passes correct headers, check MEDIAMTX_HOST env var |
