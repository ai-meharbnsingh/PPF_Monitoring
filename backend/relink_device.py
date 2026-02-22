import psycopg2

conn = psycopg2.connect('dbname=ppf_monitoring user=ppf_user password=ppf_dev_password_2026 host=localhost port=5432')
cur = conn.cursor()

# Re-insert ESP32 device linked to workshop 1, pit 10
cur.execute("""
INSERT INTO devices (
    device_id, license_key, workshop_id, pit_id,
    is_online, last_seen, status, created_at, updated_at
)
VALUES (
    'ESP32-PLACEHOLDER', 'mock-license-001', 1, 10,
    true, NOW(), 'active', NOW(), NOW()
)
ON CONFLICT (device_id) DO UPDATE SET
    pit_id = 10,
    workshop_id = 1,
    is_online = true,
    last_seen = NOW(),
    updated_at = NOW()
""")
conn.commit()
print("Device linked to pit 10")

# Verify
cur.execute("SELECT device_id, pit_id, workshop_id, is_online FROM devices")
print("Devices:", cur.fetchall())

cur.close()
conn.close()
