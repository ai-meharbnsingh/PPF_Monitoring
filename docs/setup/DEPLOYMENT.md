# Deployment Guide — PPF Workshop Monitoring System

This guide covers production deployment using Docker Compose on a Linux server or Windows machine.

---

## Prerequisites

- **Docker Engine 24+** and **Docker Compose v2**
- **Domain / Static IP** accessible by all ESP32 devices on the LAN
- **SSL certificate** (optional but recommended — Let's Encrypt via Certbot)
- Minimum **2 GB RAM**, **10 GB disk** for a single-workshop deployment

---

## 1. Server Setup

```bash
# Clone repository
git clone <repo-url> /opt/ppf-monitoring
cd /opt/ppf-monitoring

# Copy and fill .env
cp .env.example .env
nano .env   # fill in all required secrets (see below)
```

### Required `.env` variables for production

```env
# Database
DATABASE_URL=postgresql+asyncpg://ppf_user:STRONG_PASSWORD@postgres:5432/ppf_monitoring
DATABASE_USER=ppf_user
DATABASE_PASSWORD=STRONG_PASSWORD        # change this
DATABASE_NAME=ppf_monitoring

# Security
SECRET_KEY=<64-char random string>       # openssl rand -hex 32
ENVIRONMENT=production
DEBUG=false

# MQTT
MQTT_BROKER_HOST=mosquitto               # Docker service name
MQTT_USERNAME=ppf_backend
MQTT_PASSWORD=<strong password>

# Super admin (first run only)
SUPER_ADMIN_EMAIL=admin@your-domain.com
SUPER_ADMIN_USERNAME=super_admin
SUPER_ADMIN_PASSWORD=<strong password>

# CORS — restrict to your frontend domain
CORS_ORIGINS=["https://ppf.your-domain.com"]
```

---

## 2. Mosquitto Password File

Generate real hashes before starting (passwords in comments are dev-only):

```bash
# Generate ppf_backend user
docker run --rm eclipse-mosquitto:2 sh -c \
  "mosquitto_passwd -b -c /tmp/p ppf_backend 'YOUR_MQTT_PASSWORD' && cat /tmp/p"

# Append mqtt_user (for ESP32 devices)
docker run --rm eclipse-mosquitto:2 sh -c \
  "mosquitto_passwd -b /tmp/p mqtt_user 'DEVICE_PASSWORD' && cat /tmp/p"
```

Copy output into `docker/mosquitto/passwd`.

---

## 3. Start the Full Stack

```bash
# Start all services
docker-compose up -d

# First run: run migrations and seed
docker-compose exec backend alembic upgrade head
docker-compose exec backend python scripts/setup/seed_super_admin.py

# Follow logs
docker-compose logs -f backend
```

### Service health checks

```bash
docker-compose ps                         # all should be healthy/running
curl http://localhost:8000/health         # {"status":"healthy"}
docker logs ppf_mosquitto | tail -5      # "version 2.x.x running"
```

---

## 4. TLS / HTTPS (Production)

### 4a. Enable TLS on Mosquitto (port 8883)

Uncomment and fill in `docker/mosquitto/mosquitto.conf`:

```conf
listener 8883
protocol mqtt
cafile   /mosquitto/config/certs/ca.crt
certfile /mosquitto/config/certs/server.crt
keyfile  /mosquitto/config/certs/server.key
require_certificate false
```

Mount your certs:

```yaml
# docker-compose.yml — mosquitto volumes section
- ./certs/mosquitto:/mosquitto/config/certs:ro
```

Update ESP32 `config.h`:

```c
#define MQTT_BROKER_PORT  8883
#define MQTT_USE_TLS      true    // set in firmware if SSL is implemented
```

### 4b. HTTPS on the backend (via nginx reverse proxy)

Example nginx config:

```nginx
server {
    listen 443 ssl;
    server_name ppf.your-domain.com;

    ssl_certificate     /etc/letsencrypt/live/ppf.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ppf.your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 5. Frontend (Production Build)

```bash
cd frontend
npm install
npm run build          # outputs to dist/
```

Serve `dist/` via nginx or host on a CDN. Update `VITE_API_URL` in `.env.production`:

```env
VITE_API_URL=https://ppf.your-domain.com/api/v1
VITE_WS_URL=wss://ppf.your-domain.com/ws
```

---

## 6. Database Backups

```bash
# Manual backup
docker exec ppf_postgres pg_dump -U ppf_user ppf_monitoring > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i ppf_postgres psql -U ppf_user ppf_monitoring < backup_20260222.sql
```

Automate with a cron job:

```cron
0 2 * * * docker exec ppf_postgres pg_dump -U ppf_user ppf_monitoring > /backups/ppf_$(date +\%Y\%m\%d).sql
```

---

## 7. Updating

```bash
git pull origin main
docker-compose build backend          # rebuild only backend image
docker-compose up -d backend
docker-compose exec backend alembic upgrade head   # run new migrations
```

---

## 8. Monitoring

| URL | Purpose |
|-----|---------|
| `http://server:8000/health` | API + MQTT + DB health |
| `http://server:8000/metrics` | System metrics (super_admin only) |
| `http://server:8000/docs` | Swagger UI (disable in production: `DEBUG=false`) |
| `http://server:5050` | pgAdmin (start with `--profile dev`) |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `MQTT not_initialized` on startup | Ensure Mosquitto is running before backend starts. Restart backend after broker is healthy. |
| ESP32 not publishing | Check `MQTT_BROKER_HOST` in `config.h` — must be LAN IP, not `localhost`. |
| `ModuleNotFoundError: asyncpg` | Backend running without venv. Use `venv/Scripts/python.exe -m uvicorn ...` |
| Mosquitto `keepalive_interval` error | Remove that option — it's bridge-only, not valid for listeners. |
| Healthcheck failing (Mosquitto) | Verify `health` user password in `docker-compose.yml` matches `docker/mosquitto/passwd`. |

---

*PPF Monitoring Team — 2026*
