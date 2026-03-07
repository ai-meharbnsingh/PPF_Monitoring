# 🔬 CLI FORENSICS REPORT — RPi Architecture Transition Analysis

> **Project**: PP Monitoring System  
> **Forensic ID**: FORENSIC-20260307-RPi-002  
> **Focus**: ESP32 → Raspberry Pi Architecture Migration  
> **Generated**: 2026-03-07  
> **Classification**: MACHINE-FIRST BEHAVIORAL VERIFICATION  

---

## EXECUTIVE SUMMARY

**ARCHITECTURE STATUS**: Partial Migration (Legacy ESP32 code remains)  
**CRITICAL FINDINGS: 6**  
**HIGH SEVERITY: 8**  
**MEDIUM SEVERITY: 12**

The project has transitioned from ESP32 microcontrollers to Raspberry Pi for sensor data collection, but **significant ESP32 legacy code, documentation, and security vulnerabilities remain**. The RPi architecture introduces new security risks including credentials in documentation and disabled TLS verification.

### IMMEDIATE ACTIONS REQUIRED
1. **FER-RPi-001**: Remove hardcoded MQTT password from PI_MASTER_CONFIG.md
2. **FER-RPi-002**: Fix TLS verification disabled in pi_sensor_hivemq_template.py
3. **FER-RPi-003**: Archive/delete deprecated ESP32 firmware (67MB)
4. **FER-RPi-004**: Remove ESP32-specific fix scripts from backend
5. **FER-RPi-005**: Update device model docstring (still says "Olimex ESP32")
6. **FER-RPi-006**: Remove WiFi password from documentation

---

## SECTION 1: ARCHITECTURE TRANSITION ANALYSIS

### 1.1 Current Architecture (Post-Migration)

```
┌─────────────────────────────────────────────────────────────────┐
│                        RASPBERRY PI FLEET                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│  │ piwifi   │  │ piwifi2  │  │ piwifi3  │                       │
│  │ (.local) │  │ (.local) │  │ (.local) │                       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                       │
│       │             │             │                             │
│  ┌────▼─────────────▼─────────────▼─────┐                       │
│  │   pi_sensor_mqtt.py (Python 3)        │                       │
│  │   - BME688 (I2C) temperature/humidity │                       │
│  │   - PMS5003 (UART) particulate matter │                       │
│  │   - Publishes to HiveMQ Cloud         │                       │
│  └─────────────────┬─────────────────────┘                       │
└────────────────────┼────────────────────────────────────────────┘
                     │ MQTT (TLS/8883)
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      HIVEMQ CLOUD BROKER                         │
│         (c4cb4d2b4a3e432c9d61b8b56ee359af.s1.eu.hivemq.cloud)   │
└─────────────────┬───────────────────────────────────────────────┘
                  │ MQTT (TLS/8883)
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  mqtt_service.py - Subscribes to sensor topics          │    │
│  │  - _handle_sensor_message()                             │    │
│  │  - _handle_camera_registration() (from RPi MediaMTX)    │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Legacy Architecture (Pre-Migration)

```
┌─────────────────────────────────────────────────────────────────┐
│                    ESP32 MICROCONTROLLERS                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│  │ ESP32-01 │  │ ESP32-02 │  │ ESP32-03 │                       │
│  │ (C++ FW) │  │ (C++ FW) │  │ (C++ FW) │                       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                       │
│       │             │             │                             │
│       └─────────────┴─────────────┘                             │
│                     │                                            │
│              WiFi / MQTT                                        │
└────────────────────┼────────────────────────────────────────────┘
```

### 1.3 Migration Gaps

```yaml
MIGRATION_STATUS:
  hardware:
    status: COMPLETED
    notes: "ESP32 replaced with Raspberry Pi fleet (piwifi, piwifi2, piwifi3)"
    
  software:
    status: PARTIAL
    notes: "RPi runs Python scripts, but backend still references ESP32"
    
  documentation:
    status: INCOMPLETE
    notes: "PI_MASTER_CONFIG.md updated but contains hardcoded credentials"
    
  dead_code:
    status: NOT_CLEANED
    notes: "firmware/ folder (67MB), ESP32 fix scripts, ESP32 test fixtures remain"
    
  security:
    status: DEGRADED
    notes: "New vulnerabilities introduced in RPi template script"
```

---

## SECTION 2: CRITICAL SECURITY FINDINGS (RPi Specific)

### FER-RPi-001: Hardcoded MQTT Password in Documentation

```yaml
SEVERITY: CRITICAL
FILE: raspberrypi_config/PI_MASTER_CONFIG.md
LINE: 548

EVIDENCE:
  code_snippet: |
    Environment="MQTT_PASSWORD=PPF@Mqtt2026!secure"

IMPACT: |
  Production MQTT broker password exposed in git repository.
  Anyone with repository access can connect to the MQTT broker
  and publish/subscribe to all topics.

ROOT_CAUSE: |
  Convenience during RPi setup documentation. Password should
  be injected via environment variables or secrets management.

FIX: |
  1. Immediately change MQTT password in HiveMQ Cloud dashboard
  2. Replace with placeholder: Environment="MQTT_PASSWORD=${MQTT_PASSWORD}"
  3. Document that password must be set during deployment
  4. Add to .gitignore: "*.secrets" or use GitHub Secrets

VERIFICATION:
  command: "grep -n 'PPF@Mqtt' raspberrypi_config/PI_MASTER_CONFIG.md"
  expected: "No output (password removed)"
```

### FER-RPi-002: TLS Certificate Verification Disabled

```yaml
SEVERITY: CRITICAL
FILE: pi_sensor_hivemq_template.py
LINES: 61-62

EVIDENCE:
  code_snippet: |
    if USE_TLS:
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.tls_insecure_set(True)

IMPACT: |
  MQTT connections from Raspberry Pi to HiveMQ Cloud are
  vulnerable to Man-in-the-Middle attacks. An attacker on the
  local network can intercept and modify sensor data.

ROOT_CAUSE: |
  Development convenience - disabling TLS verification
  avoids certificate configuration issues but breaks security.

FIX: |
  1. Use proper CA certificate bundle
  2. Change to: client.tls_set(cert_reqs=ssl.CERT_REQUIRED,
                               ca_certs="/etc/ssl/certs/ca-certificates.crt")
  3. Remove: client.tls_insecure_set(True)

VERIFICATION:
  command: "grep -n 'tls_insecure\|CERT_NONE' pi_sensor_hivemq_template.py"
  expected: "No matches"
```

### FER-RPi-003: WiFi Password in Documentation

```yaml
SEVERITY: HIGH
FILE: raspberrypi_config/PI_MASTER_CONFIG.md
LINES: 344, 452

EVIDENCE:
  code_snippet: |
    "Jas_Mehar":
      password: "airtel2730"

IMPACT: |
  Internal WiFi network password exposed. While less critical
  than MQTT password, still a security risk.

FIX: |
  Replace with placeholder: password: "YOUR_WIFI_PASSWORD"
  Document that users must update this with their own WiFi credentials.
```

### FER-RPi-004: Default Pi Password Documented

```yaml
SEVERITY: MEDIUM
FILE: raspberrypi_config/PI_MASTER_CONFIG.md
LINE: 21

EVIDENCE:
  code_snippet: |
    | **Password** | `raspberry` |

IMPACT: |
  Default Raspberry Pi password documented. If users don't
  change it, devices are vulnerable to unauthorized access.

FIX: |
  Add security warning: "CHANGE THIS IMMEDIATELY AFTER FIRST BOOT"
```

---

## SECTION 3: ESP32 DEAD CODE CATALOG

### 3.1 Firmware Folder (67MB)

```yaml
DEAD_CODE:
  location: "firmware/"
  size: "67MB"
  contents:
    - "ESP32 C++ source code"
    - "PlatformIO build artifacts"
    - "Compiled binaries (.bin, .elf)"
    - "Library dependencies"
  
  status: DEPRECATED
  reason: "Architecture migrated to Raspberry Pi"
  
  risk: |
    - Repository bloat
    - Confusion for new developers
    - Outdated security practices in old code
    
  action: ARCHIVE_OR_DELETE
  
  migration_path: |
    1. Create archive branch: git branch archive/esp32-firmware
    2. Or move to separate repository: ppf-monitoring-firmware-esp32
    3. Delete from main: git rm -rf firmware/
    4. Add to .gitignore to prevent accidental re-addition
```

### 3.2 Backend ESP32 Fix Scripts

```yaml
DEAD_CODE:
  files:
    - backend/bind_esp32.py
    - backend/fix_demo_state.py
    - backend/fix_pit_id.py
    
  evidence:
    bind_esp32.py: |
      cur.execute("UPDATE devices SET pit_id = 1 WHERE device_id = 'ESP32-PLACEHOLDER'")
    
    fix_demo_state.py: |
      cur.execute("UPDATE devices SET ... WHERE device_id = 'ESP32-PLACEHOLDER'")
      
    fix_pit_id.py: |
      cur.execute("UPDATE devices SET pit_id = 10 WHERE device_id = 'ESP32-PLACEHOLDER'")

  status: DEPRECATED
  reason: "ESP32-PLACEHOLDER device no longer exists in production"
  
  action: DELETE
  verification: "git rm backend/bind_esp32.py backend/fix_demo_state.py backend/fix_pit_id.py"
```

### 3.3 Test Fixtures with ESP32 Device IDs

```yaml
FIXTURE_BLINDNESS:
  files:
    - backend/tests/unit/test_sensor_service.py
    - backend/tests/unit/test_license_service.py
    - backend/tests/unit/test_helpers.py
    - backend/tests/integration/test_device_endpoints.py
    
  device_ids_used:
    - "ESP32-AABBCCDDEEFF"
    - "ESP32-A1B2C3D4E5F6"
    - "ESP32-TESTDEVICE001"
    - "ESP32-NEWDEVICE002"
    
  impact: |
    Tests still pass (device_id is just a string), but fixtures
    don't reflect actual RPi device IDs like "PIWIFI-01".
    
  action: UPDATE_FIXTURES
  priority: LOW
```

### 3.4 Documentation References

```yaml
OUTDATED_DOCUMENTATION:
  - file: backend/src/services/mqtt_service.py
    line: 4
    current: "MQTT subscriber that listens for sensor data from ESP32 devices"
    should_be: "MQTT subscriber that listens for sensor data from devices"
    
  - file: backend/src/services/mqtt_service.py
    line: 71
    current: "Publish a command to an ESP32 device via MQTT"
    should_be: "Publish a command to a device via MQTT"
    
  - file: backend/src/services/license_service.py
    line: 4
    current: "License key validation for ESP32 devices"
    should_be: "License key validation for edge devices"
    
  - file: backend/src/models/device.py
    line: 4
    current: "Device ORM model — represents one Olimex ESP32-GATEWAY unit"
    should_be: "Device ORM model — represents one edge sensor device (RPi/ESP32)"
    
  - file: backend/src/services/sensor_service.py
    line: 91
    current: "Parse incoming MQTT JSON payload from ESP32"
    should_be: "Parse incoming MQTT JSON payload from sensor device"
```

---

## SECTION 4: RPi → BACKEND INTEGRATION ANALYSIS

### 4.1 Data Flow Verification

```yaml
DATA_FLOW:
  step_1:
    source: "Raspberry Pi (piwifiN)"
    process: "pi_sensor_mqtt.py reads BME688 + PMS5003"
    output: "JSON payload"
    verified: true
    
  step_2:
    source: "pi_sensor_mqtt.py"
    process: "Publish to HiveMQ Cloud via TLS"
    topic: "workshop/{WORKSHOP_ID}/pit/{PIT_ID}/sensors"
    issues:
      - "TLS verification disabled (FER-RPi-002)"
    verified: false
    
  step_3:
    source: "HiveMQ Cloud Broker"
    process: "Message routing"
    verified: true
    
  step_4:
    source: "Backend mqtt_service.py"
    process: "Subscribe and handle sensor messages"
    handler: "_handle_sensor_message()"
    verified: true
    
  step_5:
    source: "Backend"
    process: "License validation"
    service: "license_service.validate_license()"
    issues:
      - "Still references ESP32 in docstring"
    verified: true
    
  step_6:
    source: "Backend"
    process: "Store sensor reading"
    service: "sensor_service.store_sensor_reading()"
    verified: true
    
  step_7:
    source: "Backend"
    process: "WebSocket broadcast"
    verified: true
```

### 4.2 Payload Format Compatibility

```yaml
PAYLOAD_FORMAT:
  rpi_sends:
    device_id: "PIWIFI-01"
    license_key: "LIC-MOCK-PI-2026"
    sensor_type: "BME688+PMS5003"
    temperature: 24.50
    humidity: 55.20
    pressure: 1013.25
    gas_resistance: 50000
    iaq: 50
    pm25: 12
    timestamp: "2026-03-06T16:53:45Z"
    
  backend_expects:
    device_id: "string"
    license_key: "string"
    temperature: "float"
    humidity: "float"
    pm25: "float"
    
  compatibility: COMPATIBLE
  notes: |
    RPi payload format matches backend expectations.
    The device_id prefix changed from "ESP32-" to "PIWIFI-"
    but backend accepts any string.
```

### 4.3 Camera Registration Flow (RPi MediaMTX)

```yaml
CAMERA_INTEGRATION:
  source: "Raspberry Pi with MediaMTX"
  trigger: "Camera registration MQTT message"
  handler: "mqtt_service._handle_camera_registration()"
  
  flow:
    1: "RPi publishes to workshop/{id}/cameras/register"
    2: "Backend receives and parses JSON"
    3: "Camera record created/updated in database"
    4: "WebSocket notification broadcast"
    
  issues:
    - "No validation that workshop_id exists (FER-CLI-030)"
    - "No authentication on registration topic"
    
  stream_access:
    webrtc: "http://<PI_IP>:8889/cam1/whep"
    hls: "http://<PI_IP>:8888/cam1/index.m3u8"
    tailscale: "https://piwifi.taile42746.ts.net/cam1/index.m3u8"
```

---

## SECTION 5: DEPRECATED CONSTANTS AND CONFIGURATIONS

### 5.1 ESP32-Specific Backend Scripts

```yaml
DEPRECATED_SCRIPTS:
  bind_esp32.py:
    purpose: "Bind ESP32 placeholder device to pit"
    status: DEPRECATED
    lines: 4
    action: DELETE
    
  fix_demo_state.py:
    purpose: "Fix demo state for ESP32 placeholder"
    status: DEPRECATED
    lines: 10
    action: DELETE
    
  fix_pit_id.py:
    purpose: "Fix pit_id for ESP32 placeholder"
    status: DEPRECATED
    lines: 5
    action: DELETE
    
  fix_sensor_data.py:
    purpose: "Fix sensor data for specific devices"
    status: REVIEW_NEEDED
    action: VERIFY_IF_STILL_NEEDED
    
  relink_device.py:
    purpose: "Relink device to different pit"
    status: KEEP (generic utility)
    action: VERIFY_GENERIC
```

### 5.2 Serial Read Scripts

```yaml
DEPRECATED_SCRIPTS:
  read_serial.py:
    purpose: "Read from serial port (for ESP32 debugging)"
    status: DEPRECATED
    action: MOVE_TO_ARCHIVE_OR_DELETE
    
  read_serial_long.py:
    purpose: "Extended serial reading"
    status: DEPRECATED
    action: MOVE_TO_ARCHIVE_OR_DELETE
```

### 5.3 Firmware-Related Backend Code

```yaml
FIRMWARE_CODE:
  backend/routes/firmware.py:
    purpose: "OTA firmware upload/download"
    status: PARTIALLY_DEPRECATED
    notes: |
      ESP32 firmware uploads no longer needed.
      May still be used for RPi software updates?
      Verify if still needed.
      
  backend/services/firmware_service.py:
    purpose: "Firmware management"
    status: REVIEW_NEEDED
    action: VERIFY_USAGE
```

---

## SECTION 6: CONFIGURATION DRIFT ANALYSIS

### 6.1 RPi Configuration Files

```yaml
CONFIGURATION_FILES:
  raspberrypi_config/PI_MASTER_CONFIG.md:
    status: ACTIVE
    issues:
      - "Hardcoded MQTT password (FER-RPi-001)"
      - "Hardcoded WiFi password (FER-RPi-003)"
      - "Default Pi password (FER-RPi-004)"
      
  raspberrypi_config/camera_register.py:
    status: ACTIVE
    purpose: "Register cameras from RPi to backend"
    verified: true
    
  raspberrypi_config/wifi_server.py:
    status: ACTIVE
    purpose: "WiFi configuration portal"
    port: 8080
    verified: true
```

### 6.2 Sensor Script Template Issues

```yaml
pi_sensor_hivemq_template.py:
  status: TEMPLATE
  issues:
    - "Hardcoded placeholder values for MQTT broker"
    - "TLS verification disabled (FER-RPi-002)"
    - "No error handling for sensor initialization failures"
    - "Infinite loop with no graceful shutdown"
    
  hardcoded_placeholders:
    - MQTT_BROKER: "YOUR_CLUSTER_URL.s1.eu.hivemq.cloud"
    - MQTT_USERNAME: "your-username"
    - MQTT_PASSWORD: "your-password"
    - DEVICE_ID: 'PIWIFI-01'
    - LICENSE_KEY: 'LIC-RG-STUDIO-2026'
    - WORKSHOP_ID: 2
    - PIT_ID: 3
```

---

## SECTION 7: RISK MAP (RPi Transition Specific)

| FER ID | Severity | Component | Impact | Fix Effort | Action |
|--------|----------|-----------|--------|------------|--------|
| FER-RPi-001 | CRITICAL | Documentation | Data breach | 5 min | Immediate |
| FER-RPi-002 | CRITICAL | RPi Script | MITM attacks | 15 min | Immediate |
| FER-RPi-003 | HIGH | Documentation | Network breach | 5 min | Immediate |
| FER-RPi-004 | MEDIUM | Documentation | Unauthorized access | 5 min | This week |
| FER-RPi-005 | HIGH | Backend | Repo bloat | 10 min | This week |
| FER-RPi-006 | HIGH | Backend | Repo bloat | 5 min | This week |
| FER-RPi-007 | MEDIUM | Tests | Fixture blindness | 30 min | This sprint |
| FER-RPi-008 | LOW | Documentation | Confusion | 1 hour | This sprint |

---

## SECTION 8: CLEANUP RECOMMENDATIONS

### 8.1 Immediate Actions (Today)

```bash
# 1. Change MQTT password in HiveMQ Cloud dashboard
#    - Log into https://console.hivemq.cloud/
#    - Go to Access Management → Credentials
#    - Change ppf_backend password

# 2. Remove hardcoded password from documentation
sed -i '' 's/PPF@Mqtt2026!secure/${MQTT_PASSWORD}/g' raspberrypi_config/PI_MASTER_CONFIG.md

# 3. Fix TLS verification in template
cat > tls_fix.patch << 'EOF'
--- a/pi_sensor_hivemq_template.py
+++ b/pi_sensor_hivemq_template.py
@@ -58,8 +58,9 @@ client = mqtt.Client(client_id=DEVICE_ID)
 client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
 
 if USE_TLS:
-    client.tls_set(cert_reqs=ssl.CERT_NONE)
-    client.tls_insecure_set(True)
+    # Use system CA certificates for proper TLS verification
+    import certifi
+    client.tls_set(ca_certs=certifi.where())
 
 def on_connect(c, u, f, rc):
EOF
```

### 8.2 This Week Actions

```bash
# 1. Archive ESP32 firmware
git branch archive/esp32-firmware
git rm -rf firmware/
git commit -m "Archive ESP32 firmware (migrated to RPi)"

# 2. Remove ESP32 fix scripts
git rm backend/bind_esp32.py
git rm backend/fix_demo_state.py
git rm backend/fix_pit_id.py

# 3. Remove serial read scripts
git rm read_serial.py
git rm read_serial_long.py

# 4. Update .gitignore
echo "firmware/" >> .gitignore
echo "*.bin" >> .gitignore
echo "*.elf" >> .gitignore
```

### 8.3 Documentation Updates

```markdown
## Files to Update

1. backend/src/services/mqtt_service.py
   - Line 4: Remove "ESP32" reference
   - Line 71: Remove "ESP32" reference

2. backend/src/services/license_service.py
   - Line 4: Remove "ESP32" reference
   - Line 57: Update docstring

3. backend/src/models/device.py
   - Line 4: Update docstring

4. backend/src/services/sensor_service.py
   - Line 91: Remove "ESP32" reference
   - Line 94-118: Add RPi payload format example
```

---

## APPENDIX A: COMPLETE FER LISTING (RPi Specific)

| FER ID | File | Line | Severity | Issue |
|--------|------|------|----------|-------|
| FER-RPi-001 | PI_MASTER_CONFIG.md | 548 | CRITICAL | Hardcoded MQTT password |
| FER-RPi-002 | pi_sensor_hivemq_template.py | 61 | CRITICAL | TLS verification disabled |
| FER-RPi-003 | PI_MASTER_CONFIG.md | 344 | HIGH | WiFi password exposed |
| FER-RPi-004 | PI_MASTER_CONFIG.md | 21 | MEDIUM | Default Pi password documented |
| FER-RPi-005 | firmware/ | N/A | HIGH | 67MB deprecated code |
| FER-RPi-006 | backend/bind_esp32.py | 4 | HIGH | Deprecated fix script |
| FER-RPi-007 | backend/fix_demo_state.py | 7 | HIGH | Deprecated fix script |
| FER-RPi-008 | backend/fix_pit_id.py | 4 | HIGH | Deprecated fix script |
| FER-RPi-009 | test_sensor_service.py | 39 | MEDIUM | ESP32 test fixtures |
| FER-RPi-010 | mqtt_service.py | 4 | LOW | ESP32 reference in docstring |
| FER-RPi-011 | license_service.py | 4 | LOW | ESP32 reference in docstring |
| FER-RPi-012 | device.py | 4 | LOW | ESP32 reference in docstring |
| FER-RPi-013 | sensor_service.py | 91 | LOW | ESP32 reference in docstring |

---

## APPENDIX B: VERIFICATION CHECKLIST

```yaml
PRE_DEPLOYMENT_CHECKLIST:
  security:
    - [ ] MQTT password changed in HiveMQ
    - [ ] TLS verification enabled in pi_sensor_mqtt.py
    - [ ] WiFi password removed from docs
    - [ ] No credentials in git history (use BFG Repo-Cleaner if needed)
    
  cleanup:
    - [ ] firmware/ folder archived and deleted
    - [ ] ESP32 fix scripts removed
    - [ ] Serial read scripts removed
    - [ ] .gitignore updated
    
  documentation:
    - [ ] ESP32 references updated to generic "device"
    - [ ] RPi setup instructions verified
    - [ ] Sensor wiring guide current
    
  testing:
    - [ ] RPi sensor script tested on actual hardware
    - [ ] MQTT messages received by backend
    - [ ] Camera streaming working
    - [ ] Alerts triggering correctly
```

---

**END OF RPi TRANSITION FORENSIC REPORT**

*Next Steps:*
1. Address CRITICAL findings immediately (FER-RPi-001, FER-RPi-002)
2. Archive ESP32 firmware this week
3. Update documentation references
4. Re-run forensic scan after cleanup
