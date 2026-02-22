import psycopg2
from datetime import datetime

conn = psycopg2.connect('dbname=ppf_monitoring user=ppf_user password=ppf_dev_password_2026 host=localhost port=5432')
cur = conn.cursor()

# Ensure sensor types exist (dummy)
cur.execute("INSERT INTO sensor_types (code, name) VALUES ('BME680', 'BME680') ON CONFLICT DO NOTHING")
cur.execute("INSERT INTO sensor_types (code, name) VALUES ('PMS5003', 'PMS5003') ON CONFLICT DO NOTHING")
conn.commit()

# Make sure device exists
cur.execute("SELECT device_id FROM devices WHERE device_id = 'P01-SENSOR-MOCK'")
if not cur.fetchone():
    cur.execute("""
    INSERT INTO devices (
        device_id, license_key, workshop_id, pit_id, 
        is_online, last_seen, created_at, updated_at
    )
    VALUES (
        'P01-SENSOR-MOCK', 'mock-license-123', 1, 1,
        true, NOW(), NOW(), NOW()
    )
    """)
    conn.commit()

# Insert dummy sensor data (with an updated timestamp so it's "live")
try:
    cur.execute("""
    INSERT INTO sensor_data (
        device_id, pit_id, workshop_id, 
        primary_sensor_type, air_quality_sensor_type,
        temperature, humidity, pm25, pm10, iaq, iaq_accuracy,
        is_valid, created_at, device_timestamp
    ) 
    VALUES (
        'P01-SENSOR-MOCK', 1, 1, 
        'BME680', 'PMS5003',
        22.5, 45.2, 12.4, 25.1, 48.0, 3,
        true, NOW(), NOW()
    )
    """)
    conn.commit()
    print("Dummy sensor data added successfully")
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()

cur.close()
conn.close()
