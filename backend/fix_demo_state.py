import psycopg2

conn = psycopg2.connect('dbname=ppf_monitoring user=ppf_user password=ppf_dev_password_2026 host=localhost port=5432')
cur = conn.cursor()

# Fix device - move it to workshop 1, pit 10
cur.execute("UPDATE devices SET workshop_id = 1, pit_id = 10, is_online = true WHERE device_id = 'ESP32-PLACEHOLDER'")

# Make sure sensor readings from this device point to pit 10 and workshop 1
cur.execute("UPDATE sensor_data SET pit_id = 10, workshop_id = 1 WHERE device_id = 'ESP32-PLACEHOLDER'")

# Make super_admin user belong to workshop 1
cur.execute("UPDATE users SET workshop_id = 1 WHERE username = 'super_admin'")

# Make sure camera is marked online so webcam shows
cur.execute("UPDATE pits SET camera_is_online = true WHERE id = 10")

conn.commit()

# Summary
cur.execute("SELECT id, device_id, pit_id, workshop_id, is_online FROM devices")
print("Devices:", cur.fetchall())

cur.execute("SELECT temperature, humidity, created_at FROM sensor_data WHERE pit_id = 10 ORDER BY created_at DESC LIMIT 3")
print("Sensor readings for pit 10:", cur.fetchall())

cur.execute("SELECT id, workshop_id FROM users WHERE username = 'super_admin'")
print("super_admin user:", cur.fetchone())

print("\nDEMO URL: http://localhost:5173/pits/10")

cur.close()
conn.close()
