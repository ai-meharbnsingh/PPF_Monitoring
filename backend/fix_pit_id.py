import psycopg2
conn = psycopg2.connect('dbname=ppf_monitoring user=ppf_user password=ppf_dev_password_2026 host=localhost port=5432')
cur = conn.cursor()
cur.execute("UPDATE devices SET pit_id = 10 WHERE device_id = 'ESP32-PLACEHOLDER'")
cur.execute("UPDATE sensor_data SET pit_id = 10 WHERE device_id = 'ESP32-PLACEHOLDER'")
conn.commit()
print('Fixed pit id assignment')
