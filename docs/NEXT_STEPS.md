# NEXT STEPS — Continue on a New Machine

> Read this first when pulling this repo on any new system.
> Everything you need to resume exactly where we left off.

---

## Current State (as of 2026-02-25)

| Layer | Status |
|---|---|
| Backend (FastAPI + PostgreSQL + MQTT) | ✅ Phase 1 complete — all 126 tests passing |
| Frontend (React 18 + Vite) | ✅ Phase 1 complete — 13 pages |
| ESP32 Firmware | ✅ Flashed and live — sending real sensor data |
| Hikvision Camera | ✅ Configured — RTSP live via MediaMTX |
| Database | ✅ Clean slate — super_admin only (wiped 2026-02-25 for fresh demo) |
| Phase 2 (Production Deploy) | ❌ Not started — next major milestone |

---

## Hardware on This Setup

### Hikvision IP Camera
| Field | Value |
|---|---|
| IP | `192.168.29.64` (static) |
| Credentials | `admin / Hik@12345` |
| RTSP Main (1080p) | `rtsp://admin:Hik@12345@192.168.29.64/Streaming/Channels/101` |
| RTSP Sub (WebRTC) | `rtsp://admin:Hik@12345@192.168.29.64/Streaming/Channels/102` |
| MediaMTX Path | `workshop_1_pit_1` |
| Recovery (if unreachable) | Add temp alias (admin PS): `netsh interface ip add address "Wi-Fi" 192.168.1.100 255.255.255.0` → access `http://192.168.1.64` |

### ESP32 Device
| Field | Value |
|---|---|
| MAC Address | `08:3A:F2:A9:F0:84` |
| Device ID | `ESP32-083AF2A9F084` |
| License Key | `LIC-KTI6-Q10T-Y24C` |
| MQTT Broker | `192.168.137.1:1883` (Windows Mobile Hotspot IP — always fixed) |
| MQTT User | `ppf_backend` |
| Connected via | Mobile Hotspot (`LAPTOP-U2GTVCR8 5179`) |
| Pit assignment | Workshop 33 / Pit 27 (old DB — re-register after DB wipe) |

### CP Plus DVR (separate — do NOT touch)
| Field | Value |
|---|---|
| IP | `192.168.29.157` |
| Note | Legacy device — not part of this project |

### Network
| Device | IP |
|---|---|
| Airtel Modem/Router | `192.168.29.1` |
| This Laptop (Wi-Fi) | `192.168.29.173` (DHCP) |
| Mobile Hotspot adapter | `192.168.137.1` (fixed) |
| Hikvision Camera | `192.168.29.64` (static) |

---

## Step-by-Step: Start Everything on This Machine

### 1 — Start Docker Stack
```bash
cd D:/Meharban/PPF_Factory
docker compose up -d
```

### 2 — Verify Backend is Healthy
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","components":{"database":"connected","mqtt_broker":"connected"}}
```

### 3 — Seed Super Admin (only if DB was wiped)
```bash
curl -X POST http://localhost:8000/api/v1/admin/seed-super-admin
```
Login: `super_admin / SuperAdmin@123`

### 4 — Start Frontend
```bash
cd frontend
npm run dev
# Opens at http://localhost:5173
```

### 5 — Verify Camera Stream
```bash
# RTSP check
ffprobe -v error rtsp://admin:Hik@12345@192.168.29.64/Streaming/Channels/101

# HLS via MediaMTX (after someone views the pit page)
curl http://localhost:8888/workshop_1_pit_1/index.m3u8
```

### 6 — Verify ESP32 is Sending Data
```bash
# Watch MQTT live
docker exec -it ppf_mosquitto mosquitto_sub \
  -h localhost -p 1883 \
  -u ppf_backend -P "BsW0mmVr5CoDAzW21ibADB7t-kM" \
  -t "workshop/#" -v
```

---

## Step-by-Step: Start on a NEW Machine (fresh pull)

### 1 — Prerequisites
```
Docker Desktop, Node.js 20+, Python 3.13+
```

### 2 — Clone and Configure
```bash
git clone <repo-url>
cd PPF_Factory
cp backend/.env.example backend/.env
# Edit backend/.env — fill in DATABASE_PASSWORD, SECRET_KEY, MQTT passwords
```

### 3 — Start Stack
```bash
docker compose up -d
docker compose exec backend alembic upgrade head
docker compose exec db psql -U ppf_user ppf_monitoring \
  -f /docker-entrypoint-initdb.d/002_seed_sensor_types.sql
curl -X POST http://localhost:8000/api/v1/admin/seed-super-admin
```

### 4 — Camera on New Network
The Hikvision camera has a **static IP of `192.168.29.64`** — only works on the Airtel modem network.
On a new network, recover via factory default:
```powershell
# Admin PowerShell
netsh interface ip add address "Wi-Fi" 192.168.1.100 255.255.255.0
# Then open http://192.168.1.64 in browser → reconfigure IP
```

### 5 — ESP32 on New Network
The ESP32 connects to the **Windows Mobile Hotspot** at `192.168.137.1`.
- Hotspot SSID: `LAPTOP-U2GTVCR8 5179`
- Hotspot Password: `6w0)177M`
- MQTT Broker: always `192.168.137.1:1883` (hotspot adapter IP never changes)
- If on a different machine: update `MQTT_BROKER_HOST` in `firmware/include/config.h` to new hotspot IP, then reflash.

---

## What Was Done in the Last Session (2026-02-25)

1. ✅ Discovered and activated Hikvision camera via Playwright
2. ✅ Changed camera IP from `192.168.1.64` → `192.168.29.64` via ISAPI
3. ✅ Verified RTSP stream: H.264 1920×1080
4. ✅ Configured MediaMTX to pull camera stream on-demand
5. ✅ Fixed Docker networking (`extra_hosts: host.docker.internal:host-gateway`)
6. ✅ Ran Wave 3 E2E Playwright test — 1/1 passed, 23 screenshots
7. ✅ Wiped DB clean — fresh slate for real demo
8. ✅ Re-seeded super_admin

## What to Do Next (One-to-One Test)

The user wants to do a **one-to-one real demo test** with:
- Live Hikvision camera video feed in the pit detail page
- Live ESP32 sensor data (temperature + humidity) from mobile hotspot
- Full user journey: create workshop → add pit → register ESP32 → watch live

**Step order the user will guide:**
1. Create a new Owner user from super_admin Staff panel
2. Create a Workshop
3. Add a Pit (link to Hikvision camera)
4. Register ESP32 device (update firmware license key)
5. Watch live sensors + camera on pit detail page
6. Test full job workflow end to end

---

## Credentials Quick Reference

| Service | User | Password |
|---|---|---|
| App login | `super_admin` | `SuperAdmin@123` |
| Hikvision camera | `admin` | `Hik@12345` |
| MQTT broker | `ppf_backend` | `BsW0mmVr5CoDAzW21ibADB7t-kM` |
| PostgreSQL | `ppf_user` | see `backend/.env` |

---

*Last updated: 2026-02-25 — Wave 3 complete, DB wiped, ready for live demo*
