# Environment Variables Reference

> **Complete reference for ALL environment variables used in the PPF Monitoring System**
> 
> **Last Updated:** 2026-03-07

---

## Backend Environment Variables

### Database Configuration (Required)

| Variable | Required | Default | Example | Description |
|----------|----------|---------|---------|-------------|
| `DATABASE_URL` | ✅ | - | `postgresql+asyncpg://user:pass@host/db` | Full async database URL |
| `SYNC_DATABASE_URL` | ✅ (for Render) | - | `postgresql+psycopg2://user:pass@host/db` | Synchronous URL for Alembic |

### MQTT Configuration (Required)

| Variable | Required | Default | Example | Description |
|----------|----------|---------|---------|-------------|
| `MQTT_BROKER_HOST` | ✅ | - | `c4cb4d2b4a3e432c9d61b8b56ee359af.s1.eu.hivemq.cloud` | MQTT broker hostname |
| `MQTT_BROKER_PORT` | ❌ | `1883` | `8883` | MQTT port (8883 for TLS) |
| `MQTT_USERNAME` | ✅ | - | `ppf_backend` | MQTT authentication username |
| `MQTT_PASSWORD` | ✅ | - | `PPF@Mqtt2026!secure` | MQTT authentication password |
| `MQTT_USE_TLS` | ❌ | `false` | `true` | Enable TLS encryption |
| `MQTT_KEEPALIVE` | ❌ | `60` | `60` | Keepalive interval in seconds |
| `MQTT_QOS` | ❌ | `1` | `1` | Quality of Service level (0, 1, or 2) |
| `MQTT_RECONNECT_DELAY` | ❌ | `5` | `5` | Reconnection delay in seconds |

### JWT / Authentication (Required)

| Variable | Required | Default | Example | Description |
|----------|----------|---------|---------|-------------|
| `JWT_SECRET_KEY` | ✅ | - | `c8c5643b8e7e83e49f859c44c8206a56fe7f567da340b0f62233fb226699b099` | Secret key for JWT signing (min 32 chars) |
| `JWT_ALGORITHM` | ❌ | `HS256` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_HOURS` | ❌ | `24` | `24` | Access token expiry (hours) |
| `OWNER_TOKEN_EXPIRE_HOURS` | ❌ | `168` | `168` | Owner token expiry (hours) |
| `CUSTOMER_TOKEN_EXPIRE_HOURS` | ❌ | `1` | `1` | Customer token expiry (hours) |
| `MAX_LOGIN_ATTEMPTS` | ❌ | `5` | `5` | Max failed login attempts |
| `LOCKOUT_MINUTES` | ❌ | `30` | `30` | Account lockout duration |
| `PASSWORD_MIN_LENGTH` | ❌ | `8` | `8` | Minimum password length |
| `BCRYPT_ROUNDS` | ❌ | `12` | `12` | Password hashing rounds |

### Server Configuration (Required)

| Variable | Required | Default | Example | Description |
|----------|----------|---------|---------|-------------|
| `ENVIRONMENT` | ✅ | - | `production` | Environment: `development`, `staging`, `production` |
| `BACKEND_BASE_URL` | ✅ | - | `https://ppf-backend-w0aq.onrender.com` | Public backend URL |
| `SERVER_HOST` | ❌ | `0.0.0.0` | `0.0.0.0` | Server bind host |
| `SERVER_PORT` | ❌ | `8000` | `10000` | Server port (Render uses $PORT) |
| `WORKERS` | ❌ | `1` | `2` | Number of worker processes |
| `DEBUG` | ❌ | `false` | `false` | Enable debug mode |
| `LOG_LEVEL` | ❌ | `INFO` | `INFO` | Log level: DEBUG, INFO, WARNING, ERROR |

### CORS Configuration (Required for Production)

| Variable | Required | Default | Example | Description |
|----------|----------|---------|---------|-------------|
| `CORS_ORIGINS` | ✅ | `["*"]` | `["https://ppf-monitoring.vercel.app"]` | JSON array of allowed origins |

**Format:** JSON array string for Render:
```bash
CORS_ORIGINS='["https://ppf-monitoring.vercel.app","https://ppf-monitoring-git-master-ai-meharbnsinghs-projects.vercel.app"]'
```

### Super Admin Configuration (Required for First Run)

| Variable | Required | Default | Example | Description |
|----------|----------|---------|---------|-------------|
| `SUPER_ADMIN_USERNAME` | ❌ | `super_admin` | `super_admin` | Super admin username |
| `SUPER_ADMIN_PASSWORD` | ✅ | - | `SuperAdmin@123` | Super admin password (change in prod!) |
| `SUPER_ADMIN_EMAIL` | ❌ | `admin@ppf-monitor.com` | `admin@ppf-monitor.com` | Super admin email |

### Video/Streaming Configuration (Optional)

| Variable | Required | Default | Example | Description |
|----------|----------|---------|---------|-------------|
| `MEDIAMTX_HOST` | ❌ | `localhost` | `localhost` | MediaMTX hostname |
| `MEDIAMTX_RTSP_PORT` | ❌ | `8554` | `8554` | MediaMTX RTSP port |
| `MEDIAMTX_WEBRTC_PORT` | ❌ | `8889` | `8889` | MediaMTX WebRTC port |
| `MEDIAMTX_PUBLIC_URL` | ❌ | - | `https://piwifi.taile42746.ts.net` | Public MediaMTX URL |
| `STREAM_TOKEN_SECRET` | ✅ | - | `your-stream-secret-key` | Secret for stream tokens |
| `STREAM_TOKEN_EXPIRE_HOURS` | ❌ | `24` | `24` | Stream token expiry |

### Sensor Configuration (Optional)

| Variable | Required | Default | Example | Description |
|----------|----------|---------|---------|-------------|
| `SENSOR_OFFLINE_THRESHOLD_SECONDS` | ❌ | `60` | `60` | Device marked offline after (seconds) |
| `CAMERA_OFFLINE_THRESHOLD_SECONDS` | ❌ | `300` | `300` | Camera marked offline after (seconds) |
| `SENSOR_DATA_RETENTION_DAYS` | ❌ | `90` | `90` | Days to retain sensor data |

### Notification Configuration (Optional)

| Variable | Required | Default | Example | Description |
|----------|----------|---------|---------|-------------|
| `TWILIO_ACCOUNT_SID` | ❌ | - | `ACxxxxx` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | ❌ | - | `xxxxx` | Twilio auth token |
| `TWILIO_FROM_NUMBER` | ❌ | - | `+1234567890` | Twilio phone number |
| `SMTP_HOST` | ❌ | - | `smtp.gmail.com` | SMTP server host |
| `SMTP_PORT` | ❌ | `587` | `587` | SMTP server port |
| `SMTP_USER` | ❌ | - | `notifications@ppf-monitor.com` | SMTP username |
| `SMTP_PASSWORD` | ❌ | - | `xxxxxx` | SMTP password |

### Rate Limiting (Optional)

| Variable | Required | Default | Example | Description |
|----------|----------|---------|---------|-------------|
| `RATE_LIMIT_PER_MINUTE` | ❌ | `60` | `60` | General API rate limit |
| `RATE_LIMIT_LOGIN_PER_MINUTE` | ❌ | `10` | `10` | Login endpoint rate limit |

---

## Frontend Environment Variables

### Required Variables

| Variable | Required | Default | Example | Description |
|----------|----------|---------|---------|-------------|
| `VITE_API_BASE_URL` | ✅ | - | `https://ppf-backend-w0aq.onrender.com/api/v1` | Backend API base URL |
| `VITE_WS_URL` | ✅ | - | `wss://ppf-backend-w0aq.onrender.com/ws` | WebSocket URL |

### Development Variables

| Variable | Required | Default | Example | Description |
|----------|----------|---------|---------|-------------|
| `VITE_DEV_MOCK_DATA` | ❌ | `false` | `true` | Enable mock data in dev |
| `VITE_DEV_BYPASS_AUTH` | ❌ | `false` | `false` | Bypass authentication (dev only) |

---

## Raspberry Pi Configuration (pi_sensor_mqtt.py)

These are hardcoded in the Python script on each Pi:

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `DEVICE_ID` | ✅ | `PIWIFI-01` | Must match database device_id |
| `LICENSE_KEY` | ✅ | `LIC-RG-STUDIO-2026` | Must match database license_key |
| `WORKSHOP_ID` | ✅ | `2` | Workshop ID for MQTT topic |
| `PIT_ID` | ✅ | `3` | Pit ID for MQTT topic |
| `MQTT_BROKER` | ✅ | `xxx.hivemq.cloud` | MQTT broker hostname |
| `MQTT_PORT` | ❌ | `8883` | MQTT port |
| `MQTT_USER` | ✅ | `ppf_backend` | MQTT username |
| `MQTT_PASS` | ✅ | `PPF@...` | MQTT password |

**Topic format:** `workshop/{WORKSHOP_ID}/pit/{PIT_ID}/sensors`

---

## Complete Environment Files

### Backend .env (Local Development)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ppf_local

# MQTT (Local)
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USE_TLS=false
MQTT_USERNAME=
MQTT_PASSWORD=

# MQTT (Production - HiveMQ Cloud)
# MQTT_BROKER_HOST=c4cb4d2b4a3e432c9d61b8b56ee359af.s1.eu.hivemq.cloud
# MQTT_BROKER_PORT=8883
# MQTT_USE_TLS=true
# MQTT_USERNAME=ppf_backend
# MQTT_PASSWORD=PPF@Mqtt2026!secure

# JWT
JWT_SECRET_KEY=local-dev-secret-key-must-be-32-chars-min

# Server
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
BACKEND_BASE_URL=http://localhost:8000

# CORS (Local - allow all)
CORS_ORIGINS='["*"]'

# Admin
SUPER_ADMIN_PASSWORD=admin123

# Video (Optional)
STREAM_TOKEN_SECRET=stream-secret-key

# Notifications (Optional)
# TWILIO_ACCOUNT_SID=ACxxxxx
# TWILIO_AUTH_TOKEN=xxxxx
```

### Backend .env (Production on Render)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://neondb_owner:PASSWORD@ep-xxxxx-pooler.c-3.us-east-2.aws.neon.tech:5432/neondb
SYNC_DATABASE_URL=postgresql+psycopg2://neondb_owner:PASSWORD@ep-xxxxx-pooler.c-3.us-east-2.aws.neon.tech:5432/neondb

# MQTT (HiveMQ Cloud)
MQTT_BROKER_HOST=c4cb4d2b4a3e432c9d61b8b56ee359af.s1.eu.hivemq.cloud
MQTT_BROKER_PORT=8883
MQTT_USE_TLS=true
MQTT_USERNAME=ppf_backend
MQTT_PASSWORD=PPF@Mqtt2026!secure

# JWT
JWT_SECRET_KEY=c8c5643b8e7e83e49f859c44c8206a56fe7f567da340b0f62233fb226699b099

# Server
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
BACKEND_BASE_URL=https://ppf-backend-w0aq.onrender.com

# CORS (Specific origins only)
CORS_ORIGINS='["https://ppf-monitoring.vercel.app","https://ppf-monitoring-git-master-ai-meharbnsinghs-projects.vercel.app"]'

# Admin
SUPER_ADMIN_PASSWORD=SuperAdmin@123

# Video
MEDIAMTX_PUBLIC_URL=https://piwifi.taile42746.ts.net
STREAM_TOKEN_SECRET=your-stream-secret-key

# Ports (Render uses $PORT)
SERVER_PORT=$PORT
```

### Frontend .env (Local)

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

### Frontend .env (Production on Vercel)

```bash
VITE_API_BASE_URL=https://ppf-backend-w0aq.onrender.com/api/v1
VITE_WS_URL=wss://ppf-backend-w0aq.onrender.com/ws
```

---

## render.yaml Configuration

```yaml
services:
  - type: web
    name: ppf-backend
    runtime: python
    plan: free
    autoDeploy: true
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn src.main:app --host 0.0.0.0 --port $PORT --workers 2
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DATABASE_URL
        value: postgresql+asyncpg://neondb_owner:PASSWORD@ep-xxxxx-pooler.c-3.us-east-2.aws.neon.tech:5432/neondb
      - key: SYNC_DATABASE_URL
        value:postgresql+psycopg2://neondb_owner:PASSWORD@ep-xxxxx-pooler.c-3.us-east-2.aws.neon.tech:5432/neondb
      - key: MQTT_BROKER_HOST
        value: c4cb4d2b4a3e432c9d61b8b56ee359af.s1.eu.hivemq.cloud
      - key: MQTT_BROKER_PORT
        value: 8883
      - key: MQTT_USE_TLS
        value: "true"
      - key: MQTT_USERNAME
        value: ppf_backend
      - key: MQTT_PASSWORD
        value: PPF@Mqtt2026!secure
      - key: JWT_SECRET_KEY
        value: c8c5643b8e7e83e49f859c44c8206a56fe7f567da340b0f62233fb226699b099
      - key: SUPER_ADMIN_USERNAME
        value: super_admin
      - key: SUPER_ADMIN_PASSWORD
        value: SuperAdmin@123
      - key: CORS_ORIGINS
        value: '["https://ppf-monitoring.vercel.app"]'
      - key: ENVIRONMENT
        value: production
      - key: BACKEND_BASE_URL
        value: https://ppf-backend-w0aq.onrender.com
      - key: MEDIAMTX_PUBLIC_URL
        value: https://piwifi.taile42746.ts.net
      - key: STREAM_TOKEN_SECRET
        generateValue: true  # Auto-generate on first deploy
```

---

## Security Checklist

### Production Deployment

- [ ] Change `SUPER_ADMIN_PASSWORD` from default
- [ ] Use strong `JWT_SECRET_KEY` (64+ hex chars)
- [ ] Enable `MQTT_USE_TLS=true`
- [ ] Restrict `CORS_ORIGINS` to specific domains (no wildcards)
- [ ] Use environment-specific `ENVIRONMENT=production`
- [ ] Disable `DEBUG=false`
- [ ] Generate unique `STREAM_TOKEN_SECRET`
- [ ] Store sensitive values in Render secret environment variables

### Local Development

- [ ] Use different passwords than production
- [ ] Can use `DEBUG=true` and `CORS_ORIGINS=["*"]`
- [ ] Local MQTT can run without TLS on port 1883
