# PPF Monitoring System - Deployment Guide

> **Complete deployment instructions for Online (Production) and Local (Development) environments.**
> 
> **Last Updated:** 2026-03-07

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Online Deployment (Production)](#2-online-deployment-production)
3. [Local Development Setup](#3-local-development-setup)
4. [Environment Variables Reference](#4-environment-variables-reference)
5. [Database Setup Requirements](#5-database-setup-requirements)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Architecture Overview

### Production Architecture (Online)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER BROWSER                                    │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │ HTTPS
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VERCEL FRONTEND                                     │
│              https://ppf-monitoring.vercel.app                              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │ API Calls (CORS enabled)
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RENDER BACKEND                                      │
│              https://ppf-backend-w0aq.onrender.com                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │  FastAPI    │  │   MQTT      │  │  Database   │                         │
│  │   Server    │◄─┤  Subscriber │  │   Client    │                         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                         │
└─────────┼────────────────┼────────────────┼────────────────────────────────┘
          │                │                │
          │          MQTT/TLS              PostgreSQL
          │        (Port 8883)         (Neon Database)
          │                │                │
          │                ▼                │
          │    ┌─────────────────────┐      │
          │    │   HIVEMQ CLOUD      │      │
          │    │  MQTT BROKER        │      │
          │    └──────────┬──────────┘      │
          │               │                 │
          │          MQTT/TLS              │
          └───────────────┘                │
                          ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      RASPBERRY PI DEVICES                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   piwifi        │  │   piwifi2       │  │   piwifi3       │             │
│  │  (Sensors)      │  │  (Camera)       │  │  (Camera)       │             │
│  │  192.168.29.115 │  │  192.168.29.68  │  │  192.168.29.212 │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Services Map

| Service | Provider | URL/Credentials | Purpose |
|---------|----------|-----------------|---------|
| **Frontend** | Vercel | `https://ppf-monitoring.vercel.app` | React web UI |
| **Backend** | Render | `https://ppf-backend-w0aq.onrender.com` | FastAPI server |
| **Database** | Neon | PostgreSQL (see `.env.credentials`) | Data storage |
| **MQTT Broker** | HiveMQ Cloud | `c4cb4d2b4a3e432c9d61b8b56ee359af.s1.eu.hivemq.cloud:8883` | Message broker |
| **VPN** | Tailscale | `piwifi.taile42746.ts.net` | Remote Pi access |

---

## 2. Online Deployment (Production)

### 2.1 Prerequisites

1. **Vercel Account** - For frontend hosting
2. **Render Account** - For backend hosting
3. **Neon Database** - For PostgreSQL
4. **HiveMQ Cloud** - For MQTT broker

### 2.2 Step-by-Step Deployment

#### Step 1: Neon Database Setup

1. Create a project at [neon.tech](https://neon.tech)
2. Create database `neondb`
3. Save the connection string (looks like):
   ```
   postgresql://neondb_owner:PASSWORD@ep-xxxxx-pooler.c-3.us-east-2.aws.neon.tech:5432/neondb
   ```
4. **IMPORTANT:** The backend will auto-create tables via Alembic migrations

#### Step 2: HiveMQ Cloud Setup

1. Create free cluster at [console.hivemq.cloud](https://console.hivemq.cloud)
2. Create credentials:
   - **Username:** `ppf_backend`
   - **Password:** `PPF@Mqtt2026!secure`
3. Enable TLS (port 8883)
4. Note the cluster URL (e.g., `xxx.s1.eu.hivemq.cloud`)

#### Step 3: Render Backend Deployment

1. Fork/push this repo to GitHub
2. In Render Dashboard:
   - Click "New Web Service"
   - Connect your GitHub repo
   - Select branch: `master`
3. Configure service:
   
   | Setting | Value |
   |---------|-------|
   | **Name** | `ppf-backend` |
   | **Runtime** | Python 3 |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn src.main:app --host 0.0.0.0 --port $PORT --workers 2` |
   | **Root Directory** | `backend` |

4. Add **Environment Variables** (see Section 4 for complete list):

   ```bash
   DATABASE_URL=postgresql://neondb_owner:PASSWORD@ep-xxxxx.aws.neon.tech:5432/neondb
   MQTT_BROKER_HOST=xxx.s1.eu.hivemq.cloud
   MQTT_BROKER_PORT=8883
   MQTT_USE_TLS=true
   MQTT_USERNAME=ppf_backend
   MQTT_PASSWORD=PPF@Mqtt2026!secure
   JWT_SECRET_KEY=your-64-char-secret-key-here
   # ... (see Section 4 for ALL variables)
   ```

5. Deploy and verify: `https://ppf-backend-w0aq.onrender.com/health`

#### Step 4: Vercel Frontend Deployment

1. In Vercel Dashboard:
   - Click "New Project"
   - Import from GitHub
2. Configure:
   
   | Setting | Value |
   |---------|-------|
   | **Framework** | Vite |
   | **Root Directory** | `frontend` |
   | **Build Command** | `npm run build` |
   | **Output Directory** | `dist` |

3. Add **Environment Variables**:
   
   ```bash
   VITE_API_BASE_URL=https://ppf-backend-w0aq.onrender.com/api/v1
   VITE_WS_URL=wss://ppf-backend-w0aq.onrender.com/ws
   ```

4. Deploy and verify: `https://ppf-monitoring.vercel.app`

#### Step 5: Database Device Registration (CRITICAL)

**⚠️ IMPORTANT:** For each Raspberry Pi device, you MUST manually create database entries:

```sql
-- 1. Create the device record
INSERT INTO devices (device_id, license_key, status, workshop_id, pit_id, is_online)
VALUES ('PIWIFI-01', 'LIC-RG-STUDIO-2026', 'active', 2, 3, false);

-- 2. Create subscription record (REQUIRED - device won't work without this!)
INSERT INTO subscriptions (workshop_id, device_id, license_key, plan, status, monthly_fee, currency, grace_period_days)
VALUES (2, 'PIWIFI-01', 'LIC-RG-STUDIO-2026', 'trial', 'active', 0, 'INR', 7);
```

**Without the subscription record, the backend will reject all sensor data!**

---

## 3. Local Development Setup

### 3.1 Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (local or Docker)
- MQTT Broker (Mosquitto or HiveMQ)

### 3.2 Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create local .env file
cat > .env << 'EOF'
# Database (Local PostgreSQL)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ppf_local

# MQTT (Local Mosquitto or use HiveMQ Cloud)
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USE_TLS=false
MQTT_USERNAME=
MQTT_PASSWORD=

# Auth
JWT_SECRET_KEY=local-dev-secret-key-32-chars-min
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# Other
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
EOF

# 5. Run database migrations
cd ..
python backend/scripts/setup/setup_db.py

# 6. Start the server
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3.3 Frontend Setup

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Create local .env file
cat > .env << 'EOF'
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
EOF

# 4. Start development server
npm run dev
```

### 3.4 Local MQTT Broker (Optional)

```bash
# Using Docker for local MQTT
docker run -d --name mosquitto \
  -p 1883:1883 \
  -p 9001:9001 \
  eclipse-mosquitto

# Or install on Mac
brew install mosquitto
brew services start mosquitto
```

### 3.5 Local Database Setup

```bash
# Using Docker for local PostgreSQL
docker run -d --name ppf-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=ppf_local \
  -p 5432:5432 \
  postgres:15

# Connect and create tables
psql postgresql://postgres:postgres@localhost:5432/ppf_local
```

---

## 4. Environment Variables Reference

### Backend Environment Variables

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| **DATABASE_URL** | ✅ | `postgresql://...` | Neon PostgreSQL connection string |
| **MQTT_BROKER_HOST** | ✅ | `xxx.hivemq.cloud` | MQTT broker hostname |
| **MQTT_BROKER_PORT** | ✅ | `8883` | MQTT port (8883 for TLS, 1883 for plain) |
| **MQTT_USE_TLS** | ✅ | `true` | Enable TLS for MQTT |
| **MQTT_USERNAME** | ✅ | `ppf_backend` | MQTT username |
| **MQTT_PASSWORD** | ✅ | `PPF@...` | MQTT password |
| **JWT_SECRET_KEY** | ✅ | `64-char-hex` | Secret for JWT tokens (min 32 chars) |
| **JWT_ALGORITHM** | ❌ | `HS256` | JWT algorithm (default: HS256) |
| **ENVIRONMENT** | ✅ | `production` | `production`, `staging`, or `development` |
| **BACKEND_BASE_URL** | ✅ | `https://...` | Public backend URL |
| **MEDIAMTX_PUBLIC_URL** | ❌ | `https://piwifi...` | MediaMTX public URL |
| **CORS_ORIGINS** | ✅ | JSON array | Allowed frontend origins |
| **SUPER_ADMIN_PASSWORD** | ✅ | `SuperAdmin@123` | Initial admin password |

### Frontend Environment Variables

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| **VITE_API_BASE_URL** | ✅ | `https://.../api/v1` | Backend API URL |
| **VITE_WS_URL** | ✅ | `wss://.../ws` | WebSocket URL |

### Raspberry Pi Configuration

| Variable | Location | Example | Description |
|----------|----------|---------|-------------|
| **DEVICE_ID** | `pi_sensor_mqtt.py` | `PIWIFI-01` | Unique device identifier |
| **LICENSE_KEY** | `pi_sensor_mqtt.py` | `LIC-RG-STUDIO-2026` | Must match database |
| **WORKSHOP_ID** | `pi_sensor_mqtt.py` | `2` | Workshop assignment |
| **PIT_ID** | `pi_sensor_mqtt.py` | `3` | Pit assignment |
| **MQTT_BROKER** | `pi_sensor_mqtt.py` | `xxx.hivemq.cloud` | Same as backend |
| **MQTT_USER** | `pi_sensor_mqtt.py` | `ppf_backend` | MQTT username |
| **MQTT_PASS** | `pi_sensor_mqtt.py` | `PPF@...` | MQTT password |

---

## 5. Database Setup Requirements

### 5.1 Required Tables (Auto-created by Alembic)

The backend automatically creates all tables. You only need to insert device and subscription records.

### 5.2 Manual Device Registration (SQL)

For each new Raspberry Pi sensor device, execute:

```sql
-- Insert device
INSERT INTO devices (
    device_id, 
    license_key, 
    status, 
    workshop_id, 
    pit_id, 
    is_online,
    mac_address,
    firmware_version
) VALUES (
    'PIWIFI-01',           -- Matches DEVICE_ID in pi_sensor_mqtt.py
    'LIC-RG-STUDIO-2026',  -- Matches LICENSE_KEY in pi_sensor_mqtt.py
    'active',              -- 'active', 'pending', 'disabled'
    2,                     -- Workshop ID from workshops table
    3,                     -- Pit ID from pits table
    false,                 -- Will be set true when device connects
    '88:a2:9e:69:f1:3f',   -- Pi MAC address
    '1.0.0'                -- Firmware version
);

-- Insert subscription (REQUIRED!)
INSERT INTO subscriptions (
    workshop_id,
    device_id,
    license_key,
    plan,
    status,
    monthly_fee,
    currency,
    grace_period_days
) VALUES (
    2,
    'PIWIFI-01',
    'LIC-RG-STUDIO-2026',
    'trial',      -- 'trial', 'basic', 'standard', 'premium'
    'active',     -- 'active', 'suspended', 'expired'
    0,            -- Monthly fee in INR (0 for trial)
    'INR',
    7             -- Grace period days
);
```

### 5.3 Verification Queries

```sql
-- Check device and subscription
SELECT 
    d.device_id,
    d.license_key,
    d.status as device_status,
    d.is_online,
    d.last_seen,
    s.plan,
    s.status as subscription_status
FROM devices d
LEFT JOIN subscriptions s ON d.device_id = s.device_id
WHERE d.device_id = 'PIWIFI-01';

-- Should show:
-- device_id | license_key        | device_status | is_online | last_seen | plan  | subscription_status
-- PIWIFI-01 | LIC-RG-STUDIO-2026 | active        | t         | 2026-...  | trial | active
```

---

## 6. Troubleshooting

### 6.1 Device Shows Offline in Dashboard

**Checklist:**

1. **Is Pi publishing to MQTT?**
   ```bash
   # On Pi
   sudo journalctl -u pi-sensors -f
   # Should show: "Published: T=27.5°C, H=60%, PM2.5=100"
   ```

2. **Is backend receiving MQTT?**
   ```bash
   curl https://ppf-backend-w0aq.onrender.com/health
   # Should show: "mqtt_broker": "connected"
   ```

3. **Does device exist in database?**
   ```sql
   SELECT * FROM devices WHERE device_id = 'PIWIFI-01';
   ```

4. **Does subscription exist?**
   ```sql
   SELECT * FROM subscriptions WHERE device_id = 'PIWIFI-01';
   -- MUST return 1 row!
   ```

5. **Check Render logs for errors**
   - Go to Render Dashboard → ppf-backend → Logs
   - Look for: "Invalid license", "Subscription expired", etc.

### 6.2 Backend Returns 404

- **Wrong URL:** Use `https://ppf-backend-w0aq.onrender.com` (with `-w0aq`)
- **Service sleeping:** Wake it up by visiting the URL
- **Deployment failed:** Check Render Dashboard for build errors

### 6.3 MQTT Connection Failed

```bash
# Test MQTT connection from local machine
python3 << 'EOF'
import paho.mqtt.client as mqtt
import ssl

client = mqtt.Client()
client.username_pw_set("ppf_backend", "PPF@Mqtt2026!secure")
client.tls_set()
client.connect("xxx.hivemq.cloud", 8883, 60)
print("Connected!")
EOF
```

### 6.4 CORS Errors in Browser

- Ensure `CORS_ORIGINS` in backend includes your Vercel domain
- Check browser console for exact error message
- Verify `VITE_API_BASE_URL` points to correct backend

---

## Quick Reference

### URLs

| Service | Production | Local |
|---------|------------|-------|
| Frontend | `https://ppf-monitoring.vercel.app` | `http://localhost:5173` |
| Backend | `https://ppf-backend-w0aq.onrender.com` | `http://localhost:8000` |
| API Docs | `/docs` (if DEBUG=true) | `/docs` |
| Health | `/health` | `/health` |

### Common Commands

```bash
# Check all services
curl https://ppf-backend-w0aq.onrender.com/health

# SSH into Pi
ssh pi@piwifi.local

# Check Pi sensors
sudo journalctl -u pi-sensors -f

# Restart Pi sensor service
sudo systemctl restart pi-sensors

# Check database
psql $DATABASE_URL -c "SELECT * FROM devices;"
```
