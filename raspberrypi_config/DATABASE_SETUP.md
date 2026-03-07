# Database Setup Guide

> **Critical setup instructions for the PPF Monitoring database**
> 
> **Last Updated:** 2026-03-07

---

## ⚠️ CRITICAL: Device Subscription Requirement

**For a device to work and send sensor data, BOTH records MUST exist:**

1. ✅ `devices` table record
2. ✅ `subscriptions` table record

**Without a subscription record, the backend will REJECT all sensor data from the device!**

---

## Database Schema Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATABASE TABLES                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│  │    workshops    │◄────┗━━━━   pits    ━━━┛◄────┗━━━━  devices  ━━┛       │
│  │                 │     │                 │     │                 │       │
│  │ - id            │     │ - id            │     │ - device_id     │       │
│  │ - name          │     │ - workshop_id   │     │ - license_key   │       │
│  │ - location      │     │ - pit_number    │     │ - workshop_id   │◄─────┐│
│  └─────────────────┘     │ - name          │     │ - pit_id        │      ││
│                          └─────────────────┘     │ - status        │      ││
│                                                  │ - is_online     │      ││
│  ┌─────────────────┐     ┌─────────────────┐     │ - last_seen     │      ││
│  │  sensor_data    │────►│  subscriptions  │◄────┗━━━━━━━━━━━━━━━━━┛      ││
│  │                 │     │                 │                               ││
│  │ - id            │     │ - id            │                               ││
│  │ - device_id     │     │ - workshop_id   │                               ││
│  │ - pit_id        │     │ - device_id     │                               ││
│  │ - temperature   │     │ - license_key   │                               ││
│  │ - humidity      │     │ - plan          │                               ││
│  │ - pm25          │     │ - status        │                               ││
│  │ - created_at    │     │ - expires_at    │                               ││
│  └─────────────────┘     └─────────────────┘                               ││
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Device Registration

### Step 1: Ensure Workshop and Pit Exist

```sql
-- Check if workshop exists
SELECT * FROM workshops WHERE id = 2;

-- If not, create it:
INSERT INTO workshops (name, location, status)
VALUES ('RG Studio', 'Delhi', 'active')
RETURNING id;

-- Check if pit exists
SELECT * FROM pits WHERE id = 3;

-- If not, create it:
INSERT INTO pits (workshop_id, pit_number, name, status)
VALUES (2, 3, 'Pit 3', 'active')
RETURNING id;
```

### Step 2: Create Device Record

```sql
INSERT INTO devices (
    device_id,
    license_key,
    status,
    workshop_id,
    pit_id,
    is_online,
    mac_address,
    firmware_version,
    created_at,
    updated_at
) VALUES (
    'PIWIFI-01',              -- Must match DEVICE_ID in pi_sensor_mqtt.py
    'LIC-RG-STUDIO-2026',     -- Must match LICENSE_KEY in pi_sensor_mqtt.py
    'active',                 -- 'active', 'pending', 'disabled', 'suspended'
    2,                        -- Workshop ID
    3,                        -- Pit ID
    false,                    -- Will be set true when device connects
    '88:a2:9e:69:f1:3f',      -- Pi MAC address (get with: ip link show wlan0)
    '1.0.0',                  -- Firmware version
    NOW(),
    NOW()
)
ON CONFLICT (device_id) DO UPDATE SET
    license_key = EXCLUDED.license_key,
    workshop_id = EXCLUDED.workshop_id,
    pit_id = EXCLUDED.pit_id,
    status = EXCLUDED.status,
    updated_at = NOW()
RETURNING *;
```

### Step 3: Create Subscription Record (REQUIRED!)

```sql
INSERT INTO subscriptions (
    workshop_id,
    device_id,
    license_key,
    plan,
    status,
    monthly_fee,
    currency,
    grace_period_days,
    trial_expires_at,
    created_at,
    updated_at
) VALUES (
    2,                        -- Same workshop_id as device
    'PIWIFI-01',              -- Same device_id
    'LIC-RG-STUDIO-2026',     -- Same license_key
    'trial',                  -- 'trial', 'basic', 'standard', 'premium'
    'active',                 -- 'active', 'suspended', 'expired', 'cancelled'
    0,                        -- Monthly fee in INR (0 for trial)
    'INR',                    -- Currency
    7,                        -- Grace period days after expiry
    NOW() + INTERVAL '7 days', -- Trial expiry date (NULL for paid plans)
    NOW(),
    NOW()
)
ON CONFLICT (device_id) DO UPDATE SET
    license_key = EXCLUDED.license_key,
    plan = EXCLUDED.plan,
    status = EXCLUDED.status,
    updated_at = NOW()
RETURNING *;
```

### Step 4: Verify Setup

```sql
-- Complete device verification query
SELECT 
    d.device_id,
    d.license_key,
    d.status as device_status,
    d.is_online,
    d.last_seen,
    d.workshop_id,
    d.pit_id,
    s.plan,
    s.status as subscription_status,
    s.expires_at,
    w.name as workshop_name,
    p.pit_number
FROM devices d
LEFT JOIN subscriptions s ON d.device_id = s.device_id
LEFT JOIN workshops w ON d.workshop_id = w.id
LEFT JOIN pits p ON d.pit_id = p.id
WHERE d.device_id = 'PIWIFI-01';

-- Expected output:
-- device_id  | license_key        | device_status | is_online | last_seen | workshop_id | pit_id | plan  | subscription_status | expires_at | workshop_name | pit_number
-- PIWIFI-01  | LIC-RG-STUDIO-2026 | active        | t         | 2026-...  | 2           | 3      | trial | active              | 2026-...   | RG Studio     | 3
```

---

## Quick Registration Script

Save this as `register_device.sql` and run with `psql $DATABASE_URL -f register_device.sql`:

```sql
-- Register Device Script
-- Edit these variables before running:
\set device_id 'PIWIFI-01'
\set license_key 'LIC-RG-STUDIO-2026'
\set workshop_id 2
\set pit_id 3
\set mac_address '88:a2:9e:69:f1:3f'

-- 1. Create device
INSERT INTO devices (
    device_id, license_key, status, workshop_id, pit_id,
    is_online, mac_address, firmware_version, created_at, updated_at
) VALUES (
    :'device_id', :'license_key', 'active', :'workshop_id', :'pit_id',
    false, :'mac_address', '1.0.0', NOW(), NOW()
)
ON CONFLICT (device_id) DO UPDATE SET
    license_key = EXCLUDED.license_key,
    workshop_id = EXCLUDED.workshop_id,
    pit_id = EXCLUDED.pit_id,
    status = EXCLUDED.status,
    updated_at = NOW();

-- 2. Create subscription (REQUIRED!)
INSERT INTO subscriptions (
    workshop_id, device_id, license_key, plan, status,
    monthly_fee, currency, grace_period_days, created_at, updated_at
) VALUES (
    :'workshop_id', :'device_id', :'license_key', 'trial', 'active',
    0, 'INR', 7, NOW(), NOW()
)
ON CONFLICT (device_id) DO UPDATE SET
    license_key = EXCLUDED.license_key,
    plan = EXCLUDED.plan,
    status = EXCLUDED.status,
    updated_at = NOW();

-- 3. Show result
SELECT 
    d.device_id,
    d.status as device_status,
    d.is_online,
    s.plan,
    s.status as subscription_status,
    CASE 
        WHEN s.status = 'active' THEN '✅ Device will accept sensor data'
        ELSE '❌ Subscription not active - data will be rejected'
    END as status_check
FROM devices d
LEFT JOIN subscriptions s ON d.device_id = s.device_id
WHERE d.device_id = :'device_id';
```

---

## Subscription Plans Reference

| Plan | Monthly Fee | Features | Typical Use |
|------|-------------|----------|-------------|
| `trial` | ₹0 | Full access for 7 days | New device testing |
| `basic` | ₹1,000 | 1 pit, basic sensors | Small workshop |
| `standard` | ₹1,500 | 3 pits, all sensors | Medium workshop |
| `premium` | ₹2,500 | Unlimited pits, priority support | Large facility |

---

## Troubleshooting

### "Device shows offline but Pi is sending data"

**Check:**
```sql
SELECT * FROM subscriptions WHERE device_id = 'PIWIFI-01';
```

If no rows returned → **Subscription is missing!** Run Step 3 above.

### "Backend logs show 'Invalid license'"

**Check license matches:**
```sql
SELECT device_id, license_key FROM devices WHERE device_id = 'PIWIFI-01';
-- Compare with license_key in pi_sensor_mqtt.py on the Pi
```

### "Subscription status is 'expired'"

**Extend trial:**
```sql
UPDATE subscriptions 
SET 
    status = 'active',
    trial_expires_at = NOW() + INTERVAL '7 days',
    updated_at = NOW()
WHERE device_id = 'PIWIFI-01';
```

### "Device status is 'pending'"

**Activate device:**
```sql
UPDATE devices 
SET status = 'active', updated_at = NOW()
WHERE device_id = 'PIWIFI-01';
```

---

## Data Flow Verification

### 1. Check Pi is Publishing

```bash
# On the Raspberry Pi
sudo journalctl -u pi-sensors -f
# Should show: "Published: T=27.5°C, H=60%, PM2.5=100"
```

### 2. Check MQTT is Receiving

```python
# Test script - run locally
import paho.mqtt.client as mqtt
import ssl

client = mqtt.Client()
client.username_pw_set("ppf_backend", "PPF@Mqtt2026!secure")
client.tls_set()

def on_msg(c, u, msg):
    print(f"Received: {msg.topic} = {msg.payload.decode()[:100]}")

client.on_message = on_msg
client.connect("c4cb4d2b4a3e432c9d61b8b56ee359af.s1.eu.hivemq.cloud", 8883, 60)
client.subscribe("workshop/+/pit/+/sensors")
client.loop_forever()
```

### 3. Check Database Received Data

```sql
-- Latest sensor reading
SELECT 
    device_id,
    temperature,
    humidity,
    pm25,
    created_at,
    NOW() - created_at as time_ago
FROM sensor_data 
WHERE device_id = 'PIWIFI-01'
ORDER BY created_at DESC
LIMIT 1;

-- Should show recent data (within last minute if Pi is running)
```

---

## Complete Setup Checklist

For each new Raspberry Pi device:

- [ ] 1. Hardware wired correctly (BME688 + PMS5003)
- [ ] 2. Pi flashed and connected to WiFi
- [ ] 3. `pi_sensor_mqtt.py` configured with correct `DEVICE_ID` and `LICENSE_KEY`
- [ ] 4. Sensor service running: `sudo systemctl status pi-sensors`
- [ ] 5. Workshop exists in database
- [ ] 6. Pit exists in database
- [ ] 7. **Device record created in `devices` table**
- [ ] 8. **Subscription record created in `subscriptions` table** ⚠️ CRITICAL
- [ ] 9. Verify data flowing: check `sensor_data` table
- [ ] 10. Verify dashboard shows device online
