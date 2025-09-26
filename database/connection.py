"""
connection.py
Centralizes the SQLite database location and connection helper.

Functions:
- get_db(readonly: bool = False) -> sqlite3.Connection
"""

from __future__ import annotations
import os
import sqlite3
from pathlib import Path

# Database lives inside the repository under /database
DB_DIR = Path(__file__).resolve().parent
DB_PATH = DB_DIR / "movies.db"

def get_db(readonly: bool = False) -> sqlite3.Connection:
    """
    Returns a sqlite3 connection.
    Set readonly=True for SELECT-only operations (safer for API endpoints).
    """
    if readonly:
        # URI mode for read-only connection
        uri = f"file:{DB_PATH.as_posix()}?mode=ro"
        return sqlite3.connect(uri, uri=True, check_same_thread=False)
    # Ensure directory exists
    os.makedirs(DB_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH.as_posix(), check_same_thread=False)
