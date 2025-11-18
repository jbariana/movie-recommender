# api/api.py
from pathlib import Path
import json
import time
import logging
from collections import Counter  # kept for potential legacy/profile JSON stats

from database.id_to_title import id_to_title, normalize_title
from database.connection import get_db

logger = logging.getLogger(__name__)

PROFILE_PATH = Path(__file__).resolve().parent.parent / "user_profile" / "user_profile.json"


def _resolve_title_from_entry(entry):
    """
    Return a human-friendly title for a rating entry.
    Accepts entries that may have 'title', 'movie' (string or id) or 'movie_id'.
    """
    if not entry:
        return None

    # explicit title field wins
    if entry.get("title"):
        return normalize_title(str(entry.get("title")))

    # movie field might be title or id
    m = entry.get("movie")
    if m is not None:
        try:
            mid = int(m)
            t = id_to_title(mid)
            return t if t else f"ID {mid}"
        except Exception:
            return normalize_title(str(m))

    # movie_id numeric id
    mid = entry.get("movie_id")
    if mid is not None:
        try:
            mid_i = int(mid)
            t = id_to_title(mid_i)
            return t if t else f"ID {mid_i}"
        except Exception:
            return normalize_title(str(mid))

    return None


def _to_bool(val):
    """
    Robustly convert payload values to bool.
    Accepts bool, str ("true"/"false"/"1"/"0"), int, etc.
    """
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    if isinstance(val, str):
        return val.strip().lower() in ("1", "true", "t", "yes", "on")
    return False


def handle_button_click(button_id, payload=None):
    payload = payload or {}

    # --- View Ratings (legacy: from profile JSON) ---
    if button_id == "view_ratings_button":
        try:
            data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except Exception:
            data = {"username": None, "user_id": None, "ratings": []}

        results = []
        for r in data.get("ratings", []):
            title = _resolve_title_from_entry(r) or (
                f"ID {r.get('movie_id')}" if r.get("movie_id") else "Untitled"
            )
            results.append(
                {
                    "movie_id": r.get("movie_id")
                    if r.get("movie_id") is not None
                    else r.get("movie"),
                    "title": title,
                    "movie": title,  # legacy key some front-end bits expect
                    "rating": r.get("rating"),
                    "timestamp": r.get("timestamp"),
                    "is_favorite": r.get("is_favorite", False),
                    "in_watchlist": r.get("in_watchlist", False),
                }
            )
        return {
            "ratings": results,
            "source": "profile",
            "username": data.get("username"),
            "user_id": data.get("user_id"),
        }

    # --- View Statistics (DB-backed with JSON fallback) ---
    if button_id == "view_statistics_button":
        from flask import session
        from database.users import get_user_by_username
        from database.db_query import get_user_rating_stats

        uname = session.get("username")
        if not uname:
            return {"error": "not_logged_in"}, 401

        user_row = get_user_by_username(uname)  # (user_id, username, password_hash)
        if not user_row:
            return {"error": "user_not_found"}, 404

        user_id = int(user_row[0])

        # 1) Try DB stats first
        stats = get_user_rating_stats(user_id) or {}
        total_db = int(stats.get("total", 0) or 0)
        avg_db = float(stats["avg"]) if stats.get("avg") is not None else 0.0
        by_genre_db = stats.get("by_genre", [])

        # 2) If DB has nothing yet, fall back to profile JSON (and try to sync)
        if total_db == 0:
            total_json = 0
            avg_json = 0.0
            try:
                # Best-effort sync (if profile JSON exists)
                try:
                    from api.sync_user_json import sync_user_ratings

                    if PROFILE_PATH.exists():
                        sync_user_ratings(PROFILE_PATH)
                        # re-read DB after sync
                        stats2 = get_user_rating_stats(user_id) or {}
                        if int(stats2.get("total", 0) or 0) > 0:
                            total_db = int(stats2.get("total", 0))
                            avg_db = (
                                float(stats2["avg"])
                                if stats2.get("avg") is not None
                                else 0.0
                            )
                            by_genre_db = stats2.get("by_genre", [])
                except Exception as ex:
                    logger.warning(
                        "stats: sync_user_ratings best-effort failed: %s", ex
                    )

                # If still zero, compute from local profile JSON as a fallback
                if total_db == 0 and PROFILE_PATH.exists():
                    prof = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
                    raw = [
                        float(r["rating"])
                        for r in prof.get("ratings", [])
                        if r.get("rating") is not None
                    ]
                    total_json = len(raw)
                    avg_json = round(sum(raw) / total_json, 2) if total_json else 0.0
            except Exception:
                logger.exception("stats: JSON fallback failed")

            if total_db == 0:
                statistics = {
                    "total_ratings": total_json,
                    "average_rating": avg_json,
                    "top_genres": [],  # genre breakdown needs DB join; omit in fallback
                }
                return {
                    "statistics": statistics,
                    "source": "stats_profile_fallback",
                }

        # 3) Normal DB response
        statistics = {
            "total_ratings": total_db,
            "average_rating": avg_db,
            "top_genres": [
                {"genre": g["genre"], "count": int(g.get("count", 0))}
                for g in (by_genre_db or [])
            ],
        }
        return {"statistics": statistics, "source": "stats_db"}

    # --- Get Recommendations ---
    if button_id == "get_rec_button":
        from recommender.baseline import recommend_titles_for_user

        try:
            profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
            uid = int(profile.get("user_id", 99))
        except Exception:
            uid = 99

        recs = recommend_titles_for_user(uid)

        results = []
        for item in recs:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                first, score = item[0], item[1]
                title = (
                    id_to_title(first)
                    if isinstance(first, int)
                    else normalize_title(str(first))
                )
                try:
                    rating_val = float(score)
                except Exception:
                    rating_val = None
                results.append({"title": title, "movie": title, "rating": rating_val})
            else:
                title = _resolve_title_from_entry(
                    item if isinstance(item, dict) else {"movie": item}
                )
                results.append({"title": title, "movie": title, "rating": None})

        return {"ratings": results, "source": "recs"}

    # --- Add Rating (JSON + DB write with favorite/watchlist flags) ---
    if button_id == "add_rating_submit":
        movie_id = payload.get("movie_id") or payload.get("movie")
        rating = payload.get("rating")
        if movie_id is None:
            return {"ok": False, "error": "No movie_id provided."}
        if rating is None:
            return {"ok": False, "error": "No rating provided."}

        # parse favorite/watchlist flags from payload
        is_favorite = _to_bool(payload.get("is_favorite", False))
        in_watchlist = _to_bool(payload.get("in_watchlist", False))

        try:
            # read or create profile JSON
            if PROFILE_PATH.exists():
                prof = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
            else:
                prof = {"username": None, "user_id": None, "ratings": []}

            # normalize numeric movie id when possible
            try:
                mid_val = int(movie_id)
            except Exception:
                mid_val = None

            # remove any existing rating for same movie in JSON profile
            prof["ratings"] = [
                r
                for r in prof.get("ratings", [])
                if str(
                    r.get("movie_id")
                    if r.get("movie_id") is not None
                    else r.get("movie")
                )
                != str(movie_id)
            ]

            ts = int(time.time())
            new_entry = {
                "movie_id": mid_val if mid_val is not None else movie_id,
                "rating": float(rating),
                "timestamp": ts,
                "is_favorite": is_favorite,
                "in_watchlist": in_watchlist,
            }
            prof.setdefault("ratings", []).append(new_entry)
            PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            PROFILE_PATH.write_text(
                json.dumps(prof, indent=2), encoding="utf-8"
            )

            # --- write directly to DB with flags ---
            try:
                from flask import session
                from database.users import get_user_by_username

                uname = session.get("username")
                user_id_db = None
                if uname:
                    ur = get_user_by_username(uname)  # (id, username, hash) or dict
                    if ur is not None:
                        # tuple-like
                        try:
                            user_id_db = int(ur[0])
                        except Exception:
                            # dict-like fallback
                            if isinstance(ur, dict):
                                for k in ("user_id", "id", "USER_ID", "ID"):
                                    if k in ur:
                                        user_id_db = int(ur[k])
                                        break

                if user_id_db and mid_val is not None:
                    save_rating(
                        user_id_db,
                        mid_val,
                        rating,
                        is_favorite=is_favorite,
                        in_watchlist=in_watchlist,
                    )
                else:
                    logger.warning(
                        "add_rating_submit: could not resolve user_id or movie_id for DB write (user_id=%s, mid_val=%s)",
                        user_id_db,
                        mid_val,
                    )
            except Exception as ex:
                logger.warning("save_rating with flags failed: %s", ex)

            # cache bust (optional but kept from your previous logic)
            try:
                from flask import session
                from database.users import get_user_by_username
                from cache import cache, key_content_recs

                uname = session.get("username")
                user_id_for_cache = None
                if uname:
                    ur = get_user_by_username(uname)
                    if ur:
                        try:
                            user_id_for_cache = int(ur[0])
                        except Exception:
                            if isinstance(ur, dict):
                                for k in ("user_id", "id", "USER_ID", "ID"):
                                    if k in ur:
                                        user_id_for_cache = int(ur[k])
                                        break

                if user_id_for_cache:
                    for size in (10, 20, 50, 100):
                        cache.delete(
                            key_content_recs(user_id=user_id_for_cache, k=size)
                        )
            except Exception as _ex:
                logger.warning("cache bust on rating failed: %s", _ex)

            # return updated ratings with titles and flags from JSON profile
            results = []
            for r in prof.get("ratings", []):
                title = _resolve_title_from_entry(r) or (
                    f"ID {r.get('movie_id')}" if r.get("movie_id") else "Untitled"
                )
                results.append(
                    {
                        "title": title,
                        "rating": r.get("rating"),
                        "movie_id": r.get("movie_id"),
                        "timestamp": r.get("timestamp"),
                        "is_favorite": r.get("is_favorite", False),
                        "in_watchlist": r.get("in_watchlist", False),
                    }
                )

            return {
                "ok": True,
                "message": "Rating saved.",
                "ratings": results,
                "source": "profile",
            }

        except Exception as ex:
            logger.exception("Failed to add rating")
            return {"ok": False, "error": str(ex)}

    # --- Remove Rating (accept both 'remove_rating_button' and 'remove_rating') ---
    if button_id in ("remove_rating_button", "remove_rating"):
        movie_id = payload.get("movie_id") or payload.get("movie")
        if movie_id is None:
            return {"ok": False, "error": "No movie_id provided."}

        try:
            if PROFILE_PATH.exists():
                prof = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
            else:
                prof = {"username": None, "user_id": None, "ratings": []}

            before = len(prof.get("ratings", []))
            prof["ratings"] = [
                r
                for r in prof.get("ratings", [])
                if str(
                    r.get("movie_id")
                    if r.get("movie_id") is not None
                    else r.get("movie")
                )
                != str(movie_id)
            ]
            after = len(prof.get("ratings", []))
            PROFILE_PATH.write_text(
                json.dumps(prof, indent=2), encoding="utf-8"
            )

            try:
                from api.sync_user_json import sync_user_ratings

                sync_user_ratings(PROFILE_PATH)
            except Exception as ex:
                logger.warning("sync_user_ratings failed on remove: %s", ex)

            return {
                "ok": True,
                "message": "Removed."
                if before != after
                else "No rating found.",
                "ratings": prof.get("ratings", []),
                "source": "profile",
            }
        except Exception as ex:
            logger.exception("Failed to remove rating")
            return {"ok": False, "error": str(ex)}

    # --- Search ---
    if button_id == "search":
        query = (payload or {}).get("query") or ""
        query = str(query).strip()
        if not query:
            return {"ratings": [], "source": "search", "query": query}
        try:
            from database.db_query import search_movies_by_keyword

            rows = search_movies_by_keyword(query, limit=30)
            results = []
            for r in rows:
                title = r.get("title") or (
                    id_to_title(r.get("movie_id"))
                    if r.get("movie_id")
                    else None
                )
                display = (
                    title
                    if title
                    else (
                        f"ID {r.get('movie_id')}"
                        if r.get("movie_id")
                        else "Untitled"
                    )
                )
                results.append(
                    {
                        "movie_id": r.get("movie_id"),
                        "title": display,
                        "movie": display,
                        "year": r.get("year"),
                        "genres": r.get("genres"),
                    }
                )
            return {"ratings": results, "source": "search", "query": query}
        except Exception as ex:
            logger.exception("Search failed")
            return {"ratings": [], "source": "search", "error": str(ex)}

    # --- Fallback ---
    return {"error": f"Unhandled button id: {button_id}"}


def save_rating(user_id, movie_id, rating, is_favorite=False, in_watchlist=False):
    """
    Save a user's rating for a movie into the database.
    Upsert style (delete then insert) to keep a single row per (user, movie).
    Also persists favorite/watchlist flags.
    """
    from database.paramstyle import PH

    with get_db(readonly=False) as conn:
        cur = conn.cursor()
        # delete existing row
        cur.execute(
            f"DELETE FROM ratings WHERE user_id = {PH} AND movie_id = {PH};",
            (user_id, movie_id),
        )
        # insert new row with flags
        cur.execute(
            f"""
            INSERT INTO ratings (user_id, movie_id, rating, timestamp, is_favorite, in_watchlist)
            VALUES ({PH}, {PH}, {PH}, {PH}, {PH}, {PH});
            """,
            (
                user_id,
                movie_id,
                float(rating),
                int(time.time()),
                bool(is_favorite),
                bool(in_watchlist),
            ),
        )


def get_user_profile(user_id):
    """
    Return a summary of a user's profile from the DB:
        {
          "username": "user_<id>",
          "average_rating": float,
          "ratings": [(title, rating), ...],
          "favorites": [(title,), ...]  # rating >= 4
        }
    """
    ratings = []
    total = 0.0

    with get_db(readonly=True) as conn:
        cur = conn.cursor()
        # fetch user ratings joined to movie titles (works for PG/SQLite)
        try:
            cur.execute(
                "SELECT r.movie_id, r.rating, m.title "
                "FROM ratings r LEFT JOIN movies m ON m.movie_id = r.movie_id "
                "WHERE r.user_id = %s;"
                if conn.__class__.__module__.startswith("psycopg2")
                else "SELECT r.movie_id, r.rating, m.title "
                "FROM ratings r LEFT JOIN movies m ON m.movie_id = r.movie_id "
                "WHERE r.user_id = ?;",
                (user_id,),
            )
        except Exception:
            # minimal fallback
            cur.execute(
                "SELECT movie_id, rating FROM ratings WHERE user_id = %s;"
                if conn.__class__.__module__.startswith("psycopg2")
                else "SELECT movie_id, rating FROM ratings WHERE user_id = ?;",
                (user_id,),
            )
        rows = cur.fetchall()

    for row in rows:
        movie_id = row[0]
        rating = float(row[1])
        title = None
        try:
            title = row[2]
        except Exception:
            title = None

        if not title:
            title = id_to_title(int(movie_id)) or f"ID {int(movie_id)}"

        ratings.append((title, rating))
        total += rating

    avg_rating = round(total / len(ratings), 2) if ratings else 0.0
    favorites = [(title,) for title, r in ratings if r >= 4.0]

    profile = {
        "username": f"user_{user_id}",
        "average_rating": avg_rating,
        "ratings": ratings,
        "favorites": favorites,
    }
    return profile
