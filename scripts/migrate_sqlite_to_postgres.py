import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
import sys
from dotenv import load_dotenv
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # add repo root
load_dotenv()  # so DATABASE_URL in .env is picked up

from database.connection import DB_PATH
pg_url = os.getenv("DATABASE_URL")
if not pg_url:
    raise SystemExit("Set DATABASE_URL to your Postgres before running migration")

eng_pg = create_engine(pg_url, future=True)

# read from sqlite
import sqlite3
conn_sqlite = sqlite3.connect(str(DB_PATH))
tables = ["users", "movies", "ratings", "tags", "links"]

for t in tables:
    df = pd.read_sql_query(f"SELECT * FROM {t}", conn_sqlite)
    if not df.empty:
        df.to_sql(t, eng_pg, if_exists="append", index=False)
        print(f"migrated {len(df)} rows into {t}")
    else:
        print(f"{t} empty; skipped")

conn_sqlite.close()
print("✅ migration complete")