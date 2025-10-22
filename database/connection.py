"""
connection.py
Centralizes the database connection helper (SQLite or Postgres).
Use DATABASE_URL in .env to switch to Postgres.
"""

from __future__ import annotations
import os
from pathlib import Path
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# SQLite fallback path
DB_PATH = Path(os.getenv("DB_PATH", Path(__file__).resolve().parent / "movies.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

@contextmanager
def get_db(readonly: bool = False):
    """
    Context manager yielding a DB-API connection.
    - Postgres: psycopg2
    - SQLite: sqlite3
    Returns connections that work with pandas.read_sql_query.
    """
    if DATABASE_URL:
        # --- PostgreSQL path ---
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        try:
            yield conn
            if not readonly:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        # --- SQLite path (legacy) ---
        import sqlite3
        if readonly:
            uri = f"file:{DB_PATH}?mode=ro"
            conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
        else:
            conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            if not readonly:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()