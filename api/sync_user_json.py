from pathlib import Path
import json
import time
import logging
from typing import Optional

from database.connection import get_db

logger = logging.getLogger(__name__)


def _ensure_user(conn, username: str, prefer_id: Optional[int] = None) -> Optional[int]:
    cur = conn.cursor()
    if prefer_id is not None:
        try:
            cur.execute("SELECT user_id FROM users WHERE user_id = ?", (prefer_id,))
            row = cur.fetchone()
            if row:
                try:
                    return int(row["user_id"])
                except Exception:
                    return int(row[0])
        except Exception:
            pass

    cur.execute("SELECT user_id FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if row:
        try:
            return int(row["user_id"])
        except Exception:
            return int(row[0])

    cur.execute("INSERT INTO users (username) VALUES (?)", (username,))
    conn.commit()
    return int(cur.lastrowid)


def _find_movie_id_by_title(conn, title: str) -> Optional[int]:
    if not title:
        return None
    cur = conn.cursor()
    # try exact match first (case-insensitive)
    try:
        cur.execute("SELECT movie_id FROM movies WHERE LOWER(title) = LOWER(?) LIMIT 1", (title,))
        row = cur.fetchone()
        if row:
            try:
                return int(row["movie_id"])
            except Exception:
                return int(row[0])
    except Exception:
        pass
    # fallback: try LIKE search
    try:
        cur.execute("SELECT movie_id FROM movies WHERE title LIKE ? LIMIT 1", (f"%{title}%",))
        row = cur.fetchone()
        if row:
            try:
                return int(row["movie_id"])
            except Exception:
                return int(row[0])
    except Exception:
        pass
    return None


def sync_user_ratings(profile_path: Path) -> bool:
    """
    Sync the given profile JSON to the DB.
    - Coerce/resolve numeric user_id where possible
    - Ensure the user exists and update profile JSON with numeric user_id
    - Replace that user's ratings in DB with entries from JSON
    """
    try:
        profile_path = Path(profile_path)
        data = json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception as ex:
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
        conn = get_db(readonly=False)
        cur = conn.cursor()

        uid = _ensure_user(conn, username, prefer_id)

        if uid is None:
            logger.error("Could not determine or create user id for sync")
            conn.close()
            return False

        # update profile JSON to ensure it stores numeric user_id going forward
        try:
            if data.get("user_id") != uid:
                data["user_id"] = uid
                profile_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            logger.exception("Failed to update profile JSON user_id")

        # delete existing ratings for user
        cur.execute("DELETE FROM ratings WHERE user_id = ?", (uid,))

        inserted = 0
        for entry in data.get("ratings", []):
            # accept movie_id, movie, or title
            movie_id_raw = entry.get("movie_id") if entry.get("movie_id") is not None else entry.get("movie")
            movie_id = None
            if movie_id_raw is not None:
                try:
                    movie_id = int(movie_id_raw)
                except Exception:
                    # not an int; maybe it's a title string
                    movie_id = None

            if movie_id is None and entry.get("title"):
                movie_id = _find_movie_id_by_title(conn, entry.get("title"))

            if movie_id is None and entry.get("title") is None:
                # last attempt: if entry has a 'movie' that's a string treat as title
                m = entry.get("movie")
                if isinstance(m, str):
                    movie_id = _find_movie_id_by_title(conn, m)

            if movie_id is None:
                logger.debug(f"Skipping rating entry without resolvable movie_id: {entry}")
                continue

            rating = entry.get("rating")
            if rating is None:
                logger.debug(f"Skipping rating entry without rating value: {entry}")
                continue
            try:
                rating_val = float(rating)
            except Exception:
                logger.debug(f"Skipping rating with non-numeric value: {entry}")
                continue

            timestamp = int(entry.get("timestamp") or time.time())
            cur.execute(
                "INSERT INTO ratings (user_id, movie_id, rating, timestamp) VALUES (?, ?, ?, ?)",
                (uid, movie_id, rating_val, timestamp),
            )
            inserted += 1

        conn.commit()
        conn.close()
        logger.info(f"sync_user_ratings: user {username} (id={uid}) - inserted {inserted} ratings")
        return True
    except Exception:
        logger.exception("Failed to sync profile to DB")
        return False
