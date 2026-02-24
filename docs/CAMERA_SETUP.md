# Hikvision IP Camera — Network Setup Guide

> **Project:** PPF Workshop Monitoring System
> **Date documented:** 2026-02-24
> **Camera role:** Live video feed per pit → MediaMTX → WebRTC → React Frontend

---

## Camera Details

| Field | Value |
|---|---|
| **Brand** | Hikvision |
| **Resolution** | 1920 × 1080 (1080p) |
| **Connection** | Ethernet → Modem/Router |
| **Factory Default IP** | `192.168.1.64` |
| **Credentials** | `admin / Hik@12345` |
| **Current Static IP** | `192.168.29.64` (set via ISAPI 2026-02-25) |
| **Protocol** | RTSP (port 554) + HTTP web UI (port 80) |

---

## Network Context

| Device | IP | Connection |
|---|---|---|
| Airtel Modem/Router | `192.168.29.1` | — |
| This Laptop | `192.168.29.173` | Wi-Fi (Jas_Mehar_5G) |
| Hikvision Camera | `192.168.29.x` (after setup) | Ethernet → Modem |
| CP Plus DVR (separate) | `192.168.29.157` | Ethernet (DO NOT TOUCH) |

---

## Initial Setup Procedure (One-Time)

The camera ships with a **static IP of `192.168.1.64`** which is on a different subnet
from the home/workshop network (`192.168.29.x`). Follow these steps to bring it online.

### Step 1 — Add Temporary IP Alias (Admin PowerShell)

```powershell
netsh interface ip add address "Wi-Fi" 192.168.1.100 255.255.255.0
```

This gives your laptop a second IP in the `192.168.1.x` range so it can talk to the camera.

### Step 2 — Verify Camera is Reachable

```bash
ping 192.168.1.64
# Expected: replies with ~10-20ms RTT
```

### Step 3 — Open Camera Web UI

Navigate to: `http://192.168.1.64`

- **Username:** `admin`
- **Password:** *(set during activation, or Hikvision default)*

### Step 4 — Change Camera IP to Main Network

In the web UI:
`Configuration → Network → Basic Settings → TCP/IP`

| Setting | Value |
|---|---|
| IP Address Mode | DHCP (recommended) OR Static |
| Static IP (if preferred) | `192.168.29.64` |
| Subnet Mask | `255.255.255.0` |
| Default Gateway | `192.168.29.1` |
| DNS | `8.8.8.8` |

Click **Save** → camera will reboot.

### Step 5 — Remove Temporary IP Alias (Admin PowerShell)

```powershell
netsh interface ip delete address "Wi-Fi" 192.168.1.100 255.255.255.0
```

### Step 6 — Verify on Main Network

```bash
ping 192.168.29.64   # (or whatever IP was assigned)
```

---

## Changing Network (New Internet Connection / New Location)

If you switch to a different ISP, router, or location and the camera becomes unreachable:

1. Add the temp IP alias (Step 1 above) — camera always falls back to `192.168.1.64`
2. Open `http://192.168.1.64` and update the IP settings
3. Remove temp alias (Step 5 above)

> **Key fact:** The camera ALWAYS listens on `192.168.1.64` when it cannot find
> its configured network. This is your permanent recovery address.

---

## RTSP Stream URLs

Once the camera is on the main network (e.g., `192.168.29.64`):

| Stream | URL |
|---|---|
| Main stream (1080p) | `rtsp://admin:PASSWORD@192.168.29.64/Streaming/Channels/101` |
| Sub stream (360p) | `rtsp://admin:PASSWORD@192.168.29.64/Streaming/Channels/102` |
| Alternative path | `rtsp://admin:PASSWORD@192.168.29.64/h264/ch1/main/av_stream` |

---

## MediaMTX Integration

In `docker-compose.yml`, the MediaMTX path for this camera:

```yaml
MTX_PATHS_CAM1_SOURCE: rtsp://admin:PASSWORD@192.168.29.64/Streaming/Channels/101
```

Frontend WebRTC endpoint: `http://localhost:8554/cam1`

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Can't reach camera after network change | Add temp IP alias → access `192.168.1.64` → reconfigure |
| RTSP stream not working | Verify RTSP is enabled: `Configuration → Video/Audio → Video` |
| Web UI not loading | Try port 80 and 443. Some models default to HTTPS |
| Camera offline in dashboard | Check RTSP URL in `docker-compose.yml` matches current IP |
| 401 Unauthorized on RTSP | Check password — some Hikvision models require 8+ char password |

---

*Last updated: 2026-02-24*
