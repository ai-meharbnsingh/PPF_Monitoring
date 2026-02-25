import psycopg2
from datetime import datetime

try:
    conn = psycopg2.connect("postgresql://ppf_user:ppf_password_change_me@localhost:5432/ppf_monitoring")
    cur = conn.cursor()

    cur.execute("UPDATE jobs SET customer_view_expires_at = NOW() + INTERVAL '30 days' WHERE customer_view_token = 'GT3RSX';")
    conn.commit()
    
    cur.execute("SELECT id, status, customer_view_token, customer_view_expires_at FROM jobs WHERE customer_view_token = 'GT3RSX';")
    print(cur.fetchall())
    
    cur.close()
    conn.close()
    print("Database expiration set successfully via psycopg2.")
except Exception as e:
    print(f"Error: {e}")
