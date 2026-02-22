import psycopg2

conn = psycopg2.connect('dbname=ppf_monitoring user=ppf_user password=ppf_dev_password_2026 host=localhost port=5432')
cur = conn.cursor()

cur.execute("SELECT device_id, license_key, workshop_id, pit_id, is_online FROM devices WHERE device_id = 'ESP32-PLACEHOLDER'")
row = cur.fetchone()
print("device_id:", row[0])
print("license_key:", row[1])
print("workshop_id:", row[2])
print("pit_id:", row[3])
print()
print("=== ESP32 Firmware Config ===")
print(f"MQTT Broker:   localhost:1883")
print(f"MQTT Username: ppf_backend  (or leave blank if no auth on ESP side)")
print(f"MQTT Password: BsW0mmVr5CoDAzW21ibADB7t-kM")
print(f"MQTT Topic:    workshop/{row[2]}/pit/{row[3]}/sensors")
print()
print("=== JSON Payload the ESP32 must publish ===")
print("""{
  "device_id": "%s",
  "license_key": "%s",
  "temperature": 25.3,
  "humidity": 58.0
}""" % (row[0], row[1]))

cur.close()
conn.close()
