"""
connection.py
Centralizes the SQLite database connection helper.

Functions:
- get_db(readonly: bool = False) -> sqlite3.Connection
"""

from __future__ import annotations
import os
import sqlite3
from pathlib import Path

# --- SQLite connection configuration ---
# Path to the SQLite DB file (used across the app)
DB_PATH = Path(os.getenv("DB_PATH", Path(__file__).resolve().parent / "movies.db"))

# ensure directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_db(readonly: bool = False) -> sqlite3.Connection:
    """
    Returns a SQLite connection object. If readonly is True, opens the DB in read-only mode.
    Connection.row_factory = sqlite3.Row so callers can access columns by name.

    Example:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM movies LIMIT 5;")
        rows = cur.fetchall()
    """
    if readonly:
        # open readonly via URI mode
        uri = f"file:{DB_PATH}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    else:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)

    conn.row_factory = sqlite3.Row
    return conn
