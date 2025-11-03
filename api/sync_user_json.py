"""
sync_user_json.py
synchronizes user profile JSON file with database ratings table

handles:
- user account creation/resolution
- movie title to ID lookups
- full profile sync (replace existing ratings with JSON data)
"""

from pathlib import Path
import json
import time
import logging
from typing import Optional

from database.connection import get_db
from database.paramstyle import PH
from database.id_to_title import id_to_title

logger = logging.getLogger(__name__)

#ensure user exists in database and return their user_id
def _ensure_user(conn, username: str, prefer_id: Optional[int] = None) -> Optional[int]:
    cur = conn.cursor()

    #check if preferred user_id exists
    if prefer_id is not None:
        cur.execute(f"SELECT user_id FROM users WHERE user_id = {PH}", (prefer_id,))
        row = cur.fetchone()
        if row:
            return int(row[0])

    #look up existing user by username
    cur.execute(f"SELECT user_id FROM users WHERE username = {PH}", (username,))
    row = cur.fetchone()
    if row:
        return int(row[0])

    #create new user and return generated ID
    try:
        cur.execute(f"INSERT INTO users (username) VALUES ({PH}) RETURNING user_id", (username,))
        return int(cur.fetchone()[0])
    except Exception:
        #fallback for older sqlite
        cur.execute(f"INSERT INTO users (username) VALUES ({PH})", (username,))
        try:
            return int(cur.lastrowid)
        except Exception:
            cur.execute(f"SELECT user_id FROM users WHERE username = {PH}", (username,))
            return int(cur.fetchone()[0])

#resolve movie title to database movie_id
def _find_movie_id_by_title(conn, title: str) -> Optional[int]:
    if not title:
        return None
    cur = conn.cursor()

    #try exact match
    try:
        cur.execute(f"SELECT movie_id FROM movies WHERE LOWER(title) = LOWER({PH}) LIMIT 1", (title,))
        row = cur.fetchone()
        if row:
            return int(row[0])
    except Exception:
        pass

    #fallback to partial match
    try:
        cur.execute(f"SELECT movie_id FROM movies WHERE title LIKE {PH} LIMIT 1", (f"%{title}%",))
        row = cur.fetchone()
        if row:
            return int(row[0])
    except Exception:
        pass
    
    return None

#sync user profile JSON to database ratings table
def sync_user_ratings(profile_path: Path) -> bool:
    #load profile JSON file
    try:
        profile_path = Path(profile_path)
        data = json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("failed to read profile json")
        return False

    #extract username and preferred user_id
    username = data.get("username") or str(data.get("user_id") or "")
    prefer_id_raw = data.get("user_id")

    #coerce prefer_id to integer
    prefer_id = None
    try:
        if isinstance(prefer_id_raw, int):
            prefer_id = prefer_id_raw
        elif isinstance(prefer_id_raw, str) and prefer_id_raw.isdigit():
            prefer_id = int(prefer_id_raw)
    except Exception:
        prefer_id = None

    try:
        with get_db(readonly=False) as conn:
            cur = conn.cursor()

            #ensure user exists
            uid = _ensure_user(conn, username, prefer_id)
            if uid is None:
                logger.error("could not determine or create user id")
                return False

            #update JSON with resolved user_id
            try:
                if data.get("user_id") != uid:
                    data["user_id"] = uid
                    profile_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            except Exception:
                logger.exception("failed to update profile json user_id")

            #clear existing ratings for this user
            cur.execute(f"DELETE FROM ratings WHERE user_id = {PH}", (uid,))

            #insert all ratings from JSON
            inserted = 0
            for entry in data.get("ratings", []):
                movie_id = None
                movie_id_raw = entry.get("movie_id") if entry.get("movie_id") is not None else entry.get("movie")
                
                #try to parse as integer movie_id
                if movie_id_raw is not None:
                    try:
                        movie_id = int(movie_id_raw)
                    except Exception:
                        movie_id = None

                #if no numeric ID, try looking up by title
                if movie_id is None and entry.get("title"):
                    movie_id = _find_movie_id_by_title(conn, entry.get("title"))
                
                #fallback: check if "movie" field contains a title string
                if movie_id is None and entry.get("title") is None:
                    m = entry.get("movie")
                    if isinstance(m, str):
                        movie_id = _find_movie_id_by_title(conn, m)

                #skip entries without resolvable movie_id
                if movie_id is None:
                    logger.debug(f"skipping rating without resolvable movie_id: {entry}")
                    continue

                #extract and validate rating value
                rating = entry.get("rating")
                if rating is None:
                    logger.debug(f"skipping rating without value: {entry}")
                    continue
                
                try:
                    rating_val = float(rating)
                except Exception:
                    logger.debug(f"skipping non-numeric rating: {entry}")
                    continue

                #use provided timestamp or current time
                timestamp = int(entry.get("timestamp") or time.time())
                
                #insert rating into database
                cur.execute(
                    f"INSERT INTO ratings (user_id, movie_id, rating, timestamp) VALUES ({PH},{PH},{PH},{PH})",
                    (uid, movie_id, rating_val, timestamp),
                )
                inserted += 1

        logger.info(f"sync_user_ratings: user {username} (id={uid}) - inserted {inserted} ratings")
        return True

    except Exception:
        logger.exception("failed to sync profile to db")
        return False