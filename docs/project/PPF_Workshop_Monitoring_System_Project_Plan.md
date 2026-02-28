# SMART PPF WORKSHOP MONITORING SYSTEM
## Complete Project Plan & Technical Blueprint

> **Project Type:** IoT Monitoring SaaS  
> **Business Model:** Subscription-based service with device licensing  
> **Deployment:** Cloud-hosted, modular pit expansion  
> **Version:** 1.0  
> **Date:** February 20, 2026

---

## EXECUTIVE SUMMARY

### The Problem
PPF (Paint Protection Film) workshop owners lose customers due to lack of transparency. Customers wait hours without visibility into their car's status, creating anxiety and reducing trust. Workshop owners can't scale operations or justify premium pricing without demonstrating professionalism.

### The Solution
Real-time workshop monitoring system providing:
- **Live video streaming** of customer's car during modification
- **Environmental monitoring** (Temperature, Humidity, Air Quality)
- **Job progress tracking** with estimated completion times
- **Secure customer access** via login credentials
- **Multi-user management** for workshop staff

### Business Model
**Service-as-a-Product (SaaP):**
- Customers purchase hardware kits (one-time)
- Monthly subscription for cloud services
- Each device has unique license key (remote kill-switch capability)
- Plug-and-play modular expansion (add unlimited pits)

### Success Metrics (MVP Target)
- Customer satisfaction: 90%+ positive feedback on transparency
- Repeat business: 30% increase within 6 months
- Premium pricing: Justify 15-20% higher service fees
- Operational efficiency: 40% reduction in status inquiry calls

---

## 1. SYSTEM ARCHITECTURE

### 1.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    CLOUD SERVER (Your Site)                   │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐          │
│  │  MQTT      │  │ PostgreSQL  │  │   MediaMTX   │          │
│  │  Broker    │  │  Database   │  │ Video Server │          │
│  └────────────┘  └─────────────┘  └──────────────┘          │
│  ┌──────────────────────────────────────────────────┐        │
│  │     Backend API (FastAPI) + WebSocket Server     │        │
│  └──────────────────────────────────────────────────┘        │
│  ┌──────────────────────────────────────────────────┐        │
│  │    Frontend (React) - Owner + Customer Portals   │        │
│  └──────────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────┘
                            ▲
                            │ VPN Tunnel (Secure)
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                  WORKSHOP (Client Site)                       │
│  ┌─────────────────────────────────────────────┐             │
│  │  Network Switch (PoE) + Router + VPN Client │             │
│  └─────────────────────────────────────────────┘             │
│                                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │  PIT 1   │  │  PIT 2   │  │  PIT 3   │  ... (Scalable)  │
│  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │                   │
│  │ │Camera│ │  │ │Camera│ │  │ │Camera│ │  Hikvision IP Cam│
│  │ └──────┘ │  │ └──────┘ │  │ └──────┘ │  (RTSP Stream)   │
│  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │                   │
│  │ │ESP32 │ │  │ │ESP32 │ │  │ │ESP32 │ │  Olimex Gateway  │
│  │ │ +    │ │  │ │ +    │ │  │ │ +    │ │  + BME680 Sensor │
│  │ │BME680│ │  │ │BME680│ │  │ │BME680│ │                   │
│  │ └──────┘ │  │ └──────┘ │  │ └──────┘ │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Core Design Principles

1. **Reliability First:** Ethernet-based connectivity (no WiFi instability)
2. **Modular Expansion:** Each pit is identical, plug-and-play
3. **Security by Design:** VPN tunnel + device licensing + access control
4. **Service Model:** Remote management & kill-switch for non-payment
5. **Camera Agnostic:** Support customer's existing cameras OR provide tested models

---

## 2. COMPONENT SPECIFICATIONS

### 2.1 PER-PIT HARDWARE KIT (Module)

#### Kit Contents:
| Component | Model | Quantity | Unit Price (INR) | Purpose |
|-----------|-------|----------|------------------|---------|
| **IP Camera** | Hikvision DS-2CD1323G0E-I (2MP) | 1 | ₹3,500 | Live video streaming |
| **IoT Gateway** | Olimex ESP32-GATEWAY-EA-WITH-BOX | 1 | ₹2,800 | Ethernet connectivity |
| **Sensor** | Bosch BME680 Module | 1 | ₹800 | Temp/Humidity/AQI |
| **Ethernet Cable** | Cat6, 10m | 1 | ₹200 | Camera to switch |
| **Ethernet Cable** | Cat6, 5m | 1 | ₹100 | ESP32 to switch |
| **Mounting Kit** | Camera bracket + screws | 1 | ₹300 | Installation hardware |
| **Jumper Wires** | I2C connections | Set | ₹50 | Sensor to ESP32 |
| **TOTAL PER PIT KIT** | | | **₹7,750** | (~$93 USD) |

#### Camera Options:
| Option | Model | Resolution | Price | Notes |
|--------|-------|------------|-------|-------|
| **Budget (MVP)** | Hikvision DS-2CD1323G0E-I | 2MP (1080p) | ₹3,500 | Good for demo |
| **Standard** | Hikvision DS-2CD2143G2-I | 4MP | ₹6,500 | Better low-light |
| **Premium** | Hikvision DS-2CD2347G2-LU | 4MP ColorVu | ₹12,000 | 24/7 color imaging |
| **Customer's Existing** | Various RTSP-compatible | Varies | ₹0 | If already installed |

**Camera Compatibility Strategy:**
- System supports any RTSP-compatible IP camera
- During onboarding, test customer's camera compatibility
- If incompatible/poor quality → recommend our tested models
- Firmware adaptable to different camera API endpoints

### 2.2 WORKSHOP INFRASTRUCTURE (One-Time Setup)

| Component | Model | Quantity | Price (INR) | Purpose |
|-----------|-------|----------|-------------|---------|
| **PoE Switch** | TP-Link TL-SG1005P (5-port) | 1 | ₹2,500 | Power + data for cameras |
| **Router** | TP-Link Archer C6 (VPN capable) | 1 | ₹2,000 | Internet + VPN client |
| **Ethernet Cables** | Cat6, various lengths | Bulk | ₹1,000 | Workshop wiring |
| **Cable Management** | Conduits, clips | Set | ₹500 | Professional installation |
| **Installation Labor** | Electrician/technician | 1 day | ₹2,000 | Physical setup |
| **TOTAL INFRASTRUCTURE** | | | **₹8,000** | (~$95 USD) |

**Note:** For 3-pit workshop, use 8-port PoE switch (₹4,500 instead of ₹2,500)

### 2.3 CLOUD SERVER CONFIGURATION

#### Production Server Specs (Recommended):
| Resource | Specification | Provider | Monthly Cost (INR) |
|----------|--------------|----------|-------------------|
| **Cloud VM** | 2 vCPU, 4GB RAM, 50GB SSD | DigitalOcean/Linode | ₹1,200 |
| **Storage** | 500GB block storage (videos) | DigitalOcean Spaces | ₹800 |
| **Bandwidth** | 3TB/month included | Included | ₹0 |
| **Backup** | Daily snapshots | Provider service | ₹300 |
| **Domain + SSL** | .com domain + Let's Encrypt | Namecheap | ₹100 |
| **TOTAL MONTHLY** | | | **₹2,400** | (~$29 USD) |

**Scaling Plan:**
- Start: 2 vCPU, 4GB RAM (handles 5-10 workshops)
- Scale: 4 vCPU, 8GB RAM (handles 20-50 workshops)
- Enterprise: 8 vCPU, 16GB RAM (handles 100+ workshops)

---

## 3. TECHNICAL STACK

### 3.1 Backend Technologies

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **API Framework** | FastAPI | 0.109+ | RESTful API + WebSocket |
| **Database** | PostgreSQL | 15+ | Relational data storage |
| **Message Queue** | Mosquitto (MQTT) | 2.0+ | Real-time sensor data |
| **Video Server** | MediaMTX | 1.5+ | RTSP to WebRTC conversion |
| **Web Server** | Nginx | 1.24+ | Reverse proxy + SSL |
| **Process Manager** | PM2 | 5.3+ | App monitoring + restart |
| **Authentication** | JWT | Latest | Token-based auth |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Async Runtime** | Uvicorn | 0.27+ | ASGI server |

### 3.2 Frontend Technologies

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Framework** | React | 18+ | UI components |
| **State Management** | Redux Toolkit | 2.0+ | Global state |
| **Styling** | Tailwind CSS | 3.4+ | Responsive design |
| **Video Player** | Video.js | 8.0+ | WebRTC/HLS playback |
| **Real-time Comms** | Socket.IO Client | 4.6+ | WebSocket connection |
| **HTTP Client** | Axios | 1.6+ | API calls |
| **Routing** | React Router | 6.21+ | Navigation |
| **Forms** | React Hook Form | 7.49+ | Form validation |

### 3.3 IoT/Embedded Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Firmware Platform** | ESP-IDF | 5.1+ | ESP32 development |
| **MQTT Library** | PubSubClient | 2.8+ | Arduino MQTT |
| **Sensor Library** | BSEC (Bosch) | 2.4+ | BME680 data processing |
| **JSON** | ArduinoJson | 7.0+ | Data serialization |
| **OTA Updates** | ESP32 OTA | Built-in | Remote firmware update |

---

## 4. DATA FLOW & PROTOCOLS

### 4.1 Sensor Data Flow

```
BME680 Sensor (I2C)
    ↓
ESP32 Gateway (reads every 10 seconds)
    ↓ Processes with BSEC library
    ↓ Generates JSON payload
{
  "device_id": "pit1_esp32_abc123",
  "license_key": "LIC-XXXX-YYYY-ZZZZ",
  "timestamp": "2026-02-20T22:30:00Z",
  "temperature": 24.5,
  "humidity": 55.2,
  "aqi": 78,
  "pressure": 1013.25
}
    ↓ MQTT Publish to topic: workshop/{workshop_id}/pit/{pit_id}/sensors
    ↓ Over Ethernet → VPN Tunnel
    ↓
Cloud MQTT Broker (Mosquitto)
    ↓ Backend subscribes to workshop/# topics
    ↓
Backend API (FastAPI)
    ↓ Validates license_key (active subscription check)
    ↓ If valid → Store in PostgreSQL
    ↓ If invalid → Ignore data + log violation
    ↓ Push to WebSocket clients
    ↓
Frontend (Owner/Customer)
    ↓ Updates dashboard in real-time
    ↓ Display: Temp, Humidity, AQI with color-coded status
```

### 4.2 Video Stream Flow

```
Hikvision Camera (RTSP)
    ↓ rtsp://192.168.1.100:554/Streaming/Channels/101
    ↓ Over Ethernet → VPN Tunnel
    ↓
Cloud Video Server (MediaMTX)
    ↓ Pulls RTSP stream
    ↓ Transcodes to WebRTC (low latency) or HLS (compatibility)
    ↓ Generates web URL: https://video.yourdomain.com/pit1/live
    ↓
Frontend (Owner/Customer)
    ↓ Video.js player embeds stream
    ↓ Overlays sensor data on video
    ↓ Access control: Owner sees all, Customer sees assigned pit only
```

### 4.3 Job Management Flow

```
Owner Logs In (Web Dashboard)
    ↓
Creates New Job:
  - Customer name
  - Car details (model, plate)
  - Assigned pit
  - Work type (Full PPF / Partial / Ceramic Coating)
  - Estimated duration (selects from template or manual)
    ↓
Backend API
    ↓ Generates job_id
    ↓ Creates customer account (if new)
    ↓ Sends credentials via WhatsApp/SMS
    ↓ Stores in PostgreSQL
    ↓ Broadcasts job update via WebSocket
    ↓
Customer Logs In (Mobile/Web)
    ↓ Sees only their assigned pit
    ↓ Live video + Temp/Humidity/AQI
    ↓ Status: "Surface Prep" → "PPF Installation" → "Curing"
    ↓ Time Remaining: "2h 15m" (live countdown)
    ↓
Owner Updates Status (manual or via API)
    ↓ Backend pushes update to customer
    ↓ Customer sees real-time progress
```

---

## 5. DEVICE LICENSING & KILL-SWITCH MECHANISM

### 5.1 License Key Architecture

**Each ESP32 device has:**
- **Unique Device ID:** MAC address-based (e.g., `ESP32-A1B2C3D4E5F6`)
- **License Key:** 16-character alphanumeric (e.g., `LIC-4F8D-9K2L-3P7Q`)
- **Workshop Assignment:** Links device to specific workshop_id
- **Subscription Status:** `active`, `suspended`, `expired`

**License Key Storage:**
```cpp
// Hardcoded in ESP32 firmware (during provisioning)
const char* DEVICE_ID = "ESP32-A1B2C3D4E5F6";
const char* LICENSE_KEY = "LIC-4F8D-9K2L-3P7Q";
```

### 5.2 Subscription Verification

**ESP32 sends license_key with every MQTT message.**

**Backend validation logic:**
```python
def validate_license(license_key, device_id):
    # Query database
    subscription = db.query(Subscription).filter(
        Subscription.license_key == license_key,
        Subscription.device_id == device_id
    ).first()
    
    if not subscription:
        return {"valid": False, "reason": "Unknown license"}
    
    if subscription.status == "expired":
        return {"valid": False, "reason": "Subscription expired"}
    
    if subscription.status == "suspended":
        return {"valid": False, "reason": "Payment overdue"}
    
    if subscription.expires_at < datetime.now():
        return {"valid": False, "reason": "License expired"}
    
    return {"valid": True}
```

### 5.3 Kill-Switch Mechanism

**Remote Deactivation Flow:**

```
Admin Dashboard
    ↓ Marks subscription as "suspended"
    ↓ Updates database: subscription.status = "suspended"
    ↓
ESP32 sends next sensor data (with license_key)
    ↓
Backend receives MQTT message
    ↓ validate_license() returns {"valid": False, "reason": "Payment overdue"}
    ↓ Backend publishes to topic: workshop/{workshop_id}/device/{device_id}/command
    ↓ Payload: {"command": "DISABLE", "reason": "subscription_suspended"}
    ↓
ESP32 subscribes to workshop/{workshop_id}/device/{device_id}/command
    ↓ Receives DISABLE command
    ↓ Stops reading sensors
    ↓ Publishes final message: {"status": "disabled", "reason": "..."}
    ↓ Enters deep sleep (or shows LED error pattern)
```

**ESP32 Firmware Logic:**
```cpp
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  if (strstr(topic, "/command")) {
    JsonDocument doc;
    deserializeJson(doc, payload, length);
    
    if (doc["command"] == "DISABLE") {
      Serial.println("Device disabled by server");
      // Stop sensor loop
      sensorEnabled = false;
      // Publish final status
      publishDisabledStatus();
      // Enter deep sleep or idle mode
      esp_deep_sleep_start();
    }
  }
}
```

### 5.4 Re-Activation Process

**When payment received:**
1. Admin marks subscription as `active` in database
2. Backend publishes to topic: `workshop/{workshop_id}/device/{device_id}/command`
3. Payload: `{"command": "ENABLE", "reason": "payment_received"}`
4. ESP32 wakes up (if in deep sleep, requires physical reset button)
5. Resumes normal operation

**Alternative:** ESP32 polls backend API every 1 hour even when disabled (light sleep, not deep sleep).

---

## 6. FEATURE SPECIFICATION

### 6.1 Owner Dashboard Features

**User Management:**
- [ ] Add/edit workshop staff accounts (Admin, Operator roles)
- [ ] View all staff activity logs
- [ ] Assign pit access permissions per staff member

**Job Management:**
- [ ] Create new job (customer name, car details, pit assignment)
- [ ] Work type templates:
  - Full PPF (default: 6 hours)
  - Partial PPF (default: 3 hours)
  - Ceramic Coating (default: 4 hours)
  - Custom (manual time entry)
- [ ] Modify estimated time in real-time
- [ ] Update job status:
  - `Waiting` → `In Progress` → `Quality Check` → `Completed`
- [ ] View job history (past 90 days)
- [ ] Generate job reports (PDF export)

**Live Monitoring:**
- [ ] View all pits simultaneously (grid view)
- [ ] Click pit to see full-screen video + data
- [ ] Real-time sensor overlay on video:
  - Temperature (°C)
  - Humidity (%)
  - AQI (color-coded: Green <50, Yellow 50-100, Red >100)
- [ ] See which staff members are working on each pit
- [ ] View customer login activity (who's watching)

**Alerts & Notifications:**
- [ ] AQI exceeds threshold (>150) → SMS + Dashboard alert
- [ ] Temperature outside safe range (15°C - 35°C) → Alert
- [ ] Humidity too high (>70%) → Alert
- [ ] Camera offline → Immediate alert
- [ ] ESP32 offline → Alert

**Analytics:**
- [ ] Average job duration by type
- [ ] Peak usage hours (busiest pits)
- [ ] Environmental trend graphs (Temp/Humidity/AQI over time)
- [ ] Customer satisfaction (post-job rating)

### 6.2 Customer Portal Features

**Login:**
- [ ] Receive credentials via WhatsApp/SMS
- [ ] Simple login: Username + Password
- [ ] Session expires after 24 hours or job completion

**Live View:**
- [ ] See only assigned pit's video stream
- [ ] Real-time sensor data overlay:
  - Temperature, Humidity, AQI
  - Color-coded status indicators
- [ ] Full-screen mode for mobile

**Job Status:**
- [ ] Current status (e.g., "PPF Installation in Progress")
- [ ] Estimated time remaining (live countdown)
- [ ] Progress bar (manual stages set by owner)

**Notifications:**
- [ ] Job started → SMS notification
- [ ] 30 minutes remaining → SMS notification
- [ ] Job completed → SMS notification

**Post-Job:**
- [ ] View time-lapse video of full job (optional feature for Phase 2)
- [ ] Submit feedback/rating (1-5 stars)
- [ ] Download job summary PDF

### 6.3 Staff/Operator Features (Simplified Owner View)

- [ ] View assigned pit(s) only
- [ ] Update job status (no editing customer/time)
- [ ] Mark tools/materials used (inventory tracking - Phase 2)
- [ ] Cannot see other pits unless permission granted

---

## 7. DATABASE SCHEMA

### 7.1 Core Tables

**users:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL, -- 'owner', 'staff', 'customer'
    workshop_id INT REFERENCES workshops(id),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);
```

**workshops:**
```sql
CREATE TABLE workshops (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    owner_id INT REFERENCES users(id),
    address TEXT,
    phone VARCHAR(20),
    total_pits INT DEFAULT 0,
    subscription_status VARCHAR(20) DEFAULT 'trial', -- 'trial', 'active', 'suspended', 'expired'
    subscription_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**pits:**
```sql
CREATE TABLE pits (
    id SERIAL PRIMARY KEY,
    workshop_id INT REFERENCES workshops(id),
    pit_number INT NOT NULL, -- 1, 2, 3, ...
    device_id VARCHAR(50) UNIQUE NOT NULL, -- ESP32 MAC
    license_key VARCHAR(20) UNIQUE NOT NULL,
    camera_ip VARCHAR(50),
    camera_rtsp_url TEXT,
    camera_model VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'disabled', 'maintenance'
    created_at TIMESTAMP DEFAULT NOW()
);
```

**jobs:**
```sql
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    workshop_id INT REFERENCES workshops(id),
    pit_id INT REFERENCES pits(id),
    customer_id INT REFERENCES users(id),
    car_model VARCHAR(100),
    car_plate VARCHAR(20),
    work_type VARCHAR(50), -- 'Full PPF', 'Partial PPF', 'Ceramic Coating'
    estimated_duration_minutes INT,
    actual_start_time TIMESTAMP,
    estimated_end_time TIMESTAMP,
    actual_end_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'waiting', -- 'waiting', 'in_progress', 'quality_check', 'completed'
    assigned_staff TEXT[], -- Array of staff user IDs
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**sensor_data:**
```sql
CREATE TABLE sensor_data (
    id SERIAL PRIMARY KEY,
    pit_id INT REFERENCES pits(id),
    temperature FLOAT,
    humidity FLOAT,
    aqi INT,
    pressure FLOAT,
    timestamp TIMESTAMP DEFAULT NOW(),
    INDEX idx_pit_timestamp (pit_id, timestamp DESC)
);
```

**subscriptions:**
```sql
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    workshop_id INT REFERENCES workshops(id),
    device_id VARCHAR(50) REFERENCES pits(device_id),
    license_key VARCHAR(20) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'suspended', 'expired'
    plan VARCHAR(20), -- 'basic', 'standard', 'premium'
    monthly_fee DECIMAL(10,2),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    last_payment_date TIMESTAMP
);
```

**alerts:**
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    workshop_id INT REFERENCES workshops(id),
    pit_id INT REFERENCES pits(id),
    alert_type VARCHAR(50), -- 'high_aqi', 'camera_offline', 'temp_out_of_range'
    severity VARCHAR(20), -- 'info', 'warning', 'critical'
    message TEXT,
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 8. API ENDPOINTS

### 8.1 Authentication

```
POST /api/auth/login
  Body: { "username": "owner1", "password": "..." }
  Response: { "access_token": "JWT_TOKEN", "role": "owner" }

POST /api/auth/logout
  Headers: { "Authorization": "Bearer JWT_TOKEN" }
  Response: { "message": "Logged out successfully" }

GET /api/auth/me
  Headers: { "Authorization": "Bearer JWT_TOKEN" }
  Response: { "id": 1, "username": "owner1", "role": "owner", "workshop_id": 1 }
```

### 8.2 Job Management (Owner/Staff)

```
POST /api/jobs
  Headers: { "Authorization": "Bearer JWT_TOKEN" }
  Body: {
    "customer_name": "John Doe",
    "car_model": "Tesla Model 3",
    "car_plate": "DL01AB1234",
    "pit_id": 1,
    "work_type": "Full PPF",
    "estimated_duration_minutes": 360
  }
  Response: { "job_id": 42, "customer_credentials": { "username": "johndoe", "password": "temp123" } }

GET /api/jobs?workshop_id=1&status=in_progress
  Response: [ { "job_id": 42, "customer_name": "John Doe", "pit_number": 1, ... }, ... ]

PATCH /api/jobs/42/status
  Body: { "status": "quality_check" }
  Response: { "job_id": 42, "status": "quality_check", "updated_at": "2026-02-20T23:00:00Z" }

PATCH /api/jobs/42/time
  Body: { "estimated_end_time": "2026-02-21T02:00:00Z" }
  Response: { "job_id": 42, "estimated_end_time": "2026-02-21T02:00:00Z" }
```

### 8.3 Live Monitoring (Owner/Customer)

```
GET /api/pits/{pit_id}/stream
  Headers: { "Authorization": "Bearer JWT_TOKEN" }
  Response: { "stream_url": "https://video.domain.com/pit1/live", "protocol": "webrtc" }

GET /api/pits/{pit_id}/sensors/latest
  Response: { "temperature": 24.5, "humidity": 55.2, "aqi": 78, "timestamp": "..." }

GET /api/pits/{pit_id}/sensors/history?from=2026-02-20T00:00:00Z&to=2026-02-20T23:59:59Z
  Response: [ { "temperature": 24.3, "humidity": 54.8, "aqi": 76, "timestamp": "..." }, ... ]
```

### 8.4 Device Management (Admin/Owner)

```
POST /api/devices
  Body: {
    "device_id": "ESP32-A1B2C3D4E5F6",
    "pit_number": 1,
    "camera_ip": "192.168.1.100",
    "camera_model": "Hikvision DS-2CD1323G0E-I"
  }
  Response: { "license_key": "LIC-4F8D-9K2L-3P7Q", "status": "active" }

PATCH /api/devices/{device_id}/status
  Body: { "status": "disabled", "reason": "payment_overdue" }
  Response: { "device_id": "...", "status": "disabled", "command_sent": true }
```

### 8.5 WebSocket Events (Real-Time)

**Client subscribes to:**
```
ws://domain.com/ws?token=JWT_TOKEN

Events received:
- sensor_update: { "pit_id": 1, "temperature": 24.5, "humidity": 55.2, "aqi": 78 }
- job_status: { "job_id": 42, "status": "quality_check" }
- alert: { "pit_id": 1, "alert_type": "high_aqi", "severity": "warning", "message": "AQI exceeded 150" }
```

---

## 9. DEPLOYMENT ARCHITECTURE

### 9.1 Cloud Server Setup (DigitalOcean Droplet)

**Initial Server Configuration:**
```bash
# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y nginx postgresql-15 mosquitto mosquitto-clients python3.11 python3-pip nodejs npm git ufw

# Setup firewall
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 1883/tcp  # MQTT
ufw allow 8554/tcp  # RTSP (MediaMTX)
ufw enable

# Install MediaMTX
wget https://github.com/bluenviron/mediamtx/releases/download/v1.5.0/mediamtx_v1.5.0_linux_amd64.tar.gz
tar -xzf mediamtx_v1.5.0_linux_amd64.tar.gz -C /opt/mediamtx
```

**Backend Setup:**
```bash
# Clone repository (after development)
cd /var/www
git clone https://github.com/yourusername/ppf-monitoring-backend.git
cd ppf-monitoring-backend

# Python virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database setup
sudo -u postgres psql
CREATE DATABASE ppf_monitoring;
CREATE USER ppf_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ppf_monitoring TO ppf_user;

# Run migrations
alembic upgrade head

# Start backend with PM2
npm install -g pm2
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name ppf-backend
pm2 save
pm2 startup
```

**Frontend Setup:**
```bash
# Build React app
cd /var/www/ppf-monitoring-frontend
npm install
npm run build

# Configure Nginx
nano /etc/nginx/sites-available/ppf-monitoring
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        root /var/www/ppf-monitoring-frontend/build;
        try_files $uri /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 9.2 Workshop Setup (Per Location)

**Network Configuration:**
```
1. Router with VPN Client (WireGuard/OpenVPN)
   - Connect to cloud server's VPN server
   - Static route to cloud MQTT broker (1883)
   - Static route to cloud MediaMTX server (8554)

2. PoE Switch
   - Connect to router
   - Assign static IPs to cameras (192.168.1.100-110)
   - Assign static IPs to ESP32s (192.168.1.150-160)

3. ESP32 Configuration (per pit)
   - Flash firmware with unique device_id and license_key
   - Configure MQTT broker: mqtt://cloud-server-ip:1883
   - Configure WiFi fallback (optional)
```

**VPN Setup (Workshop Router):**
```bash
# Install WireGuard client on router (example for OpenWRT)
opkg update
opkg install wireguard luci-proto-wireguard

# Add WireGuard interface with config from cloud server
# This creates secure tunnel: workshop <-> cloud
```

### 9.3 ESP32 Firmware Provisioning

**Firmware Structure:**
```
ppf-esp32-firmware/
├── config.h           # Device-specific (UNIQUE PER DEVICE)
├── main.cpp           # Core logic (SAME FOR ALL DEVICES)
├── sensors.cpp        # BME680 handling
├── mqtt.cpp           # MQTT client
└── ota.cpp            # OTA update handler
```

**config.h (Unique per device):**
```cpp
#ifndef CONFIG_H
#define CONFIG_H

// UNIQUE IDENTIFIERS (Change for each device)
const char* DEVICE_ID = "ESP32-A1B2C3D4E5F6";
const char* LICENSE_KEY = "LIC-4F8D-9K2L-3P7Q";
const char* WORKSHOP_ID = "workshop_001";
const char* PIT_ID = "pit1";

// NETWORK CONFIG (Same for all devices in workshop)
const char* MQTT_BROKER = "10.8.0.1";  // VPN IP of cloud server
const int MQTT_PORT = 1883;
const char* MQTT_USER = "workshop_001";
const char* MQTT_PASS = "secure_mqtt_password";

// SENSOR CONFIG (Same for all)
const int I2C_SDA = 21;
const int I2C_SCL = 22;
const int SENSOR_READ_INTERVAL = 10000;  // 10 seconds

#endif
```

**Flashing Process:**
1. Edit `config.h` for each device
2. Compile firmware: `pio run -t upload`
3. Test locally before deployment
4. Ship to workshop with pre-configured settings

---

## 10. COST BREAKDOWN

### 10.1 MVP Costs (Single Pit Deployment)

| Category | Item | Quantity | Unit Price (INR) | Total (INR) |
|----------|------|----------|------------------|-------------|
| **Hardware (Per Pit)** | | | | |
| | Hikvision 2MP Camera | 1 | ₹3,500 | ₹3,500 |
| | Olimex ESP32-GATEWAY-EA | 1 | ₹2,800 | ₹2,800 |
| | BME680 Sensor | 1 | ₹800 | ₹800 |
| | Cables + Mounting | 1 | ₹650 | ₹650 |
| **Workshop Infrastructure** | | | | |
| | PoE Switch (5-port) | 1 | ₹2,500 | ₹2,500 |
| | Router (VPN-capable) | 1 | ₹2,000 | ₹2,000 |
| | Installation Labor | 1 day | ₹2,000 | ₹2,000 |
| **Cloud Costs (First Month)** | | | | |
| | Server (DigitalOcean) | 1 | ₹1,200 | ₹1,200 |
| | Storage (500GB) | 1 | ₹800 | ₹800 |
| | Domain + SSL | 1 | ₹100 | ₹100 |
| **Development (One-Time)** | | | | |
| | Backend Development | 80 hours | ₹500/hr | ₹40,000 |
| | Frontend Development | 60 hours | ₹500/hr | ₹30,000 |
| | ESP32 Firmware | 30 hours | ₹500/hr | ₹15,000 |
| | Testing + Documentation | 20 hours | ₹500/hr | ₹10,000 |
| **TOTAL MVP COST** | | | | **₹1,11,350** |
| **(~$1,335 USD)** | | | | |

### 10.2 3-Pit Workshop Deployment

| Category | Total (INR) |
|----------|-------------|
| Hardware (3 pits × ₹7,750) | ₹23,250 |
| Workshop Infrastructure (8-port switch) | ₹10,000 |
| Cloud Setup (same as MVP) | ₹2,100 |
| **TOTAL HARDWARE (3 pits)** | **₹35,350** |
| **Development (same, one-time)** | ₹95,000 |
| **TOTAL 3-PIT DEPLOYMENT** | **₹1,30,350** |
| **(~$1,565 USD)** | |

### 10.3 Monthly Recurring Costs

| Category | Per Workshop (INR) | Notes |
|----------|-------------------|-------|
| Cloud Server | ₹1,200 | Shared across all workshops |
| Cloud Storage | ₹800 | Scales with video retention |
| Backups | ₹300 | Daily snapshots |
| Domain/SSL | ₹100 | Annual cost divided by 12 |
| **Subtotal per workshop** | **₹2,400** | |
| **Cost per pit (÷3)** | **₹800/pit/month** | |

**Scaling Economics:**
- **1-5 workshops:** ₹2,400/month total (single server)
- **10 workshops:** ₹3,000/month (upgraded server: 4 vCPU, 8GB RAM)
- **50 workshops:** ₹6,000/month (enterprise server: 8 vCPU, 16GB RAM)

### 10.4 Pricing Model (Suggested)

| Plan | Monthly Fee (per pit) | Margins |
|------|----------------------|---------|
| **Cost to us** | ₹800/pit/month | (cloud + storage) |
| **Selling Price** | ₹1,500/pit/month | 87% margin |
| **Volume Discount (5+ pits)** | ₹1,200/pit/month | 50% margin |

**Hardware Sales:**
- **Cost:** ₹7,750/pit kit
- **Selling Price:** ₹12,000/pit kit
- **Margin:** ₹4,250 (55%)

**Example Revenue (10-Workshop Client, 30 pits total):**
- Hardware (one-time): 30 × ₹12,000 = ₹3,60,000
- Monthly recurring: 30 × ₹1,200 = ₹36,000/month = ₹4,32,000/year
- **Year 1 Revenue:** ₹7,92,000 (~$9,500 USD)

---

## 11. DEVELOPMENT TIMELINE

### Phase 1: MVP (Single Pit) - 6 Weeks

**Week 1-2: Backend Foundation**
- [ ] Setup cloud server (DigitalOcean)
- [ ] Install PostgreSQL, Mosquitto, MediaMTX
- [ ] Database schema implementation
- [ ] JWT authentication API
- [ ] Basic CRUD APIs (users, jobs, pits)
- [ ] MQTT subscriber service (sensor data ingestion)

**Week 3: ESP32 Firmware**
- [ ] BME680 sensor integration (BSEC library)
- [ ] MQTT client implementation
- [ ] License key validation
- [ ] OTA update capability
- [ ] Testing with single device

**Week 4: Video Streaming**
- [ ] MediaMTX configuration (RTSP to WebRTC)
- [ ] Camera integration (test with Hikvision)
- [ ] Stream access control (authenticated URLs)
- [ ] Latency optimization (<3 seconds)

**Week 5: Frontend Development**
- [ ] Owner dashboard (job creation, live monitoring)
- [ ] Customer portal (login, video view, sensor overlay)
- [ ] WebSocket integration (real-time updates)
- [ ] Responsive design (mobile-first)

**Week 6: Testing & Demo**
- [ ] End-to-end testing (customer journey)
- [ ] Load testing (simulate 10 concurrent streams)
- [ ] Bug fixes and polish
- [ ] **Demo to Friend (Client)**
- [ ] Gather feedback

**Deliverables:**
✅ Fully functional 1-pit system
✅ Owner can create jobs, monitor live
✅ Customer can login and view their car
✅ Real-time sensor data with alerts
✅ Video recording (7-day retention)

---

### Phase 2: Production Deployment (3 Pits) - 4 Weeks

**Week 7-8: Scaling & Optimization**
- [ ] Multi-pit support in frontend (grid view)
- [ ] Enhanced analytics dashboard
- [ ] Alert system (SMS integration via Twilio)
- [ ] Job templates with time presets
- [ ] Staff account management

**Week 9: Hardware Deployment**
- [ ] Purchase hardware for 3 pits
- [ ] Workshop installation (cabling, mounting)
- [ ] VPN setup (workshop to cloud)
- [ ] Flash ESP32s with unique config
- [ ] Test all 3 pits end-to-end

**Week 10: Production Hardening**
- [ ] Backup automation (daily database snapshots)
- [ ] Monitoring (PM2 Plus, error logging)
- [ ] SSL certificate setup (Let's Encrypt)
- [ ] Security audit (pen testing)
- [ ] **Go Live**

**Deliverables:**
✅ 3-pit workshop fully operational
✅ Customer onboarding process documented
✅ 24/7 monitoring in place

---

### Phase 3: Franchise/Multi-Location Readiness - 4 Weeks

**Week 11-12: Multi-Tenancy Architecture**
- [ ] Workshop isolation (data segregation)
- [ ] Admin super-dashboard (view all workshops)
- [ ] Automated provisioning (new workshop onboarding)
- [ ] Bulk ESP32 firmware flashing tool

**Week 13: Billing & Subscription Management**
- [ ] Subscription tracking (payment due dates)
- [ ] Kill-switch automation (7-day grace period)
- [ ] Email reminders (payment overdue)
- [ ] Payment gateway integration (Razorpay/Stripe)

**Week 14: Documentation & Packaging**
- [ ] Installation guide (for franchise setup)
- [ ] Technical manual (troubleshooting)
- [ ] Sales materials (brochures, pricing sheets)
- [ ] **Ready for Scaling**

**Deliverables:**
✅ Plug-and-play expansion kit
✅ Self-service onboarding portal
✅ Automated billing system
✅ Franchise-ready deployment package

---

## 12. SECURITY MEASURES

### 12.1 Network Security

**VPN Tunnel (WireGuard):**
- All workshop devices connect via encrypted VPN
- No public IPs exposed for cameras/ESP32s
- Cloud server runs WireGuard server
- Workshop router acts as VPN client

**Firewall Rules:**
```bash
# Allow only VPN clients to access MQTT and RTSP
ufw allow from 10.8.0.0/24 to any port 1883  # MQTT
ufw allow from 10.8.0.0/24 to any port 8554  # RTSP
```

### 12.2 Application Security

**Authentication:**
- JWT tokens (HS256 algorithm, 256-bit secret)
- Token expiry: 24 hours (customers), 7 days (owner/staff)
- Refresh token mechanism for long sessions

**Password Security:**
- Bcrypt hashing (cost factor 12)
- Minimum 8 characters, 1 uppercase, 1 number
- Rate limiting: 5 failed attempts → 15-minute lockout

**API Security:**
- HTTPS only (HTTP redirects to HTTPS)
- CORS policy (whitelist allowed origins)
- Rate limiting: 100 requests/minute per IP
- SQL injection prevention (SQLAlchemy ORM, parameterized queries)

### 12.3 Data Security

**Encryption:**
- Database: Encrypted at rest (PostgreSQL TDE)
- Video storage: AES-256 encryption
- Credentials in transit: TLS 1.3

**Access Control:**
- Role-based permissions (Owner, Staff, Customer)
- Customer can ONLY see their assigned pit
- Staff can only see permitted pits
- Owner has full access

**Data Retention:**
- Sensor data: 90 days (then archived to cold storage)
- Video recordings: 7 days (configurable per workshop)
- Job history: Indefinite
- Logs: 30 days

---

## 13. MONITORING & ALERTS

### 13.1 System Health Monitoring

**PM2 Monitoring:**
```bash
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 50M
pm2 set pm2-logrotate:retain 7

# Monitor backend process
pm2 monit
```

**Database Monitoring:**
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check database size
SELECT pg_size_pretty(pg_database_size('ppf_monitoring'));
```

**MQTT Broker Monitoring:**
```bash
# Check active MQTT connections
mosquitto_sub -h localhost -t '$SYS/broker/clients/connected'
```

### 13.2 Alert Thresholds

| Alert Type | Threshold | Action | Notification |
|------------|-----------|--------|--------------|
| **High AQI** | >150 | Log + Dashboard alert | Owner SMS |
| **Critical AQI** | >200 | Log + Dashboard alert + Push | Owner SMS + App |
| **Temperature** | <15°C or >35°C | Log + Dashboard alert | Owner Dashboard |
| **Humidity** | >70% | Log + Dashboard alert | Owner Dashboard |
| **Camera Offline** | >30 seconds | Log + Dashboard alert | Owner SMS |
| **ESP32 Offline** | >60 seconds | Log + Dashboard alert | Owner Dashboard |
| **Server CPU** | >80% for 5 min | Log | Admin Email |
| **Disk Space** | >85% | Log | Admin Email |

### 13.3 Automated Alerts (Twilio SMS)

**Backend Alert Service:**
```python
from twilio.rest import Client

def send_sms_alert(to_phone, message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=message,
        from_='+1234567890',  # Twilio number
        to=to_phone
    )
    return message.sid

# Example usage
if aqi > 150:
    send_sms_alert(owner_phone, f"Alert: High AQI detected in Pit {pit_number}: {aqi}")
```

---

## 14. EXPANSION & FRANCHISE MODEL

### 14.1 Onboarding New Workshop (Automated)

**Step 1: Admin Creates Workshop**
```
Admin Dashboard → Add New Workshop
  - Workshop Name
  - Owner Name, Email, Phone
  - Address
  - Number of pits
  - Subscription plan
```

**Step 2: System Auto-Generates:**
- Workshop ID (e.g., `workshop_042`)
- Owner account (username, temp password)
- MQTT credentials (unique per workshop)
- VPN config file (WireGuard `.conf`)

**Step 3: Provisioning Email Sent to Owner:**
```
Subject: Welcome to PPF Monitoring System

Dear [Owner Name],

Your workshop has been activated!

Workshop ID: workshop_042
Login URL: https://ppf-monitoring.com/login
Username: owner_workshop_042
Temporary Password: TempPass123 (change on first login)

Next Steps:
1. Download VPN config: [link]
2. Download installation guide: [link]
3. Order hardware kits (3 pits): [link to order form]

Support: support@ppf-monitoring.com
```

### 14.2 Hardware Kit Provisioning

**Factory Pre-Configuration:**
- Each ESP32 flashed with unique `device_id` and `license_key`
- QR code label on device (contains `device_id` for easy setup)
- Pre-printed installation guide included in kit

**Workshop Setup Process:**
1. Receive hardware kit (camera + ESP32 + sensor + cables)
2. Mount camera in pit (overhead position)
3. Connect camera to PoE switch
4. Connect ESP32 to PoE switch (or power adapter)
5. Scan QR code on ESP32 → Auto-registers in cloud
6. Test in Owner Dashboard (see live stream + sensor data)

**Typical Installation Time:** 2-3 hours for 3 pits (by electrician)

### 14.3 Scaling Economics

**Cost to Add 1 New Workshop (3 pits):**
| Item | Cost (INR) |
|------|-----------|
| Hardware (3 kits) | ₹23,250 |
| Shipping | ₹500 |
| Installation support (remote) | ₹1,000 |
| **Total** | **₹24,750** |

**Revenue from 1 New Workshop (3 pits, first year):**
| Item | Revenue (INR) |
|------|--------------|
| Hardware markup | ₹12,750 (55% margin) |
| Subscription (3 × ₹1,500 × 12) | ₹54,000 |
| **Total Year 1** | **₹66,750** |

**Profit:** ₹66,750 - ₹24,750 = ₹42,000/workshop/year

**Break-Even:** 3 workshops (~₹1.26L revenue/year) covers development cost in Year 1

---

## 15. RISK ASSESSMENT

### 15.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Internet outage at workshop** | Medium | High | VPN auto-reconnect, local data buffering in ESP32 (SD card) |
| **Camera failure** | Low | Medium | Immediate alert to owner, spare camera in kit |
| **ESP32 failure** | Low | Medium | Spare ESP32 in kit, 24-hour replacement SLA |
| **Cloud server downtime** | Low | High | Use managed cloud (99.9% uptime SLA), automated backups |
| **Video streaming lag** | Medium | Medium | Optimize MediaMTX config, lower resolution option |
| **Database corruption** | Very Low | Critical | Daily backups to S3, WAL archiving, PITR capability |

### 15.2 Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Customer rejects transparency** | Low | High | Demo before full rollout, offer trial period |
| **Competitor enters market** | Medium | Medium | Patent key innovations, build network effects |
| **Subscription non-payment** | Medium | Medium | Kill-switch after 7-day grace, SMS reminders |
| **Hardware supply chain delays** | Medium | Low | Stock 10-20% buffer inventory |
| **Low adoption rate** | Medium | High | Targeted marketing, referral incentives |

### 15.3 Regulatory Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Privacy concerns (video recording)** | Low | Medium | Clear consent forms, GDPR compliance (if applicable) |
| **Data localization laws** | Low | Medium | Host in India if servicing Indian market |
| **Electrical safety certification** | Low | Low | Use CE/FCC certified hardware |

---

## 16. SUCCESS METRICS

### 16.1 MVP Success Criteria (Phase 1)

- [ ] System uptime: >99% for 30 days
- [ ] Video latency: <3 seconds
- [ ] Sensor data accuracy: ±2% (validated against calibrated instruments)
- [ ] Customer satisfaction: 4+ stars (out of 5) from 10+ customers
- [ ] Zero security incidents (unauthorized access)

### 16.2 Production Success Criteria (Phase 2)

- [ ] 3 pits operational for 90 days
- [ ] 50+ jobs completed successfully
- [ ] Owner reports 40% reduction in status inquiry calls
- [ ] Customer repeat rate: 30% within 6 months
- [ ] Zero data loss incidents

### 16.3 Scaling Success Criteria (Phase 3)

- [ ] Onboard 5 new workshops within 3 months
- [ ] 95%+ subscription renewal rate
- [ ] <1 hardware failure per 100 devices per year
- [ ] Self-service onboarding (no manual intervention)

---

## 17. NEXT STEPS (ACTION PLAN)

### Immediate (Next 2 Weeks)
1. **Finalize MVP scope with friend**
   - Confirm 1-pit demo budget: ₹1,11,350
   - Set demo date: [Target Date]

2. **Order hardware for MVP**
   - 1× Hikvision 2MP camera
   - 1× Olimex ESP32-GATEWAY-EA
   - 1× BME680 sensor
   - Cables, mounting kit

3. **Setup cloud infrastructure**
   - Provision DigitalOcean droplet
   - Install PostgreSQL, Mosquitto, Nginx
   - Configure domain + SSL

4. **Start development**
   - Backend: FastAPI + PostgreSQL schema
   - ESP32: Firmware skeleton + MQTT test

### Short-Term (Week 3-6)
5. **Complete MVP development** (follow Phase 1 timeline)
6. **Conduct internal testing** (all features working)
7. **Deploy to friend's workshop** (1 pit)
8. **Run pilot for 2 weeks** (gather feedback)

### Medium-Term (Week 7-14)
9. **Iterate based on feedback**
10. **Scale to 3 pits** (follow Phase 2 timeline)
11. **Document installation process**
12. **Prepare franchise kit**

### Long-Term (Month 4-6)
13. **Launch marketing campaign** (target 5 workshops)
14. **Onboard first paying customers**
15. **Optimize based on real-world data**
16. **Plan Phase 3 features** (mobile app, advanced analytics)

---

## 18. APPENDIX

### A. ESP32 Firmware Code Skeleton

```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <bsec.h>
#include "config.h"

Bsec iaqSensor;
WiFiClient espClient;
PubSubClient mqttClient(espClient);

void setup() {
  Serial.begin(115200);
  Wire.begin(I2C_SDA, I2C_SCL);
  
  // Initialize BME680
  iaqSensor.begin(BME680_I2C_ADDR_SECONDARY, Wire);
  checkIaqSensorStatus();
  
  // Set sample rate
  bsec_virtual_sensor_t sensorList[3] = {
    BSEC_OUTPUT_IAQ,
    BSEC_OUTPUT_SENSOR_HEAT_COMPENSATED_TEMPERATURE,
    BSEC_OUTPUT_SENSOR_HEAT_COMPENSATED_HUMIDITY
  };
  iaqSensor.updateSubscription(sensorList, 3, BSEC_SAMPLE_RATE_LP);
  
  // Connect to MQTT broker
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  connectMQTT();
}

void loop() {
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();
  
  if (iaqSensor.run()) {
    publishSensorData();
  }
  
  delay(SENSOR_READ_INTERVAL);
}

void publishSensorData() {
  char topic[100];
  sprintf(topic, "workshop/%s/%s/sensors", WORKSHOP_ID, PIT_ID);
  
  String payload = "{";
  payload += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  payload += "\"license_key\":\"" + String(LICENSE_KEY) + "\",";
  payload += "\"temperature\":" + String(iaqSensor.temperature) + ",";
  payload += "\"humidity\":" + String(iaqSensor.humidity) + ",";
  payload += "\"aqi\":" + String(iaqSensor.iaq) + ",";
  payload += "\"pressure\":" + String(iaqSensor.pressure) + "}";
  
  mqttClient.publish(topic, payload.c_str());
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  // Handle kill-switch command
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  if (message.indexOf("DISABLE") >= 0) {
    Serial.println("Device disabled by server");
    // Enter deep sleep or idle mode
    esp_deep_sleep_start();
  }
}
```

### B. Backend API Code Skeleton (FastAPI)

```python
from fastapi import FastAPI, WebSocket, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timedelta

app = FastAPI()
security = HTTPBearer()

# JWT configuration
SECRET_KEY = "your-256-bit-secret-key"
ALGORITHM = "HS256"

# Database models (using SQLAlchemy)
class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    workshop_id = Column(Integer, ForeignKey("workshops.id"))
    pit_id = Column(Integer, ForeignKey("pits.id"))
    customer_name = Column(String(100))
    car_model = Column(String(100))
    status = Column(String(20), default="waiting")
    estimated_end_time = Column(DateTime)
    # ... other fields

# Authentication
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

# API Endpoints
@app.post("/api/auth/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"user_id": user.id, "role": user.role})
    return {"access_token": token, "role": user.role}

@app.post("/api/jobs")
def create_job(job_data: JobCreate, token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    # Create new job
    job = Job(**job_data.dict())
    db.add(job)
    db.commit()
    
    # Create customer account
    customer_username = generate_username(job_data.customer_name)
    customer_password = generate_temp_password()
    customer = User(username=customer_username, password_hash=hash_password(customer_password), role="customer")
    db.add(customer)
    db.commit()
    
    return {"job_id": job.id, "customer_credentials": {"username": customer_username, "password": customer_password}}

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await websocket.accept()
    # Verify token
    # Subscribe to relevant topics
    # Push updates to client
```

### C. Camera Configuration (Hikvision Example)

```python
# Python script to configure Hikvision camera via API
import requests
from requests.auth import HTTPDigestAuth

CAMERA_IP = "192.168.1.100"
USERNAME = "admin"
PASSWORD = "admin123"

# Get RTSP URL
rtsp_url = f"rtsp://{USERNAME}:{PASSWORD}@{CAMERA_IP}:554/Streaming/Channels/101"

# Configure camera settings via API
def configure_camera():
    base_url = f"http://{CAMERA_IP}/ISAPI"
    auth = HTTPDigestAuth(USERNAME, PASSWORD)
    
    # Set video quality
    video_config = """
    <VideoEncoderConfiguration>
        <videoResolutionWidth>1920</videoResolutionWidth>
        <videoResolutionHeight>1080</videoResolutionHeight>
        <videoQualityControlType>CBR</videoQualityControlType>
        <constantBitRate>2048</constantBitRate>
    </VideoEncoderConfiguration>
    """
    
    response = requests.put(
        f"{base_url}/Streaming/channels/101",
        data=video_config,
        auth=auth,
        headers={"Content-Type": "application/xml"}
    )
    
    return response.status_code == 200
```

---

## CONCLUSION

This project plan provides a complete roadmap for building a production-ready PPF workshop monitoring system with:

✅ **Modular architecture** - Scale from 1 to unlimited pits  
✅ **Service model** - Remote licensing and kill-switch capability  
✅ **Camera flexibility** - Support existing cameras or provide tested models  
✅ **Franchise-ready** - Plug-and-play deployment for new locations  
✅ **Cost-effective** - ₹7,750/pit hardware, ₹1,500/pit/month subscription  
✅ **6-week MVP** - Demo-ready single-pit system  
✅ **14-week full deployment** - 3-pit production + franchise readiness

**Next Action:** Order MVP hardware and begin Phase 1 development.

---

**Document Version:** 1.0  
**Last Updated:** February 20, 2026  
**Author:** Technical Architecture Team  
**Status:** Ready for Implementation
