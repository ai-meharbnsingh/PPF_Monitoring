# PPF Workshop Monitoring System — Code Audit Report

> **Audit Date:** 2026-02-22  
> **Auditor:** Senior Technical Auditor (AI)  
> **Scope:** Backend (FastAPI), Frontend (React/TypeScript), Firmware (ESP32), Infrastructure (Docker)

---

## 1. EXECUTIVE SUMMARY

### Overall Health Score: 72/100

| Category | Score | Status |
|----------|-------|--------|
| Backend Code Quality | 75/100 | 🟡 Good with issues |
| Backend API Security | 68/100 | 🟡 Needs attention |
| Frontend Code Quality | 70/100 | 🟡 Acceptable |
| Frontend Security | 55/100 | 🔴 Needs immediate attention |
| Firmware Quality | 78/100 | 🟢 Good |
| Infrastructure | 65/100 | 🟡 Needs hardening |
| Test Coverage | 60/100 | 🟡 Incomplete |

### Top 5 Critical Issues

1. **JWT stored in localStorage** - XSS vulnerability, token theft risk
2. **No rate limiting on API** - Brute-force attack vector
3. **Missing database indexes** - Performance degradation at scale
4. **No audit log for sensitive operations** - Insufficient compliance trail
5. **MQTT without TLS** - Unencrypted IoT communication

### Top 5 Strengths

1. **Proper async/await patterns** throughout backend
2. **Comprehensive input validation** with Pydantic schemas
3. **Good separation of concerns** in service layer
4. **Watchdog timer implemented** in firmware
5. **Role-based access control** properly implemented

---

## 2. CRITICAL ISSUES (Must Fix Before Demo)

### 🔴 CRITICAL-001: JWT Token Stored in localStorage (XSS Vulnerability)

**File:** `frontend/src/store/slices/authSlice.ts`  
**Line:** 48-49  
**OWASP Category:** A07:2021 – Identification and Authentication Failures

**Issue:** JWT tokens are stored in localStorage, making them vulnerable to XSS attacks. Any malicious script can steal the token.

```typescript
// CODE BEFORE (vulnerable)
localStorage.setItem(LS_TOKEN_KEY, action.payload.token)
localStorage.setItem(LS_USER_KEY, JSON.stringify(action.payload.user))
```

**Fix:** Use httpOnly cookies for JWT storage, or implement proper CSP headers.

```typescript
// RECOMMENDED: Backend sets httpOnly cookie
// Frontend reads auth state from API response only, not localStorage
```

**Severity:** 🔴 CRITICAL  
**Effort:** 4-6 hours (backend cookie implementation)

---

### 🔴 CRITICAL-002: Missing Rate Limiting on API Endpoints

**File:** `backend/src/main.py`, all route files  
**OWASP Category:** A07:2021 – Identification and Authentication Failures

**Issue:** No rate limiting implemented on any API endpoint. Login, device commands, and other endpoints are vulnerable to brute-force attacks.

**Fix:** Add SlowAPI or custom rate limiting:

```python
# CODE TO ADD in main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to login endpoint in auth.py
@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, ...):
```

**Severity:** 🔴 CRITICAL  
**Effort:** 2-3 hours

---

### 🔴 CRITICAL-003: Missing Database Indexes on Foreign Keys

**File:** `backend/src/models/*.py`  
**Performance Impact:** N+1 queries, slow dashboard loading

**Issue:** No indexes defined on frequently queried foreign keys (workshop_id, pit_id, device_id, created_at).

**Fix:** Add indexes to models:

```python
# Add to SensorData model
__table_args__ = (
    Index('idx_sensor_data_workshop_id', 'workshop_id'),
    Index('idx_sensor_data_pit_id', 'pit_id'),
    Index('idx_sensor_data_created_at', 'created_at'),
    Index('idx_sensor_data_device_id_created_at', 'device_id', 'created_at'),
)
```

**Affected Tables:** sensor_data, jobs, alerts, device_commands

**Severity:** 🔴 HIGH  
**Effort:** 1-2 hours (create migration)

---

### 🔴 CRITICAL-004: No Audit Logging for Data Modifications

**File:** `backend/src/api/routes/*.py`  
**Compliance Risk:** Cannot track who changed what

**Issue:** Only login/logout is audited. No audit trail for:
- Job status changes
- Alert acknowledgments
- Device configuration changes
- User role changes

**Fix:** Add audit decorator:

```python
# Create audit decorator
def audit_action(action: str, resource_type: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            # Log audit after successful operation
            await log_audit_action(action, resource_type, ...)
            return result
        return wrapper
    return decorator

# Usage
@router.post("/jobs/{job_id}/status")
@audit_action("job.status_change", "job")
async def update_job_status(...):
```

**Severity:** 🔴 HIGH  
**Effort:** 4-6 hours

---

### 🔴 CRITICAL-005: MQTT Communication Without TLS

**File:** `docker/mosquitto/mosquitto.conf`, `firmware/src/connectivity/mqtt_handler.cpp`  
**OWASP IoT Category:** Insecure Communication

**Issue:** MQTT traffic is unencrypted. Device credentials and sensor data transmitted in plaintext.

**Fix:** 
1. Configure Mosquitto for TLS
2. Update firmware to use TLS port 8883
3. Add certificate bundle to firmware

```conf
# mosquitto.conf additions
listener 8883
protocol mqtt
cafile /mosquitto/certs/ca.crt
certfile /mosquitto/certs/server.crt
keyfile /mosquitto/certs/server.key
require_certificate false
tls_version tlsv1.2
```

**Severity:** 🔴 HIGH  
**Effort:** 4-8 hours (cert management + firmware update)

---

## 3. HIGH PRIORITY ISSUES (Must Fix Before Production)

### 🟡 HIGH-001: Missing CORS Restriction

**File:** `backend/config/settings.yaml`  
**Line:** 18-20

**Issue:** CORS origins include localhost ports which is acceptable for dev, but needs strict restriction in production.

```yaml
# CURRENT
cors_origins:
  - "http://localhost:3000"
  - "http://localhost:5173"
```

**Fix:** Make CORS origins environment-specific:

```yaml
# Production should only allow specific domains
cors_origins:
  - "https://dashboard.ppf-monitor.com"
```

**Severity:** 🟡 MEDIUM  
**Effort:** 30 minutes

---

### 🟡 HIGH-002: WebSocket Token in Query Parameter

**File:** `backend/src/api/routes/websocket.py`  
**Line:** 32

**Issue:** JWT token passed as query parameter may be logged by proxies and servers.

```python
@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
):
```

**Fix:** Use subprotocol header for token:

```python
# Client sends token in Sec-WebSocket-Protocol header
# Server extracts from headers instead of query params
```

**Severity:** 🟡 MEDIUM  
**Effort:** 2-3 hours

---

### 🟡 HIGH-003: Missing Input Sanitization in Alert Messages

**File:** `backend/src/services/sensor_service.py`  
**Line:** 235-246

**Issue:** Sensor values are interpolated into alert messages without sanitization. Potential XSS if messages are rendered unescaped.

```python
# CURRENT
message=(
    f"Temperature {reading.temperature:.1f}°C is outside safe range "
    f"({temp_min}°C — {temp_max}°C)"
),
```

**Fix:** Sanitize values or use parameterized messages in frontend.

**Severity:** 🟡 MEDIUM  
**Effort:** 1 hour

---

### 🟡 HIGH-004: Race Condition in Device Command Status

**File:** `backend/src/services/device_service.py`  
**Line:** 200-222

**Issue:** Command status is set to SENT before actual MQTT publish. If publish fails, status remains SENT instead of FAILED.

```python
# CURRENT (problematic)
cmd_record.status = DeviceCommandStatus.SENT.value  # Set before actual send
await publish_device_command(...)  # May fail after status update
```

**Fix:**

```python
# FIX
async def send_device_command(...):
    cmd_record = DeviceCommandModel(...)
    db.add(cmd_record)
    await db.flush()
    
    try:
        await publish_device_command(...)  # Publish first
        cmd_record.status = DeviceCommandStatus.SENT.value  # Then update status
    except Exception as exc:
        cmd_record.status = DeviceCommandStatus.FAILED.value
        raise
    
    await db.commit()
```

**Severity:** 🟡 MEDIUM  
**Effort:** 1-2 hours

---

### 🟡 HIGH-005: N+1 Query in Latest Readings

**File:** `backend/src/api/routes/sensors.py`  
**Line:** 60-72

**Issue:** Loop queries database for each pit individually.

```python
# CURRENT (N+1 problem)
for pit in pits:
    summary = await _build_latest_summary(db, pit, thresholds)  # One query per pit
```

**Fix:** Use single query with window functions:

```python
# Use DISTINCT ON or ROW_NUMBER() for single query
query = select(SensorData).distinct(SensorData.pit_id).order_by(
    SensorData.pit_id, SensorData.created_at.desc()
)
```

**Severity:** 🟡 MEDIUM  
**Effort:** 3-4 hours

---

## 4. LOW PRIORITY IMPROVEMENTS (Nice to Have)

### 🟢 LOW-001: Missing API Versioning Strategy

**File:** `backend/src/main.py`

**Issue:** API prefix is `/api/v1` but no deprecation or versioning strategy exists for v2.

**Recommendation:** Add sunset headers and API version negotiation.

**Severity:** 🟢 LOW

---

### 🟢 LOW-002: Hardcoded Status Values

**File:** `backend/src/api/routes/pits.py`  
**Line:** 40

```python
status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
```

**Issue:** Magic string "active" should use enum constant.

**Severity:** 🟢 LOW

---

### 🟢 LOW-003: Frontend Console.log Statements

**File:** Check all frontend files for `console.log`

**Issue:** Debug logging may expose sensitive information in production.

**Fix:** Remove or use proper logging utility.

**Severity:** 🟢 LOW

---

### 🟢 LOW-004: Missing Loading States in Frontend

**File:** Multiple frontend components

**Issue:** Some async operations don't show loading states.

**Severity:** 🟢 LOW

---

## 5. SECURITY VULNERABILITIES

| ID | Category | OWASP Ref | Severity | Status |
|----|----------|-----------|----------|--------|
| SEC-001 | JWT in localStorage | A07:2021 | 🔴 Critical | Open |
| SEC-002 | No Rate Limiting | A07:2021 | 🔴 Critical | Open |
| SEC-003 | MQTT without TLS | IoT Top 10 | 🔴 High | Open |
| SEC-004 | CORS misconfiguration | A05:2021 | 🟡 Medium | Open |
| SEC-005 | WebSocket token in URL | A08:2021 | 🟡 Medium | Open |
| SEC-006 | Missing security headers | A05:2021 | 🟡 Medium | Open |
| SEC-007 | No input length limits | A03:2021 | 🟡 Medium | Open |

### SEC-006: Missing Security Headers

**Fix:** Add middleware in FastAPI:

```python
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

## 6. TEST COVERAGE GAPS

| Module | Unit Tests | Integration Tests | Edge Cases | Security Tests |
|--------|------------|-------------------|------------|----------------|
| auth_service | ✅ 13 | ✅ 6 | 🟡 Partial | ❌ None |
| sensor_service | ✅ 29 | ❌ None | 🟡 Partial | ❌ None |
| device_service | ❌ None | ✅ 14 | 🟡 Partial | ❌ None |
| job_service | ❌ None | ✅ 14 | ❌ None | ❌ None |
| mqtt_service | ❌ None | ❌ None | ❌ None | ❌ None |
| websocket_service | ❌ None | ❌ None | ❌ None | ❌ None |
| license_service | ✅ 8 | ❌ None | ✅ Good | ❌ None |

### Missing Test Categories:

1. **Concurrent access tests** - Multiple users modifying same job
2. **Race condition tests** - Simultaneous alert generation
3. **Load tests** - WebSocket connection limits
4. **Fuzz tests** - Invalid MQTT payloads
5. **Security tests** - IDOR attempts, privilege escalation

---

## 7. PERFORMANCE CONCERNS

### PERF-001: Unbounded Sensor Data Growth

**Table:** `sensor_data`

**Issue:** No data retention strategy. At 10-second intervals per device:
- 1 device = 8,640 rows/day
- 10 devices = 86,400 rows/day
- 1 year = ~31M rows

**Recommendation:** Implement time-based partitioning or archiving:

```sql
-- Create monthly partitions
CREATE TABLE sensor_data_2026_02 PARTITION OF sensor_data
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- Archive old data
INSERT INTO sensor_data_archive SELECT * FROM sensor_data 
    WHERE created_at < NOW() - INTERVAL '90 days';
DELETE FROM sensor_data WHERE created_at < NOW() - INTERVAL '90 days';
```

---

### PERF-002: No Caching Layer

**Issue:** Alert configs, user profiles fetched repeatedly without caching.

**Recommendation:** Add Redis cache:

```python
from redis.asyncio import Redis
redis = Redis.from_url("redis://localhost")

@cache(ttl=300)
async def get_alert_config(workshop_id: int):
    ...
```

---

## 8. ARCHITECTURE RECOMMENDATIONS

### REC-001: Implement Circuit Breaker Pattern

For MQTT and external service calls:

```python
from pybreaker import CircuitBreaker

mqtt_breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

@mqtt_breaker
def publish_device_command(...):
    ...
```

### REC-002: Event Sourcing for Job Status

Current job status history is append-only but not truly event-sourced. Consider using outbox pattern for reliable WebSocket notifications.

### REC-003: Horizontal Scaling Preparation

WebSocket connections won't scale horizontally with current in-memory manager. Consider Redis pub/sub for multi-instance deployment.

---

## 9. CODE QUALITY METRICS

| Metric | Score | Notes |
|--------|-------|-------|
| Type Safety | 85% | Good use of TypeScript and Python typing |
| Documentation | 70% | Docstrings present, some gaps |
| Error Handling | 75% | Try/catch present, inconsistent error messages |
| Code Duplication | 15% | Role checks repeated in many routes |
| Test Coverage | 45% | Backend ~60%, Frontend ~30% |
| Technical Debt | Medium | ~2 weeks to address all high/critical issues |

---

## 10. PRIORITIZED FIX LIST

| # | Issue | Severity | Effort (hrs) | Dependencies |
|---|-------|----------|--------------|--------------|
| 1 | JWT in localStorage → httpOnly cookies | 🔴 Critical | 6 | Backend changes |
| 2 | Add rate limiting | 🔴 Critical | 3 | None |
| 3 | Add database indexes | 🔴 Critical | 2 | Migration |
| 4 | MQTT TLS configuration | 🔴 Critical | 8 | Certificate setup |
| 5 | Audit logging | 🔴 High | 6 | None |
| 6 | Fix race condition in device commands | 🟡 Medium | 2 | None |
| 7 | Optimize N+1 sensor query | 🟡 Medium | 4 | None |
| 8 | WebSocket token in header | 🟡 Medium | 3 | Frontend + Backend |
| 9 | CORS production restriction | 🟡 Medium | 0.5 | Config only |
| 10 | Add security headers | 🟡 Medium | 1 | None |
| 11 | Data retention policy | 🟡 Medium | 8 | Migration |
| 12 | Redis caching layer | 🟢 Low | 8 | Infrastructure |

**Total Critical/High Effort:** ~27 hours  
**Total All Issues:** ~51.5 hours

---

## APPENDIX A: Files Requiring Changes

### Backend
- `backend/src/main.py` - Rate limiting, security headers
- `backend/src/api/routes/auth.py` - Cookie support
- `backend/src/api/routes/websocket.py` - Token in header
- `backend/src/api/routes/sensors.py` - N+1 fix
- `backend/src/services/device_service.py` - Race condition
- `backend/src/models/*.py` - Add indexes
- `backend/src/config/settings.yaml` - CORS

### Frontend
- `frontend/src/store/slices/authSlice.ts` - Remove localStorage
- `frontend/src/api/client.ts` - Cookie support
- `frontend/src/services/websocket.ts` - Token in header

### Firmware
- `firmware/src/connectivity/mqtt_handler.cpp` - TLS support
- `firmware/include/config.h` - TLS port config

### Infrastructure
- `docker/mosquitto/mosquitto.conf` - TLS listener
- `docker-compose.yml` - Volume mounts for certs

---

## APPENDIX B: Compliance Checklist

| Requirement | Status | Notes |
|-------------|--------|-------|
| Authentication | ✅ Pass | JWT with proper expiry |
| Authorization | ✅ Pass | RBAC implemented |
| Audit Logging | 🔴 Fail | Only login audited |
| Data Encryption at Rest | 🟡 Partial | PostgreSQL encryption TBD |
| Data Encryption in Transit | 🔴 Fail | MQTT not encrypted |
| Input Validation | ✅ Pass | Pydantic schemas |
| Error Handling | 🟡 Partial | Missing some edge cases |
| Rate Limiting | 🔴 Fail | Not implemented |
| Secure Headers | 🔴 Fail | Not implemented |

---

*End of Audit Report*
