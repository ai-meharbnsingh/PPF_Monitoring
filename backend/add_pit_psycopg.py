import psycopg2

conn = psycopg2.connect('dbname=ppf_monitoring user=ppf_user password=ppf_dev_password_2026 host=localhost port=5432')
cur = conn.cursor()

# Make sure workshop exists
cur.execute("SELECT id FROM workshops WHERE id = 1")
if not cur.fetchone():
    cur.execute("""
    INSERT INTO workshops (name, slug, subscription_plan, subscription_status, is_active, max_users, max_pits)
    VALUES ('Pit 1 Demo', 'pit-1-demo', 'basic', 'active', true, 5, 1) ON CONFLICT DO NOTHING
    """)
    conn.commit()

# Insert pit
try:
    cur.execute("""
    INSERT INTO pits (workshop_id, pit_number, name, description, status, camera_is_online) 
    VALUES (1, 1, 'Demo Pit 1', 'Main floor', 'active', false) ON CONFLICT DO NOTHING
    """)
    conn.commit()
    print("Success")
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()

cur.close()
conn.close()
