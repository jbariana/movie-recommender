"""
connection.py
centralizes database connection helper for sqlite or postgres
switches between databases using DATABASE_URL environment variable
"""

from __future__ import annotations
import os
from pathlib import Path
from contextlib import contextmanager
from dotenv import load_dotenv

#load environment variables from .env file
load_dotenv()

#check for postgres connection string in environment
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
# psycopg2 does NOT accept the SQLAlchemy-style scheme with "+psycopg2"
# e.g., "postgresql+psycopg2://user:pass@host:5432/db"
if DATABASE_URL.startswith("postgresql+psycopg2://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL.split("postgresql+psycopg2://", 1)[1]

#default sqlite database path if no postgres URL provided
DB_PATH = Path(os.getenv("DB_PATH", Path(__file__).resolve().parent / "movies.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_db(readonly: bool = False):
    """
    context manager for database connections
    automatically handles commits, rollbacks, and cleanup
    
    usage:
        with get_db(readonly=True) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM movies")
    """
    #use postgres if DATABASE_URL is set in .env
    if DATABASE_URL:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        try:
            yield conn
            #commit changes if not readonly
            if not readonly:
                conn.commit()
        except Exception:
            #rollback on errors
            conn.rollback()
            raise
        finally:
            #always close connection
            conn.close()
    
    #fallback to sqlite
    else:
        import sqlite3
        #use read-only mode if specified
        uri = f"file:{DB_PATH}?mode=ro" if readonly else str(DB_PATH)
        conn = sqlite3.connect(uri, uri=readonly, check_same_thread=False)
        #enable dict-like row access
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            #commit changes if not readonly
            if not readonly:
                conn.commit()
        except Exception:
            #rollback on errors
            conn.rollback()
            raise
        finally:
            #always close connection
            conn.close()