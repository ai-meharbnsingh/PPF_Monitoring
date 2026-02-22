import psycopg2

conn = psycopg2.connect('dbname=ppf_monitoring user=ppf_user password=ppf_dev_password_2026 host=localhost port=5432')
cur = conn.cursor()

# Check what columns devices table has
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'devices' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]
print("Devices columns:", cols)

# Check if ESP32-PLACEHOLDER already exists  
cur.execute("SELECT id, device_id, pit_id, workshop_id FROM devices")
print("Current devices:", cur.fetchall())

cur.close()
conn.close()
