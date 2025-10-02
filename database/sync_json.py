import json
from pathlib import Path
import sqlite3
import time

DB_PATH = Path(__file__).parent / "movies.db"

def _parse_rating_entry(r):
    """
    Accepts either:
      - dict: {"movie_id": .., "rating": .., "timestamp": ..}
      - list/tuple: [movie_id, rating] or [movie_id, rating, timestamp]
    Returns (movie_id:int, rating:float, timestamp:int) or None on parse error.
    """
    if isinstance(r, dict):
        movie_id = r.get("movie_id") or r.get("movieId")
        rating = r.get("rating")
        ts = r.get("timestamp")
    elif isinstance(r, (list, tuple)):
        if len(r) < 2:
            return None
        movie_id = r[0]
        rating = r[1]
        ts = r[2] if len(r) > 2 else None
    else:
        return None

    try:
        movie_id = int(movie_id)
        rating = float(rating)
    except Exception:
        return None

    if ts is None:
        ts = int(time.time())
    else:
        try:
            ts = int(ts)
        except Exception:
            ts = int(time.time())

    return movie_id, rating, ts

def sync_user_ratings(json_path: Path):

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    user_id = data.get("user_id")
    ratings = data.get("ratings", [])

    
    uid = int(user_id)

    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    try:
        cursor = conn.cursor()
        if not ratings:
            cursor.execute("DELETE FROM ratings WHERE user_id = ?", (uid,))
            conn.commit()
            print(f"(Sync)Removed all ratings for user {user_id}.")
            return

        synced = 0
        for r in ratings:
            parsed = _parse_rating_entry(r)
            if not parsed:
                continue
            movie_id, rating, ts = parsed

            cursor.execute("DELETE FROM ratings WHERE user_id = ? AND movie_id = ?", (uid, movie_id))
            cursor.execute(
                "INSERT INTO ratings (user_id, movie_id, rating, timestamp) VALUES (?, ?, ?, ?)",
                (uid, movie_id, rating, ts)
            )
            synced += 1
        conn.commit()
        print(f"(Sync)Synced {synced} ratings for user {user_id}.")
    finally:
        conn.close()
