# PPF WORKSHOP MONITORING SYSTEM — CODE AUDIT PROMPT

> **How to Use This File:**
> 1. Open a NEW Claude chat (or any AI assistant)
> 2. Paste this ENTIRE document as your first message
> 3. Then attach/upload your project files as listed in the "Files to Upload" section
> 4. Claude will perform a deep code-level audit and produce a detailed report

---

## INSTRUCTIONS FOR THE AI AUDITOR

You are performing a **comprehensive technical code audit** of an IoT SaaS project called "PPF Workshop Monitoring System". This system monitors Paint Protection Film workshops using ESP32 sensors, MQTT, and a web dashboard.

### YOUR ROLE
You are a **Senior Technical Auditor** with expertise in:
- Python/FastAPI backend development
- React/TypeScript frontend development
- ESP32/Arduino embedded firmware
- Docker/DevOps infrastructure
- IoT security and MQTT protocols
- Database design (PostgreSQL/SQLAlchemy)

### AUDIT SCOPE
Perform a deep, line-by-line code audit covering these 10 categories:

---

## CATEGORY 1: BACKEND CODE QUALITY

Audit all files in `backend/src/` for:

- [ ] **Architecture**: Is the service layer properly separated from routes? Are there circular imports?
- [ ] **Error Handling**: Do all endpoints have try/except? Are errors logged? Are proper HTTP status codes returned?
- [ ] **Input Validation**: Are all Pydantic schemas comprehensive? Any missing field validations?
- [ ] **SQL Injection Risk**: Are all queries parameterized? Any raw SQL without parameterization?
- [ ] **Async/Await Issues**: Are all async database calls properly awaited? Any missing `await`?
- [ ] **N+1 Query Problems**: Are relationships loaded with `selectinload`/`joinedload` where needed?
- [ ] **Memory Leaks**: Any objects that grow unbounded? WebSocket connection tracking?
- [ ] **Configuration**: Are all secrets loaded from .env? Any hardcoded credentials?
- [ ] **Type Hints**: Are all function signatures properly typed?
- [ ] **Dead Code**: Any unused imports, unreachable code, or commented-out blocks?

**Output format for each issue found:**
```
FILE: backend/src/services/sensor_service.py
LINE: 45
SEVERITY: 🔴 HIGH / 🟡 MEDIUM / 🟢 LOW
ISSUE: Missing await on async database call
FIX: Add `await` before `session.execute()`
CODE BEFORE: result = session.execute(query)
CODE AFTER: result = await session.execute(query)
```

---

## CATEGORY 2: BACKEND API SECURITY

Audit all files in `backend/src/api/routes/` and `backend/src/api/dependencies.py` for:

- [ ] **Authentication Bypass**: Can any protected endpoint be accessed without JWT?
- [ ] **Authorization Flaws**: Can a `staff` role access `owner`-only endpoints? Can one workshop's user access another workshop's data?
- [ ] **JWT Implementation**: Is token expiry enforced? Is refresh token rotation implemented? Is the secret strong enough?
- [ ] **Password Security**: Is bcrypt used with sufficient cost factor? Are temporary passwords forced to change?
- [ ] **IDOR Vulnerabilities**: Can a user manipulate IDs to access other users' resources?
- [ ] **Rate Limiting**: Is there any protection against brute-force attacks?
- [ ] **CORS Configuration**: Is it properly restricted or wide open?
- [ ] **Input Sanitization**: Any XSS vectors in stored data that gets rendered?
- [ ] **File Upload Safety**: If file uploads exist, are they validated?
- [ ] **License Key Security**: Can the kill-switch be bypassed?

---

## CATEGORY 3: BACKEND TEST COVERAGE

Audit all files in `backend/tests/` for:

- [ ] **Coverage Gaps**: Which service functions lack unit tests?
- [ ] **Edge Case Testing**: Are boundary conditions tested (empty strings, max values, special characters)?
- [ ] **Negative Testing**: Are error paths tested (invalid auth, missing fields, unauthorized access)?
- [ ] **Integration Test Completeness**: Do API tests cover all CRUD operations for each resource?
- [ ] **Test Isolation**: Do tests properly clean up? Is there test pollution between runs?
- [ ] **Mock Quality**: Are external services (MQTT, WebSocket) properly mocked?
- [ ] **Assertion Quality**: Are tests checking specific values or just "not None"?
- [ ] **Missing Test Categories**: Are there tests for concurrent access, race conditions, data integrity?

**Output a test coverage gap matrix:**
```
| Module               | Unit Tests | Integration Tests | Edge Cases | Security Tests |
|---------------------|------------|-------------------|------------|----------------|
| auth_service        | ✅ 13      | ✅ 6              | ?          | ?              |
| sensor_service      | ✅ 29      | ?                 | ?          | ?              |
| job_service         | ?          | ✅ 14             | ?          | ?              |
| ...                 |            |                   |            |                |
```

---

## CATEGORY 4: FRONTEND CODE QUALITY

Audit all files in `frontend/src/` for:

- [ ] **Component Architecture**: Are components properly decomposed? Any god-components doing too much?
- [ ] **State Management**: Is Redux used appropriately? Any state that should be local instead of global?
- [ ] **TypeScript Strictness**: Are there `any` types? Missing interfaces? Unsafe type assertions?
- [ ] **Error Boundaries**: Are React error boundaries implemented to prevent white screens?
- [ ] **Memory Leaks**: Are useEffect cleanup functions implemented? Are intervals/timeouts cleared?
- [ ] **API Error Handling**: Do all API calls handle loading, success, and error states?
- [ ] **Accessibility**: Are ARIA labels, keyboard navigation, and screen reader support present?
- [ ] **Performance**: Are expensive computations memoized? Are large lists virtualized?
- [ ] **Hardcoded Values**: Any hardcoded API URLs, colors, or magic numbers?
- [ ] **Console Logs**: Any debug console.log statements left in production code?

---

## CATEGORY 5: FRONTEND SECURITY

Audit frontend for:

- [ ] **XSS Vulnerabilities**: Any use of `dangerouslySetInnerHTML`? User input rendered without sanitization?
- [ ] **Token Storage**: Where is JWT stored? localStorage (vulnerable to XSS) or httpOnly cookie?
- [ ] **Sensitive Data Exposure**: Any API keys, secrets, or sensitive config in frontend code?
- [ ] **CSRF Protection**: Are state-changing requests protected?
- [ ] **Route Guard Bypass**: Can protected pages be accessed by manipulating browser URL?
- [ ] **WebSocket Security**: Is the WebSocket connection authenticated? Can messages be spoofed?

---

## CATEGORY 6: ESP32 FIRMWARE

Audit all files in `firmware/src/` for:

- [ ] **Memory Management**: Any unbounded string concatenation? Buffer overflows? Stack vs heap usage?
- [ ] **Watchdog Timer**: Is WDT enabled to recover from firmware hangs?
- [ ] **Network Resilience**: What happens when WiFi/Ethernet disconnects? Does MQTT reconnect properly?
- [ ] **Sensor Error Handling**: What if a sensor returns NaN or fails to respond? Is there retry logic?
- [ ] **OTA Security**: Is OTA update authenticated? Can a malicious firmware be pushed?
- [ ] **Credential Security**: Are WiFi passwords and MQTT credentials stored securely?
- [ ] **Power Management**: Is deep sleep used between readings for battery scenarios?
- [ ] **JSON Payload Safety**: Can ArduinoJson buffer overflow? Is the buffer size adequate?
- [ ] **I2C/UART Stability**: Are timeouts implemented for sensor communication?
- [ ] **Timestamp Accuracy**: Is NTP sync handled when time server is unreachable?

---

## CATEGORY 7: DATABASE DESIGN

Audit `backend/src/models/` and migration files for:

- [ ] **Schema Design**: Are relationships properly defined? Any missing foreign keys?
- [ ] **Indexing**: Are frequently queried columns indexed? Any missing indexes on foreign keys?
- [ ] **Data Types**: Are column types appropriate? (e.g., BigInteger for sensor_data PK, proper timestamp types)
- [ ] **Constraints**: Are NOT NULL, UNIQUE, CHECK constraints properly applied?
- [ ] **Cascade Rules**: What happens when a workshop is deleted? Are orphan records prevented?
- [ ] **Migration Safety**: Can migrations be rolled back? Are they idempotent?
- [ ] **Data Retention**: Is there a strategy for archiving/purging old sensor data?
- [ ] **Multi-tenancy**: Is workshop data properly isolated? Can one tenant query another's data?

---

## CATEGORY 8: DOCKER & INFRASTRUCTURE

Audit `docker-compose.yml`, `Dockerfile`, and config files for:

- [ ] **Container Security**: Is the app running as non-root? Are images pinned to specific versions?
- [ ] **Secret Management**: Are secrets passed via environment variables, not baked into images?
- [ ] **Health Checks**: Do all services have health checks with appropriate intervals?
- [ ] **Resource Limits**: Are CPU/memory limits set on containers?
- [ ] **Network Isolation**: Are services on appropriate Docker networks?
- [ ] **Volume Persistence**: Is PostgreSQL data persisted? Are backups possible?
- [ ] **Log Management**: Are container logs rotated? Any risk of disk full?
- [ ] **Port Exposure**: Are only necessary ports exposed to the host?

---

## CATEGORY 9: MQTT & IoT PROTOCOL

Audit MQTT configuration and sensor data flow for:

- [ ] **MQTT Authentication**: Are all clients authenticated? Is anonymous access disabled?
- [ ] **MQTT ACL**: Can one device publish to another device's topic? Are topics properly restricted?
- [ ] **TLS Configuration**: Is MQTT traffic encrypted in transit?
- [ ] **QoS Settings**: Is QoS 1 appropriate? Should critical commands use QoS 2?
- [ ] **Topic Structure**: Is the topic hierarchy logical and scalable?
- [ ] **Payload Validation**: Is incoming MQTT data validated before database insertion?
- [ ] **Retained Messages**: Are retained messages used appropriately?
- [ ] **Last Will Testament**: Is LWT configured for device offline detection?

---

## CATEGORY 10: OVERALL ARCHITECTURE & SCALABILITY

Audit the overall system design for:

- [ ] **Single Points of Failure**: What happens if PostgreSQL goes down? MQTT broker? The single FastAPI instance?
- [ ] **Horizontal Scalability**: Can the backend scale to multiple instances? Any shared state issues?
- [ ] **Data Growth**: How will sensor_data table perform with millions of rows? Partitioning strategy?
- [ ] **WebSocket Scalability**: How many concurrent WebSocket connections can be handled?
- [ ] **MQTT Broker Scalability**: What's the limit on concurrent device connections?
- [ ] **API Response Times**: Are there any endpoints that will slow down as data grows?
- [ ] **Caching Strategy**: Is there any caching? Should Redis be added for frequently accessed data?
- [ ] **Monitoring**: How will you know when something breaks in production?
- [ ] **Disaster Recovery**: What's the RTO/RPO? Can the system be restored from backups?

---

## FILES TO UPLOAD

Upload these files/folders for the audit (prioritize in this order):

### Priority 1 — Backend Core (MUST UPLOAD)
```
backend/src/api/dependencies.py
backend/src/api/routes/auth.py
backend/src/api/routes/workshops.py
backend/src/api/routes/devices.py
backend/src/api/routes/sensors.py
backend/src/api/routes/jobs.py
backend/src/api/routes/alerts.py
backend/src/api/routes/websocket.py
backend/src/api/routes/streams.py
backend/src/api/routes/subscriptions.py
backend/src/api/routes/admin.py
backend/src/api/routes/health.py
backend/src/api/routes/users.py
backend/src/api/routes/pits.py
backend/src/services/auth_service.py
backend/src/services/sensor_service.py
backend/src/services/device_service.py
backend/src/services/job_service.py
backend/src/services/license_service.py
backend/src/services/mqtt_service.py
backend/src/services/websocket_service.py
backend/src/services/workshop_service.py
backend/src/services/notification_service.py
backend/src/config/settings.py
backend/src/config/database.py
backend/src/main.py
```

### Priority 2 — Models & Schemas
```
backend/src/models/user.py
backend/src/models/workshop.py
backend/src/models/pit.py
backend/src/models/device.py
backend/src/models/sensor_data.py
backend/src/models/job.py
backend/src/models/alert.py
backend/src/models/subscription.py
backend/src/models/audit_log.py
backend/src/models/device_command.py
backend/src/models/base.py
backend/src/schemas/ (all files)
backend/src/utils/constants.py
backend/src/utils/helpers.py
```

### Priority 3 — Tests
```
backend/tests/conftest.py
backend/tests/unit/test_auth_service.py
backend/tests/unit/test_helpers.py
backend/tests/unit/test_license_service.py
backend/tests/unit/test_sensor_service.py
backend/tests/integration/test_auth_endpoints.py
backend/tests/integration/test_workshop_endpoints.py
backend/tests/integration/test_device_endpoints.py
backend/tests/integration/test_job_endpoints.py
```

### Priority 4 — Firmware
```
firmware/src/main.cpp
firmware/src/sensors/dht22.cpp
firmware/src/sensors/dht22.h
firmware/src/sensors/pms5003.cpp
firmware/src/sensors/pms5003.h
firmware/src/sensors/bme680.cpp
firmware/src/sensors/bme680.h
firmware/src/mqtt/mqtt_handler.cpp
firmware/src/mqtt/mqtt_handler.h
firmware/src/network/network_manager.cpp
firmware/src/network/network_manager.h
firmware/src/config.h
firmware/platformio.ini
```

### Priority 5 — Frontend (Key Files)
```
frontend/src/App.tsx
frontend/src/services/api/client.ts
frontend/src/services/socket.ts
frontend/src/store/index.ts
frontend/src/store/authSlice.ts
frontend/src/store/pitsSlice.ts
frontend/src/store/jobsSlice.ts
frontend/src/store/alertsSlice.ts
frontend/src/store/devicesSlice.ts
frontend/src/pages/DashboardPage.tsx
frontend/src/pages/LoginPage.tsx
frontend/src/pages/JobDetailPage.tsx
frontend/src/pages/TrackingPage.tsx
frontend/src/components/ProtectedRoute.tsx
frontend/src/components/SensorCard.tsx
frontend/src/components/VideoPlayer.tsx
frontend/src/hooks/useWebSocket.ts
```

### Priority 6 — Infrastructure
```
docker-compose.yml
backend/Dockerfile
backend/requirements.txt
docker/mosquitto/mosquitto.conf
docker/mosquitto/acl.conf
docker/mediamtx/mediamtx.yml
backend/alembic/env.py
backend/database/migrations/001_initial_schema.sql
backend/database/migrations/002_seed_sensor_types.sql
.env.example
```

---

## EXPECTED OUTPUT FORMAT

After reviewing all uploaded files, produce the audit report in this exact structure:

### 1. EXECUTIVE SUMMARY
- Overall health score (X/100)
- Top 5 critical issues
- Top 5 strengths

### 2. CRITICAL ISSUES (Must Fix Before Demo)
For each issue:
- File path and line number
- Issue description
- Severity (🔴 CRITICAL / 🔴 HIGH)
- Exact code fix with before/after

### 3. HIGH PRIORITY ISSUES (Must Fix Before Production)
Same format as above with 🟡 MEDIUM severity

### 4. LOW PRIORITY IMPROVEMENTS (Nice to Have)
Same format with 🟢 LOW severity

### 5. SECURITY VULNERABILITIES
Dedicated section listing all security issues found, with OWASP category references

### 6. TEST COVERAGE GAPS
Matrix showing what's tested vs what's missing

### 7. PERFORMANCE CONCERNS
Any code patterns that will cause issues at scale

### 8. ARCHITECTURE RECOMMENDATIONS
Suggestions for improving the overall system design

### 9. CODE QUALITY METRICS
- Estimated technical debt score
- Code duplication percentage
- Type safety score
- Error handling coverage

### 10. PRIORITIZED FIX LIST
Numbered list of all issues sorted by priority, with estimated fix time for each

---

## PROJECT CONTEXT (For the Auditor)

**Business Model:** Hardware Kit (₹12,000) + Monthly Subscription (₹1,500/pit/month)
**Target Users:** PPF (Paint Protection Film) workshop owners in India
**Tech Stack:**
- Backend: Python 3.13 + FastAPI + SQLAlchemy + PostgreSQL
- Frontend: React 18 + TypeScript + Vite + Redux Toolkit + Tailwind CSS
- Firmware: ESP32 + Arduino Framework + PlatformIO
- Sensors: BME688 (temp/humidity/pressure/VOC) + PMS5003 (PM2.5 dust)
- Communication: MQTT (Mosquitto) + WebSocket
- Video: MediaMTX (RTSP/WebRTC/HLS)
- Infrastructure: Docker Compose + Nginx + Let's Encrypt
- Camera: Hikvision 2MP IP Camera

**Current State:**
- Backend: 126/126 tests passing, all API routes complete
- Frontend: 60+ files, 12 pages, 40+ components complete
- Firmware: All sensor drivers + MQTT + OTA complete (untested on hardware)
- Docker: 6-service stack configured
- Deployment: NOT DONE (no cloud server yet)
- Hardware: NOT ORDERED (shopping list finalized)

**Known Issues Already Identified:**
1. platformio.ini upload_flags were malformed (fixed)
2. CORS is set to wildcard (needs restriction)
3. No MQTT TLS configured
4. No rate limiting on API
5. Frontend never tested with live backend
6. Firmware never tested on real ESP32 hardware

Please be thorough, critical, and specific. I want actionable findings with exact code fixes, not vague recommendations.
