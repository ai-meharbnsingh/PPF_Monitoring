# PPF Workshop Monitor — Frontend

React + TypeScript + Vite single-page application for the PPF Workshop Monitoring System.

> **Phase 1 Complete** · 13 pages · 40+ components · Redux Toolkit 2 · Native WebSocket
> Last Updated: 2026-02-24

---

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| React | 18 | UI framework |
| TypeScript | 5 | Type safety |
| Vite | 5 | Build tool / dev server |
| Redux Toolkit | 2 | Global state (auth, jobs, pits, alerts, devices) |
| React Router | 6 | Client-side routing (lazy-loaded pages) |
| Axios | latest | API client with JWT interceptor + 401 queue |
| Native WebSocket | — | Real-time sensor/job/alert events (exponential backoff, 25s ping) |
| Tailwind CSS | v3 | Utility-first styling + custom `card` / `sidebar` classes |
| Video.js | 8 | WebRTC WHEP player → HLS fallback |
| Recharts | 2 | Sensor history charts |
| React Hook Form | 7 | Form validation (login, job create, alert config) |
| react-hot-toast | 2 | Toast notifications |
| Lucide React | latest | Icon set |

---

## Getting Started

### Prerequisites

- Node.js ≥ 18
- Backend API running on `http://localhost:8000` (start with `docker compose up -d` from repo root)

### Install dependencies

```bash
npm install
```

### Run development server

```bash
npm run dev   # http://localhost:5173
```

### Build for production

```bash
npm run build    # output → dist/
npm run preview  # preview production build locally
```

---

## Environment Variables

Create `frontend/.env.local` (not committed):

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
VITE_MEDIAMTX_HOST=localhost
```

The Vite dev proxy in `vite.config.ts` forwards `/api` requests to the backend automatically — no `.env.local` needed for local development.

---

## Login

Use the `super_admin` account — password is set in `backend/.env` via `SUPER_ADMIN_PASSWORD`.
See [`docs/HARDWARE_SETUP.md`](../docs/HARDWARE_SETUP.md) or the root [`README.md`](../README.md) for first-run setup.

> **Security note:** Never hardcode credentials in source files. Always use `.env` / `.env.local`.

---

## Pages (13 total)

| Page | Route | Auth | Description |
|------|-------|------|-------------|
| Login | `/login` | No | JWT login form |
| Change Password | `/change-password` | JWT | Forced redirect for `is_temporary_password` accounts |
| Dashboard | `/dashboard` | Owner/Admin | Pit grid with live sensor tiles — 30s poll fallback |
| Pit Detail | `/pits/:id` | Owner | Live °C/% readings · sensor history charts · video stream |
| Jobs | `/jobs` | Owner/Staff | Job list with status filter tabs + Create Job modal |
| Job Detail | `/jobs/:id` | Owner/Staff | Status pipeline · Assign Staff · Copy Tracking Link · Vehicle |
| Customer Tracking | `/track/:token` | **None** | Public — vehicle info + job progress + ETA countdown |
| Alerts | `/alerts` | Owner/Staff | Alert list + per-alert acknowledge + bulk clear |
| Alert Config | `/alerts/config` | Owner | Threshold editor (PM2.5, PM10, temp, humidity, IAQ) |
| Devices | `/devices` | Owner | ESP32 list · online/offline badge · MQTT commands modal |
| Staff | `/staff` | Owner | User list + create staff + admin password reset |
| Admin | `/admin` | Super Admin | Workshop management · paginated audit log · system metrics |
| Not Found | `/*` | — | 404 fallback |

---

## Project Structure

```
src/
├── api/                 Axios API client functions (one file per resource)
│   ├── client.ts        Axios instance — JWT interceptor + 401 auto-refresh queue
│   ├── auth.ts          login, me, change-password
│   ├── jobs.ts          list, create, getJob, updateStatus, assignStaff
│   ├── pits.ts          list, getPit
│   ├── sensors.ts       latest, history, stats
│   ├── devices.ts       list, register, update, sendCommand
│   ├── workshops.ts     list, create, update, delete
│   ├── alerts.ts        list, acknowledge, acknowledgeAll
│   ├── users.ts         list, create, update, resetPassword, deactivate
│   ├── streams.ts       getStreamUrls
│   └── tracking.ts      getByToken (public, no auth)
│
├── components/
│   ├── alerts/          AlertBell, AlertItem, AlertPanel, AlertSeverityBadge
│   ├── auth/            ProtectedRoute, RoleGuard
│   ├── devices/         DeviceCard, DeviceCommandModal, DeviceRegisterModal
│   ├── jobs/            JobCard, JobCreateModal, JobStatusBadge, JobStatusFlow, JobTimeline
│   ├── layout/          AppLayout, Sidebar, Topbar
│   ├── sensors/         SensorCard, SensorHistoryChart
│   ├── ui/              Button, Card, Spinner, Modal, Pagination, Badge, etc.
│   └── video/           StreamTokenLoader, VideoPlayer (Video.js WebRTC/HLS)
│
├── hooks/               useAppDispatch, useAppSelector
│
├── pages/               One file per route (lazy-loaded via React.lazy)
│
├── services/
│   └── websocket.ts     Native WebSocket singleton — exponential backoff, 25s ping
│
├── store/
│   ├── index.ts         Redux store setup
│   └── slices/
│       ├── authSlice.ts      JWT token + user profile (persisted to localStorage)
│       ├── jobsSlice.ts      Job list + currentJob
│       ├── pitsSlice.ts      Pit list + sensorMap (keyed by pitId)
│       ├── alertsSlice.ts    Alert list + unread count
│       └── devicesSlice.ts   Device list + online/offline state
│
├── types/               TypeScript interfaces mirroring backend Pydantic schemas
│   ├── auth.ts, common.ts, job.ts, pit.ts, sensor.ts
│   ├── alert.ts, device.ts, user.ts, stream.ts, websocket.ts
│   └── index.ts         Barrel re-export
│
└── utils/               formatters.ts · constants.ts · sensor colour helpers
```

---

## Real-Time (WebSocket)

The `websocket.ts` service connects to `ws://localhost:8000/ws?token=<JWT>` and dispatches Redux actions for:

| Event | Action |
|-------|--------|
| `sensor_update` | Updates `pitsSlice.sensorMap[pitId]` |
| `job_status` | Updates `jobsSlice` |
| `alert` | `toast.error()` + `alertsSlice.newAlertReceived` |
| `device_offline` / `device_online` | Updates `devicesSlice` |

Reconnect strategy: exponential backoff (1s → 2s → 4s … max 30s) with a 25s keep-alive ping.

---

## E2E Testing (Playwright)

```bash
# Run all tests (tests/ + e2e/ — both directories scanned)
npx playwright test

# Full 13-page visual walkthrough (slowMo: 500ms, headless: false)
npx playwright test e2e/full_visual_demo.spec.ts

# Live ESP32 + MQTT + WebSocket chain verification
npx playwright test e2e/live_demo_execution.spec.ts

# Interactive demo with manual pause (no timeout)
npx playwright test tests/interactive_demo.spec.ts
```

Screenshots are saved to `screenshots/wave-2/` after each run (ATO §4.3 compliant).

**Results (2026-02-24):**
- Mocked smoke tests: **8/8 ✅**
- Live MQTT chain: **✅ verified** — 28–31°C / 58–70% from real sensor pump
- Full visual walkthrough: **13/13 pages ✅** — 23 screenshots captured

---

*PPF Monitoring Team · Phase 1 Complete ✅ · 2026-02-24*
