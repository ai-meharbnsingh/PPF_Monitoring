# PPF Workshop Monitor — Frontend

React + TypeScript + Vite single-page application for the PPF Workshop Monitoring System.

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| React | 18 | UI framework |
| TypeScript | 5 | Type safety |
| Vite | 5 | Build tool / dev server |
| Redux Toolkit | 2 | Global state management |
| React Router | 6 | Client-side routing |
| Axios | latest | API client |
| TanStack Query | 5 | Server state / caching |
| Socket.IO Client | 4 | Real-time WebSocket events |
| Recharts | 2 | Sensor history charts |
| React Webcam | 7 | Live camera for demo mode |
| Lucide React | latest | Icon set |
| react-hot-toast | 2 | Toast notifications |

## Getting Started

### Prerequisites

- Node.js ≥ 18
- Backend API running on `http://localhost:8000`

### Install dependencies

```bash
npm install
```

### Run development server

```bash
npm run dev
```

The app starts on `http://localhost:5173` (Vite auto-assigns next available port if in use).

### Build for production

```bash
npm run build
```

Output is written to `dist/`.

### Preview production build

```bash
npm run preview
```

## Project Structure

```
src/
├── api/          # Axios API client functions (one file per resource)
├── components/   # Reusable UI components
│   ├── auth/     # ProtectedRoute, RoleGuard
│   ├── devices/  # DeviceCard, DeviceCommandModal, DeviceRegisterModal
│   ├── jobs/     # JobCard, JobCreateModal, JobStatusBadge
│   ├── layout/   # AppLayout, Sidebar, Header
│   ├── sensors/  # SensorTile, SensorHistoryChart
│   ├── ui/       # Button, Card, Spinner, Modal, Pagination, etc.
│   └── video/    # StreamTokenLoader, VideoPlayer
├── hooks/        # Custom React hooks
├── pages/        # Route-level page components
├── store/        # Redux slices and store configuration
├── types/        # TypeScript type definitions
└── utils/        # Formatting, sensor colour helpers, constants
```

## Environment

The dev proxy is configured in `vite.config.ts` to forward `/api` requests to `http://localhost:8000`.

## Login

Default super-admin credentials (from backend `.env`):

| Field | Value |
|-------|-------|
| Username | `super_admin` |
| Password | `4grZStIoPAX11CEEymamBw` |
