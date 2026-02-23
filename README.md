# PPF Workshop Monitoring System

> **Smart IoT SaaS for Paint Protection Film workshops**
> Real-time environmental monitoring · Job lifecycle tracking · Customer portal

[![Backend Tests](https://img.shields.io/badge/backend%20tests-126%2F126%20✅-brightgreen)](#backend--key-api-endpoints)
[![E2E Tests](https://img.shields.io/badge/playwright%20E2E-live%20✅-brightgreen)](#testing)
[![Firmware](https://img.shields.io/badge/firmware-ESP32%20v1.0.0%20✅-orange)](#3--flash-the-esp32-firmware)
[![Phase](https://img.shields.io/badge/phase-1%20complete%20✅-brightgreen)](#project-status)

---

## What This System Does

PPF workshops apply paint protection film to cars in climate-controlled bays ("pits"). Dust,
temperature, and humidity all affect adhesion quality. This system:

1. **Monitors** each pit continuously via ESP32 sensors (DHT22 / BME680 / PMS5003)
2. **Alerts** owners in real-time when conditions go out of specification
3. **Tracks** every job — creation, staff assignment, status pipeline, customer notification
4. **Lets customers** follow their car's progress via a public tracking link (no login needed)
5. **Streams** live video from each pit via Hikvision camera + MediaMTX

**Business model:** Hardware kit sale (₹16,250/pit) + ₹1,500/pit/month subscription

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│  PPF WORKSHOP (on-site)                                               │
│                                                                       │
│   [ESP32 + DHT22 / BME680 / PMS5003]                                  │
│         │  MQTT publish (QoS 1)                                        │
│         ▼                                                             │
│   [Mosquitto Broker :1883]                                            │
│         │  paho-mqtt subscriber                                        │
│         ▼                                                             │
│   [FastAPI Backend :8000]──────────────────[PostgreSQL :5432]         │
│         │  WebSocket push (/ws)             (sensor history, jobs,    │
│         │  REST API (/api/v1/…)              users, alerts, audit)    │
│         │                                                             │
│   [Hikvision Camera] ──RTSP──▶ [MediaMTX :8554]                      │
│         │                           │  WebRTC WHEP / HLS              │
└─────────┼───────────────────────────┼──────────────────────────────--─┘
          │                           │
          ▼                           ▼
   ┌─────────────────────────────────────┐
   │       React Frontend (:5173)        │
   │  Owner Dashboard · Job Management  │
   │  Customer Tracking (public, no auth)│
   │  Live Video · Alerts · Devices     │
   └─────────────────────────────────────┘
```

**Data flow:** Sensor → MQTT → Backend parser → DB + alert check → WebSocket → React UI

---

## Repository Structure

```
PPF_Factory/
│
├── backend/                    FastAPI application (Python 3.13)
│   ├── src/
│   │   ├── api/routes/         13 route modules (auth, jobs, pits, sensors, WS …)
│   │   ├── models/             13 SQLAlchemy async ORM models
│   │   ├── services/           Business logic (auth, jobs, MQTT, alerts, licensing)
│   │   ├── schemas/            Pydantic v2 request/response models
│   │   └── main.py             App entry point — 13 routers registered
│   ├── tests/                  126 pytest tests (100 % passing)
│   ├── alembic/                Database migration framework
│   ├── database/migrations/    001_initial_schema.sql · 002_seed_sensor_types.sql
│   ├── Dockerfile              Multi-stage build (builder + non-root runtime)
│   └── CHANGELOG.md
│
├── frontend/                   React 18 SPA (TypeScript · Vite 5 · Tailwind CSS v3)
│   ├── src/
│   │   ├── pages/              13 pages (Dashboard, Jobs, Job Detail, Tracking, Admin …)
│   │   ├── components/         40+ reusable components
│   │   ├── store/slices/       Redux Toolkit 2 (auth, jobs, pits, alerts, devices)
│   │   ├── api/                Axios clients with JWT interceptor + 401 auto-refresh
│   │   └── services/websocket.ts  Native WebSocket singleton (exponential back-off)
│   ├── e2e/                    Playwright E2E tests (live demo + full visual walkthrough)
│   ├── tests/                  Interactive demo tests (test.setTimeout(0))
│   └── playwright.config.ts
│
├── firmware/                   ESP32 PlatformIO project (Arduino framework)
│   ├── include/config.h        Per-device provisioning: DEVICE_ID, LICENSE_KEY, WiFi
│   └── src/
│       ├── connectivity/       MQTT handler + network manager (Ethernet / WiFi fallback)
│       ├── sensors/            DHT22 · PMS5003 · BME680 drivers
│       └── utils/              NTP sync · ArduinoJson payload builder
│
├── docker/
│   └── mosquitto/              Mosquitto 2.x config (auth required, ACL ready)
│
├── docs/
│   ├── PROJECT_TASKS.md        Phase tracker & task checklist
│   ├── DEPLOYMENT.md           Production deployment guide
│   └── HARDWARE_SETUP.md       ESP32 wiring, flashing & provisioning guide
│
└── docker-compose.yml          Full stack: PostgreSQL · Mosquitto · MediaMTX · FastAPI · pgAdmin
```

---

## Quick Start

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Docker + Compose v2 | Any recent | Run full backend stack |
| Node.js | 20+ | Frontend dev server |
| Python | 3.13+ | Backend dev (optional — Docker handles prod) |
| PlatformIO | latest | Flash ESP32 firmware (optional) |

---

### 1 · Start the Backend Stack (Docker)

```bash
# Copy environment template and fill in secrets
cp backend/.env.example backend/.env

# Start all services (PostgreSQL, Mosquitto, MediaMTX, FastAPI, pgAdmin)
docker compose up -d

# Run database migrations
docker compose exec backend alembic upgrade head

# Seed sensor types (DHT22, PMS5003, BME680)
docker compose exec db psql -U ppf_user ppf_db \
  -f /docker-entrypoint-initdb.d/002_seed_sensor_types.sql

# Create first super_admin account
curl -X POST http://localhost:8000/api/v1/admin/seed-super-admin
```

Services after startup:

| Service | Port | URL |
|---------|------|-----|
| FastAPI backend | 8000 | http://localhost:8000/docs |
| PostgreSQL | 5432 | (internal) |
| Mosquitto MQTT | 1883 | |
| MediaMTX video | 8554 | rtsp://localhost:8554 |
| pgAdmin | 5050 | http://localhost:5050 |

---

### 2 · Start the Frontend (Dev)

```bash
cd frontend
npm install
npm run dev       # http://localhost:5173
```

Login with `super_admin` / password set in `backend/.env → SUPER_ADMIN_PASSWORD`.

**Production build:**
```bash
npm run build     # output → frontend/dist/ (serve via Nginx)
```

---

### 3 · Flash the ESP32 Firmware

```bash
cd firmware

# Step 1 — Register the device in the backend dashboard first:
#   POST /api/v1/workshops/{id}/devices
#   Copy the returned device_id and license_key

# Step 2 — Edit firmware provisioning
nano include/config.h
# Set: DEVICE_ID, LICENSE_KEY, WORKSHOP_ID, PIT_ID
# Set: WIFI_SSID, WIFI_PASSWORD (or use captive portal on first boot)
# Set: MQTT_BROKER_HOST to your backend server IP

# Step 3 — Build and flash (WiFi testing mode)
pio run -e esp32-gateway-eth --target upload

# Step 4 — Monitor serial
pio device monitor --baud 115200
```

---

## Backend — Key API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/login` | No | Login → JWT token |
| GET | `/api/v1/auth/me` | JWT | Current user profile |
| GET | `/api/v1/workshops/{id}/pits` | Owner | List pits (plain array) |
| POST | `/api/v1/workshops/{id}/jobs` | Owner/Staff | Create job + auto-create customer |
| GET | `/api/v1/jobs/{id}` | Owner/Staff | Full job + status history |
| PATCH | `/api/v1/jobs/{id}/assign-staff` | Owner | Assign staff member |
| POST | `/api/v1/jobs/{id}/status` | Owner/Staff | Status transition (state machine) |
| **GET** | **`/api/v1/track/{token}`** | **None** | **Public customer tracking** |
| GET | `/api/v1/pits/{id}/sensors/latest` | Owner/Staff | Latest sensor readings |
| GET | `/api/v1/pits/{id}/sensors/history` | Owner/Staff | Paginated historical data |
| POST | `/api/v1/devices/{id}/command` | Owner | Send MQTT command to ESP32 |
| WS | `/ws` | JWT (query param) | Real-time push (sensor · job · alert) |
| GET | `/health` | No | DB + MQTT health probe |

Full spec: [`backend/docs/api/API_ENDPOINTS.md`](backend/docs/api/API_ENDPOINTS.md)

---

## Frontend — Pages

| Page | Route | Roles | Description |
|------|-------|-------|-------------|
| Login | `/login` | All | JWT login form |
| Change Password | `/change-password` | All | Forced for `is_temporary_password` accounts |
| Dashboard | `/dashboard` | Owner/Admin | Pit grid with live sensor tiles (30s poll fallback) |
| Pit Detail | `/pits/:id` | Owner | Live sensor °C/% · history charts · video stream |
| Jobs | `/jobs` | Owner/Staff | Job list with status tabs + Create Job modal |
| Job Detail | `/jobs/:id` | Owner/Staff | Status pipeline · **Assign Staff** · Tracking Link · Vehicle |
| **Customer Tracking** | **`/track/:token`** | **None** | Public progress page — vehicle info + ETA countdown |
| Alerts | `/alerts` | Owner/Staff | Alert list + per-alert acknowledge + bulk clear |
| Alert Config | `/alerts/config` | Owner | Custom threshold editor per sensor type |
| Devices | `/devices` | Owner | ESP32 registration · online/offline badge · MQTT commands |
| Staff | `/staff` | Owner | User list + create + temporary password reset |
| Admin | `/admin` | Super Admin | Workshop management · audit log · system metrics |
| Not Found | `/*` | All | 404 page |

---

## Firmware — Sensor Configurations

| Config | Build Flag in `platformio.ini` | Sensors |
|--------|-------------------------------|---------|
| DHT22 only | `-DSENSOR_DHT22_ONLY` | Temperature · Humidity |
| DHT22 + PMS5003 | *(default — production)* | Temp · Humidity · PM1 · PM2.5 · PM10 |
| BME680 | `#define SENSOR_CONFIG_BME680` in `config.h` | Temp · Humidity · Pressure · IAQ |

**Remote commands (MQTT):**

| Command | ESP32 Action |
|---------|-------------|
| `DISABLE` | Stop publishing sensor readings |
| `ENABLE` | Resume publishing |
| `RESTART` | Reboot (hardware WDT: 90 s) |
| `SET_INTERVAL` | Change publish interval (5 s – 1 hr) |
| `UPDATE_FIRMWARE` | **Safe stub in v1** — logs notice, does nothing |

> **OTA Safety Review (v1):**
> The `UPDATE_FIRMWARE` command is an intentional **no-op stub**. The device cannot be bricked
> by this command in the current firmware. When OTA is implemented in v2, the following must
> be addressed: (1) change `platformio.ini` partition scheme from `default.csv` to
> `partitions_ota.csv` to enable dual-app A/B slots; (2) add `esp_https_ota` to `lib_deps`;
> (3) extend or suspend the 90 s watchdog during flash; (4) define a `url` field in the
> `UPDATE_FIRMWARE` MQTT payload; (5) validate firmware signature before applying.

---

## Role-Based Access Control

| Role | Assigned to | Capabilities |
|------|-------------|-------------|
| `super_admin` | Platform owner | All workshops · billing · audit log · seed admin |
| `owner` | Workshop manager | Their workshop — full job + device + staff control |
| `staff` | Technician | Update job status · view sensors · acknowledge alerts |
| `customer` | Car owner | **Public tracking link only** — no account needed |

---

## Environment Variables (`.env`)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL async URL (`postgresql+asyncpg://user:pass@host/db`) |
| `SECRET_KEY` | JWT signing secret (minimum 32 characters) |
| `MQTT_BROKER_HOST` | Mosquitto host (`localhost` for local, server IP for prod) |
| `MQTT_USERNAME` | Backend MQTT user (`ppf_backend`) |
| `MQTT_PASSWORD` | Backend MQTT password |
| `SUPER_ADMIN_PASSWORD` | Initial super-admin password |
| `REDIS_URL` | Optional — for token blacklist (Phase 2) |

---

## Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| Dashboard | `super_admin` | from `SUPER_ADMIN_PASSWORD` in `.env` |
| Mosquitto (backend) | `ppf_backend` | from `MQTT_PASSWORD` in `.env` |

---

## Testing

### Backend — pytest
```bash
cd backend
pytest --tb=short -q          # 126 tests — all pass
```

### Frontend — Playwright E2E
```bash
cd frontend
npx playwright test                                    # All tests (tests/ + e2e/)
npx playwright test e2e/full_visual_demo.spec.ts       # Full 13-page visual walkthrough
npx playwright test e2e/live_demo_execution.spec.ts    # Live ESP32 + webcam demo
npx playwright test tests/interactive_demo.spec.ts     # Interactive pause demo (no timeout)
```

**Mocked smoke tests (8/8 ✅):** Login, invalid creds, dashboard redirect, create job, job detail, tracking link copy, customer portal, invalid token.

**Live E2E demo (✅ verified 2026-02-24):** Full MQTT chain — ESP32 → Mosquitto → Backend → DB → WebSocket → React UI. Temperature/humidity confirmed live at 28–31°C / 58–70%.

**Full visual walkthrough (✅ 23 screenshots):** Every page walked through with `slowMo:500`. Screenshots saved to `frontend/screenshots/wave-2/`.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI 0.115 · SQLAlchemy 2 (async) · PostgreSQL 16 · Alembic · Pydantic v2 |
| Auth | JWT HS256 · bcrypt cost-12 · role-based dependency guards |
| Real-time | paho-mqtt (backend) · PubSubClient (ESP32) · native WebSocket (FastAPI↔React) |
| Frontend | React 18 · Vite 5 · TypeScript 5 · Redux Toolkit 2 · Tailwind CSS v3 |
| Video | MediaMTX · WebRTC WHEP (primary) · HLS (fallback) · Video.js 8 |
| Firmware | Arduino/ESP-IDF · PlatformIO · ArduinoJson 6 · WiFiManager |
| Infrastructure | Docker Compose · Mosquitto 2 · pgAdmin 4 |
| Testing | pytest 126 backend · Playwright 8 E2E |

---

## Project Status

| Phase | Status | Notes |
|-------|--------|-------|
| 1-A Backend Foundation | ✅ Complete | 13 models · JWT · MQTT · WebSocket |
| 1-B API Routes | ✅ Complete | 23 endpoints |
| 1-C Services | ✅ Complete | All business logic |
| 1-D Backend Tests | ✅ **126/126** | 100 % passing (Python 3.13 compatible) |
| 1-E ESP32 Firmware | ✅ Complete | DHT22 + PMS5003 + BME680 + OTA stub |
| 1-F Docker Stack | ✅ 95 % | Missing: SSL certs (production) |
| 1-G Frontend | ✅ Complete | 13 pages · 40+ components · WebSocket |
| 1-H E2E + Demo Prep | ✅ Complete | Live E2E demo · full visual walkthrough · MQTT chain verified |
| 2 · Production Deploy | ❌ Not started | DigitalOcean + SSL + hardware order |
| 3 · Franchise Scale | ❌ Not started | Multi-tenant self-service onboarding |

---

## Known Issues

No open bugs. All Phase 1 issues resolved.

| ID | Component | Description | Resolution |
|----|-----------|-------------|------------|
| ~~BUG-001~~ | Frontend · Job Detail | Staff assignment UI missing on `/jobs/:id` | ✅ Fixed 2026-02-24 — checkbox multi-select sidebar card added |
| ~~BUG-002~~ | Playwright · Tests | `interactive_demo.spec.ts` timed out at 30s | ✅ Fixed 2026-02-24 — `test.setTimeout(0)` applied |

---

## Documentation

| Document | Location | Status |
|----------|----------|--------|
| API Endpoints | [`backend/docs/api/API_ENDPOINTS.md`](backend/docs/api/API_ENDPOINTS.md) | ✅ |
| Database Design | [`backend/docs/database/DATABASE_DESIGN.md`](backend/docs/database/DATABASE_DESIGN.md) | ✅ |
| Firmware Guide | [`firmware/README.md`](firmware/README.md) | ✅ |
| Frontend Guide | [`frontend/README.md`](frontend/README.md) | ✅ |
| Deployment Guide | [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | ✅ |
| Hardware Setup | [`docs/HARDWARE_SETUP.md`](docs/HARDWARE_SETUP.md) | ✅ |
| Task Tracker | [`docs/PROJECT_TASKS.md`](docs/PROJECT_TASKS.md) | ✅ |
| Backend Changelog | [`backend/CHANGELOG.md`](backend/CHANGELOG.md) | ✅ |

---

## Hardware BOM — 1 Pit (MVP)

| Component | Model | Cost (INR) |
|-----------|-------|-----------|
| Microcontroller | Olimex ESP32-GATEWAY-EA | ₹2,800 |
| Environmental sensor | BME680 breakout | ₹800 |
| Particulate sensor | PMS5003 | *(bundled in alt. kit)* |
| Camera | Hikvision DS-2CD1023G0-I (2 MP) | ₹3,500 |
| PoE switch | 5-port unmanaged | ₹2,500 |
| Router (VPN-capable) | Any OpenWRT-compatible | ₹2,000 |
| Cabling + mounting | — | ₹650 |
| **Total per pit** | | **₹16,250** |

**Unit economics:**
- Hardware selling price: ₹12,000 → margin: ₹4,250/kit (55 %)
- Monthly subscription: ₹1,500 · Cloud cost: ~₹800 · **Net: ₹700/pit/month (47 %)**
- Break-even: 3 workshops · Year-1 target: 10 workshops × 30 pits = ₹7,92,000/yr

---

*PPF Monitoring Team · Phase 1 Complete ✅ · 2026-02-24*
