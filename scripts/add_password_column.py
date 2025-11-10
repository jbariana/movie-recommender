"""
add password_hash column to existing users table
"""

import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if DATABASE_URL:
    # postgres
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # add password_hash column if it doesn't exist
    cur.execute("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS password_hash TEXT;
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Added password_hash column to users table (Postgres)")
else:
    # sqlite
    import sqlite3
    from pathlib import Path
    
    DB_PATH = Path(os.getenv("DB_PATH", "database/movies.db"))
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # check if column exists
    cur.execute("PRAGMA table_info(users);")
    columns = [row[1] for row in cur.fetchall()]
    
    if "password_hash" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN password_hash TEXT;")
        conn.commit()
        print("Added password_hash column to users table (SQLite)")
    else:
        print("password_hash column already exists")
    
    cur.close()
    conn.close()