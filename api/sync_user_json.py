from pathlib import Path
import json
import time
import logging
from typing import Optional

from database.connection import get_db
from database.paramstyle import PH

logger = logging.getLogger(__name__)


def _ensure_user(conn, username: str, prefer_id: Optional[int] = None) -> Optional[int]:
    cur = conn.cursor()

    if prefer_id is not None:
        cur.execute(f"SELECT user_id FROM users WHERE user_id = {PH}", (prefer_id,))
        row = cur.fetchone()
        if row:
            return int(row[0])

    cur.execute(f"SELECT user_id FROM users WHERE username = {PH}", (username,))
    row = cur.fetchone()
    if row:
        return int(row[0])

    # Insert and return new id
    # Postgres supports RETURNING; SQLite (>=3.35) also does; fallback included.
    try:
        cur.execute(f"INSERT INTO users (username) VALUES ({PH}) RETURNING user_id", (username,))
        return int(cur.fetchone()[0])
    except Exception:
        cur.execute(f"INSERT INTO users (username) VALUES ({PH})", (username,))
        try:
            return int(cur.lastrowid)
        except Exception:
            cur.execute(f"SELECT user_id FROM users WHERE username = {PH}", (username,))
            return int(cur.fetchone()[0])


def _find_movie_id_by_title(conn, title: str) -> Optional[int]:
    if not title:
        return None
    cur = conn.cursor()

    # exact (case-insensitive)
    try:
        cur.execute(f"SELECT movie_id FROM movies WHERE LOWER(title) = LOWER({PH}) LIMIT 1", (title,))
        row = cur.fetchone()
        if row:
            return int(row[0])
    except Exception:
        pass

    # fallback LIKE
    try:
        cur.execute(f"SELECT movie_id FROM movies WHERE title LIKE {PH} LIMIT 1", (f"%{title}%",))
        row = cur.fetchone()
        if row:
            return int(row[0])
    except Exception:
        pass
    return None


def sync_user_ratings(profile_path: Path) -> bool:
    """
    Sync the given profile JSON to the DB.
    - Resolve/create numeric user_id
    - Ensure the user exists
    - Replace that user's ratings in DB with entries from JSON
    """
    try:
        profile_path = Path(profile_path)
        data = json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("Failed to read profile JSON")
        return False

    username = data.get("username") or str(data.get("user_id") or "")
    prefer_id_raw = data.get("user_id")

    # coerce prefer_id to int if possible
    prefer_id = None
    try:
        if isinstance(prefer_id_raw, int):
            prefer_id = prefer_id_raw
        elif isinstance(prefer_id_raw, str) and prefer_id_raw.isdigit():
            prefer_id = int(prefer_id_raw)
    except Exception:
        prefer_id = None

    try:
        # >>> IMPORTANT: use context manager <<<
        with get_db(readonly=False) as conn:
            cur = conn.cursor()

            uid = _ensure_user(conn, username, prefer_id)
            if uid is None:
                logger.error("Could not determine or create user id for sync")
                return False

            # ensure JSON stores numeric user_id going forward
            try:
                if data.get("user_id") != uid:
                    data["user_id"] = uid
                    profile_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            except Exception:
                logger.exception("Failed to update profile JSON user_id")

            # replace ratings
            cur.execute(f"DELETE FROM ratings WHERE user_id = {PH}", (uid,))

            inserted = 0
            for entry in data.get("ratings", []):
                # accept movie_id, movie, or title
                movie_id = None
                movie_id_raw = entry.get("movie_id") if entry.get("movie_id") is not None else entry.get("movie")
                if movie_id_raw is not None:
                    try:
                        movie_id = int(movie_id_raw)
                    except Exception:
                        movie_id = None

                if movie_id is None and entry.get("title"):
                    movie_id = _find_movie_id_by_title(conn, entry.get("title"))
                if movie_id is None and entry.get("title") is None:
                    m = entry.get("movie")
                    if isinstance(m, str):
                        movie_id = _find_movie_id_by_title(conn, m)

                if movie_id is None:
                    logger.debug(f"Skipping rating without resolvable movie_id: {entry}")
                    continue

                rating = entry.get("rating")
                if rating is None:
                    logger.debug(f"Skipping rating without value: {entry}")
                    continue
                try:
                    rating_val = float(rating)
                except Exception:
                    logger.debug(f"Skipping non-numeric rating: {entry}")
                    continue

                timestamp = int(entry.get("timestamp") or time.time())
                cur.execute(
                    f"INSERT INTO ratings (user_id, movie_id, rating, timestamp) VALUES ({PH},{PH},{PH},{PH})",
                    (uid, movie_id, rating_val, timestamp),
                )
                inserted += 1

        logger.info(f"sync_user_ratings: user {username} (id={uid}) - inserted {inserted} ratings")
        return True

    except Exception:
        logger.exception("Failed to sync profile to DB")
        return False