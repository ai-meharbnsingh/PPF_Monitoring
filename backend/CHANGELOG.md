# Changelog
## Smart PPF Workshop Monitoring System — Backend

All notable changes are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/)

---

## [Unreleased]

### Pending
- Production deployment (DigitalOcean / VPS, SSL, domain)
- Phase 2: SMS/email notifications (Twilio, SendGrid)
- Phase 2: BME680 IAQ sensor support upgrade
- Phase 2: Multi-workshop admin dashboard

---

## [2026-02-24] — v0.4.0 — Phase 1 Complete (E2E Verified)

### Added
- **Full E2E Playwright test suite** (`frontend/e2e/full_visual_demo.spec.ts`) — 13-page visual walkthrough, slowMo:500, 23 screenshots captured to `screenshots/wave-2/`
- **Live MQTT chain verification** (`frontend/e2e/live_demo_execution.spec.ts`) — ESP32 → Mosquitto → FastAPI → PostgreSQL → WebSocket → React confirmed end-to-end
- **Interactive demo test** (`frontend/tests/interactive_demo.spec.ts`) — `test.setTimeout(0)` for unbounded `page.pause()` flow

### Fixed
- **BUG-001:** Staff Assignment UI missing on Job Detail page — added multi-select checkbox card with `RoleGuard(owner/super_admin)`, pre-populated from `assigned_staff_ids`, saves via `POST /jobs/{id}/assign-staff`
- **BUG-002:** Playwright interactive demo timing out at 30s — resolved by adding `test.setTimeout(0)` before `page.pause()` call

### Changed
- **`frontend/playwright.config.ts`** — Switched from `testDir: './tests'` to `testMatch: ['tests/**/*.spec.ts', 'e2e/**/*.spec.ts']` to scan both test directories
- **`firmware/include/config.h`** — Updated with live device credentials: `ESP32-083AF2A9F084` / `LIC-KTI6-Q10T-Y24C` / Workshop 33 / Pit 27
- **`frontend/README.md`** — Complete rewrite: removed hardcoded credentials, corrected tech stack, added full 13-page route table, WebSocket events table, E2E section
- **`README.md`** (root) — Updated badges, 13-page count, resolved known issues table, expanded testing section, Phase 1 Complete footer

### Verified (2026-02-24)
- Backend: **126/126 pytest tests passing**
- Frontend mocked smoke tests: **8/8 passing**
- Live MQTT chain: **✅** — 28–31°C / 58–70% from real ESP32 sensor pump
- Full visual walkthrough: **13/13 pages ✅** — 23 screenshots captured

---

## [2026-02-22] — v0.3.0 — React Frontend (Full SPA)

### Added

**Frontend application at `D:\Meharban\PPF_Factory\frontend\`**

Built with: **React 18 + Vite 5 + TypeScript 5 + Tailwind CSS v3 + Redux Toolkit 2 + React Router v6**

---

### Frontend Setup Instructions

#### Prerequisites
- Node.js ≥ 18 and npm ≥ 9
- Backend running at `http://localhost:8000` (see backend setup below)

#### 1 — Install dependencies
```bash
cd D:\Meharban\PPF_Factory\frontend
npm install
```

#### 2 — Environment variables
A `.env.local` file already exists with all required variables:
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
VITE_MEDIAMTX_HOST=localhost
VITE_MEDIAMTX_WEBRTC_PORT=8889
VITE_MEDIAMTX_HLS_PORT=8888
VITE_ENABLE_VIDEO=true
VITE_ENABLE_CHARTS=true
```
Copy `.env.example` and adjust values for different environments.

#### 3 — Start the development server
```bash
npm run dev
# Opens at http://localhost:5173
```

The Vite dev server proxies `/api` → `http://localhost:8000` and `/ws` → `ws://localhost:8000`,
so no CORS configuration is needed during development.

#### 4 — Build for production
```bash
npm run build
# Output at frontend/dist/
```

---

### Backend Setup (reminder)

#### Prerequisites
- Python 3.11+
- PostgreSQL 15+ running locally or via Docker
- (Optional) Mosquitto MQTT broker on port 1883
- (Optional) MediaMTX for video streaming

#### 1 — Python environment
```bash
cd D:\Meharban\PPF_Factory\backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

#### 2 — Environment variables
```bash
copy .env.example .env
# Edit .env — set DATABASE_URL, SECRET_KEY, MQTT_HOST etc.
```
Minimum required keys in `.env`:
```
DATABASE_URL=postgresql+asyncpg://ppf_user:password@localhost:5432/ppf_factory
SYNC_DATABASE_URL=postgresql+psycopg2://ppf_user:password@localhost:5432/ppf_factory
SECRET_KEY=<random 64-char hex — run: python -c "import secrets; print(secrets.token_hex(32))">
```

#### 3 — Database migrations
```bash
# First time only — create and apply migrations
alembic revision --autogenerate -m "initial"
alembic upgrade head

# Apply existing migrations (after pulling from git)
alembic upgrade head
```

#### 4 — Seed super admin
```bash
# POST /api/v1/admin/seed-super-admin (first run only)
# Or call from Python:
python -c "
import asyncio, httpx
asyncio.run(httpx.AsyncClient().post('http://localhost:8000/api/v1/admin/seed-super-admin'))
"
```

#### 5 — Start the backend
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---

### Full Stack Startup Order

```
1. PostgreSQL         (localhost:5432)
2. MQTT broker        (localhost:1883)   — optional for dev
3. MediaMTX           (localhost:8889)   — optional for dev
4. Backend            uvicorn src.main:app --reload --port 8000
5. Frontend           npm run dev  (from frontend/)
```

---

### Frontend Architecture

| Layer | Technology |
|---|---|
| Build | Vite 5 + TypeScript 5 |
| Styling | Tailwind CSS v3 |
| State | Redux Toolkit 2 (5 slices: auth, pits, jobs, alerts, devices) |
| Routing | React Router v6 `createBrowserRouter` |
| HTTP | Axios 1.7 — JWT Bearer interceptor + 401 auto-refresh (queue pattern) |
| Real-time | Native Browser WebSocket — reconnects with exponential backoff |
| Video | Video.js 8 — WebRTC WHEP primary → hls.js fallback |
| Charts | Recharts 2 — LineChart with 1h/6h/24h/7d range tabs |
| Forms | React Hook Form 7 |
| Notifications | react-hot-toast |
| Icons | Lucide React |
| Dates | date-fns |

### Pages / Routes

| Route | Page | Access |
|---|---|---|
| `/login` | LoginPage | Public |
| `/change-password` | ChangePasswordPage | Authenticated |
| `/track/:token` | TrackingPage | Public (no auth) |
| `/` | DashboardPage | All roles |
| `/pits/:pitId` | PitDetailPage | All roles |
| `/jobs` | JobsPage | All roles |
| `/jobs/:jobId` | JobDetailPage | All roles |
| `/alerts` | AlertsPage | All roles |
| `/alerts/config` | AlertConfigPage | owner, super_admin |
| `/devices` | DevicesPage | owner, super_admin |
| `/staff` | StaffPage | owner, super_admin |
| `*` | NotFoundPage | — |

### Key Implementation Notes

- **Token refresh:** Body field is `{ access_token: string }` — matches FastAPI `POST /auth/refresh-token`
- **Auth rehydration:** Token + user stored in `localStorage` under `ppf_token` / `ppf_user` — restored on page reload
- **Temp password redirect:** `is_temporary_password === true` forces `/change-password` via `ProtectedRoute`
- **WS subscription:** On connect, sends `{ action: "subscribe_workshop", workshop_id }` — required to receive events
- **Sensor card borders:** Border colour = worst sensor status across all metrics in that pit (critical=red, warning=amber, good=emerald)
- **Job transitions:** `ALLOWED_TRANSITIONS` in `src/types/common.ts` mirrors backend `JOB_STATUS_TRANSITIONS` — only valid next states shown as buttons
- **Public tracking:** Uses a separate Axios instance with no auth interceptor (`src/api/tracking.ts`)
- **Video offline:** If `camera_is_online === false`, shows placeholder card immediately without attempting stream fetch

---

## [2026-02-22] — v0.2.0 — Complete Backend

### Added

**Pydantic Schemas (`src/schemas/`):**
- `common.py` — PaginatedResponse, SuccessResponse, ErrorResponse, build_paginated()
- `auth.py` — LoginRequest, ChangePasswordRequest, TokenRefreshRequest, LoginResponse, UserProfileResponse
- `workshop.py` — WorkshopCreate, WorkshopUpdate, WorkshopSummary, WorkshopResponse
- `pit.py` — PitCreate, PitUpdate, PitSummary, PitResponse (with embedded DeviceSummaryInPit)
- `device.py` — DeviceRegister, DeviceUpdate, DeviceCommandRequest, SensorTypeResponse, DeviceResponse, DeviceCommandResponse
- `sensor_data.py` — SensorReadingResponse, LatestSensorSummary, SensorStatsResponse (DHT22+PMS5003+BME680 all nullable)
- `job.py` — JobCreate, JobStatusUpdate, JobAssignStaff, JobSummary, JobResponse, JobTrackingResponse, JobStatusHistoryResponse
- `alert.py` — AlertAcknowledgeRequest, AlertConfigUpdate, AlertResponse, AlertConfigResponse
- `user.py` — UserCreate, UserUpdate, AdminResetPassword, UserSummary, UserResponse, CustomerCreateResponse
- `subscription.py` — SubscriptionCreate, SubscriptionUpdate, RecordPayment, SubscriptionSummary, SubscriptionResponse
- `stream.py` — StreamTokenResponse, PitStreamStatus

**Supporting Services (`src/services/`):**
- `workshop_service.py` — Workshop CRUD, unique slug generation, auto AlertConfig creation on workshop create
- `device_service.py` — Device registration (sensor type resolution, auto subscription), update, MQTT command dispatch
- `job_service.py` — Full job lifecycle: create, JOB_STATUS_TRANSITIONS validation, staff assign, customer auto-create, view token tracking
- `notification_service.py` — SMS via Twilio (feature-flagged), email stub for Phase 2, dispatch_alert_notifications()

**API Route Files (`src/api/routes/`):**
- `workshops.py` — GET/POST/PATCH/DELETE /workshops; role-scoped access
- `pits.py` — Full CRUD under /workshops/{id}/pits with active-job guard on delete
- `devices.py` — Register, update, list, command dispatch; workshop-scoped
- `sensors.py` — Latest per-pit readings (dashboard), paginated history, aggregate stats (avg/min/max over N hours)
- `jobs.py` — Create, status transitions, staff assign, job progress %, public customer tracking (/track/{token})
- `users.py` — Create staff/owner, update, admin password reset, deactivate; self-view allowed
- `alerts.py` — Alert list/detail/acknowledge/bulk-acknowledge, AlertConfig get/PATCH
- `streams.py` — MediaMTX stream token generation with RTSP/WebRTC/HLS URLs, stream status check
- `subscriptions.py` — Create/update subscriptions, record payments with device auto-re-enable
- `admin.py` — Seed super admin, system info snapshot, paginated audit log

**Package Init Files:**
- All `__init__.py` files for: src, src/api, src/api/routes, src/config, src/models, src/schemas, src/services, src/utils

**Testing Infrastructure (`tests/`):**
- `conftest.py` — In-memory SQLite DB, async test client, pre-seeded user fixtures (super_admin/owner/staff), JWT token/header helpers
- `tests/unit/test_auth_service.py` — bcrypt hashing, JWT create/decode/tamper detection, password strength validation
- `tests/unit/test_helpers.py` — All utility functions: license key format, device ID, slugs, sensor status eval, job progress computation
- `tests/integration/test_auth_endpoints.py` — Login success/fail, /me auth, /health endpoint

**Alembic Migration Framework:**
- `alembic.ini` — Alembic config
- `alembic/env.py` — Imports all ORM models, uses SYNC_DATABASE_URL from settings, compare_type=True
- `alembic/script.py.mako` — Migration file template

**Scripts:**
- `scripts/setup/install.sh` — venv creation, pip install, .env setup, logs dir, guided next-steps

**Updated:**
- `src/main.py` — All 10 route routers registered (workshops, pits, devices, sensors, jobs, users, alerts, streams, subscriptions, admin)

### Architecture Decisions
- **Thin routes, fat services:** All DB logic lives in services/; routes only validate + delegate
- **Lazy imports for circular deps:** `device_service.py` imports mqtt_service inside function body to avoid circular import
- **Soft deletes everywhere:** Users and workshops are deactivated, not hard-deleted
- **Job status machine:** `JOB_STATUS_TRANSITIONS` dict in constants.py is the single source of truth for allowed transitions; validated in `job_service.update_job_status`
- **Customer account auto-creation:** `job_service.create_job` creates customer User if `customer_name` provided and no matching phone/email exists
- **Subscription auto-created with device:** `device_service.register_device` creates a TRIAL subscription automatically
- **Sensor thresholds from AlertConfig, fallback to settings defaults:** sensor routes load AlertConfig per workshop; fall back to WHO 2021 defaults if not found

---

## [2026-02-21] — v0.1.0 — Backend Foundation

### Added

**Documentation:**
- `docs/database/DATABASE_DESIGN.md` — Complete 13-table schema design with sensor hardware strategy
- `docs/api/API_ENDPOINTS.md` — Full REST API + WebSocket endpoint specification

**Project Structure:**
- Full directory scaffold per claude.md.md standards (src/, tests/, docs/, config/, database/, scripts/)
- All `__init__.py` files for Python package structure

**Configuration:**
- `config/settings.yaml` — All application settings (no hardcoded values)
- `.env.example` — Environment variable template (secrets never committed)
- `.gitignore` — Comprehensive exclusion list
- `requirements.txt` — All Python dependencies pinned to versions

**Database Layer:**
- `src/config/database.py` — Async SQLAlchemy engine, session factory, get_db dependency
- `src/models/base.py` — TimestampMixin for created_at/updated_at
- `src/models/workshop.py` — Workshop ORM model (top-level tenant)
- `src/models/user.py` — User ORM model (super_admin, owner, staff, customer)
- `src/models/pit.py` — Pit ORM model with camera configuration
- `src/models/device.py` — Device ORM model with sensor type configuration + SensorType reference
- `src/models/sensor_data.py` — Time-series sensor data model (DHT22+PMS5003 AND BME680 support)
- `src/models/job.py` — Job and JobStatusHistory ORM models
- `src/models/alert.py` — Alert and AlertConfig ORM models
- `src/models/subscription.py` — Subscription ORM model (licensing/kill-switch)
- `src/models/device_command.py` — DeviceCommand ORM model
- `src/models/audit_log.py` — AuditLog ORM model
- `database/migrations/001_initial_schema.sql` — Full schema SQL migration
- `database/migrations/002_seed_sensor_types.sql` — Sensor type seed data

**Application Core:**
- `src/config/settings.py` — Centralised Settings class (pydantic-settings, YAML + .env)
- `src/utils/logger.py` — Loguru-based logger with file rotation
- `src/utils/constants.py` — All enums: UserRole, JobStatus, AlertType, DeviceCommand, etc.
- `src/utils/helpers.py` — Pure utility functions: license key gen, sensor status eval, etc.
- `src/main.py` — FastAPI app with CORS, lifespan (MQTT start/stop), route registration

**Services:**
- `src/services/auth_service.py` — JWT creation/validation, bcrypt password hashing
- `src/services/license_service.py` — ESP32 license key validation (kill-switch trigger)
- `src/services/sensor_service.py` — Sensor data parsing, storage, alert evaluation
- `src/services/mqtt_service.py` — MQTT subscriber (paho-mqtt), device command publisher
- `src/services/websocket_service.py` — WebSocket connection manager, broadcast helpers

**API Routes:**
- `src/api/dependencies.py` — FastAPI dependencies: get_current_user, require_roles, require_workshop_access
- `src/api/routes/auth.py` — POST /auth/login, /logout, /me, /change-password, /refresh-token
- `src/api/routes/websocket.py` — WS /ws (real-time sensor + job + alert events)
- `src/api/routes/health.py` — GET /health, GET /metrics

### Architecture Decisions
- **Sensor flexibility:** sensor_data table supports DHT22+PMS5003 AND BME680 via nullable columns. Switching sensors requires no schema migration.
- **No hardcoded values:** All thresholds, timeouts, intervals from config/settings.yaml
- **Fail-fast error handling:** No bare except blocks. All errors logged with context before re-raising.
- **Denormalized workshop_id on sensor_data:** Avoids JOIN on every dashboard query (performance)
- **MQTT on background thread:** paho-mqtt runs loop on separate thread; submits async work to FastAPI's event loop via asyncio.run_coroutine_threadsafe

---

## Legend
- **Added** — New features
- **Changed** — Changes to existing features
- **Fixed** — Bug fixes
- **Removed** — Removed features
- **Security** — Security fixes
- **Deprecated** — Soon-to-be removed features
