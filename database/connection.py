"""
connection.py
Centralizes the PostgreSQL database connection helper.

Functions:
- get_db(readonly: bool = False) -> psycopg2.Connection
"""

from __future__ import annotations
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# --- PostgreSQL connection configuration ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "movies")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

def get_db(readonly: bool = False):
    """
    Returns a PostgreSQL connection object.
    Uses environment variables for credentials.

    Example:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM movies LIMIT 5;")
        rows = cur.fetchall()
    """
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=RealDictCursor,
    )

    # Set read-only mode if requested
    if readonly:
        conn.set_session(readonly=True, autocommit=True)
    else:
        conn.autocommit = True

    return conn
