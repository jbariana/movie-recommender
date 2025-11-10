# database/users.py
from typing import Optional, Tuple
from database.connection import get_db
from database.paramstyle import PH

def get_user_by_username(username: str) -> Optional[Tuple[int, str, str]]:
    """
    Returns (user_id, username, password_hash) or None
    """
    with get_db(readonly=True) as conn:
        cur = conn.cursor()
        cur.execute(
            f"SELECT user_id, username, password_hash FROM users WHERE username = {PH};",
            (username,),
        )
        row = cur.fetchone()
        return tuple(row) if row else None

def create_user(username: str, password_hash: str) -> int:
    """
    Inserts user and returns user_id. If username exists, raises.
    """
    with get_db(readonly=False) as conn:
        cur = conn.cursor()
        cur.execute(
            f"INSERT INTO users (username, password_hash) VALUES ({PH}, {PH}) RETURNING user_id;"
            if conn.__class__.__module__.startswith("psycopg2")
            else f"INSERT INTO users (username, password_hash) VALUES ({PH}, {PH});",
            (username, password_hash),
        )
        if cur.description:  # Postgres RETURNING
            return int(cur.fetchone()[0])
        # SQLite: fetch id
        cur.execute("SELECT last_insert_rowid();")
        return int(cur.fetchone()[0])

def set_password(username: str, password_hash: str) -> None:
    with get_db(readonly=False) as conn:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE users SET password_hash = {PH} WHERE username = {PH};",
            (password_hash, username),
        )
