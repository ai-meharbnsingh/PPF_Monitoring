import psycopg2
conn = psycopg2.connect('dbname=ppf_monitoring user=ppf_user password=ppf_dev_password_2026 host=localhost port=5432')
cur = conn.cursor()
cur.execute("UPDATE devices SET pit_id = 1 WHERE device_id = 'ESP32-PLACEHOLDER'")
cur.execute("UPDATE pits SET camera_is_online = true WHERE workshop_id=1 AND pit_number=1")
conn.commit()
print('Done')
