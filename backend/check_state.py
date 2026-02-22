import psycopg2

conn = psycopg2.connect('dbname=ppf_monitoring user=ppf_user password=ppf_dev_password_2026 host=localhost port=5432')
cur = conn.cursor()

# Get the real state of Workshop 1
cur.execute("SELECT id, name FROM workshops WHERE id = 1")
ws = cur.fetchone()
print("Workshop:", ws)

cur.execute("SELECT id, pit_number, name, camera_is_online, workshop_id FROM pits WHERE workshop_id = 1")
pits = cur.fetchall()
print("Pits:", pits)

cur.execute("SELECT device_id, pit_id, workshop_id, is_online FROM devices WHERE workshop_id = 1")
devs = cur.fetchall()
print("Devices:", devs)

cur.execute("SELECT temperature, humidity, created_at FROM sensor_data WHERE pit_id = 10 ORDER BY created_at DESC LIMIT 3")
readings = cur.fetchall()
print("Sensor readings:", readings)

cur.close()
conn.close()
