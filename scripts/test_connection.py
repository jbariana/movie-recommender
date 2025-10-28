# Save as test_connection.py and run it
import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print("DATABASE_URL:", DATABASE_URL)

if DATABASE_URL:
    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        print("✅ PostgreSQL connected:", cur.fetchone()[0])
        conn.close()
    except Exception as e:
        print("❌ PostgreSQL connection failed:", e)
else:
    print("❌ No DATABASE_URL found")