# api/api.py
from pathlib import Path
import json
import time
import logging
from collections import Counter  # kept for potential legacy/profile JSON stats

from database.id_to_title import id_to_title, normalize_title
from database.connection import get_db

logger = logging.getLogger(__name__)

# Legacy single-file fallback kept for backwards-compatibility,
# but prefer per-user files returned by profile_path_for_username().
LEGACY_PROFILE_PATH = Path(__file__).resolve().parent.parent / "user_profile" / "user_profile.json"

def profile_path_for_username(username: str | None) -> Path:
    PROFILE_DIR = Path(__file__).resolve().parent.parent / "user_profile"
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    if username:
        safe = "".join(c for c in username if c.isalnum() or c in ("_", "-")).lower()
        return PROFILE_DIR / f"{safe}.json"
    return LEGACY_PROFILE_PATH


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


def handle_button_click(button_id, payload=None):
    payload = payload or {}

    from flask import session
    from database.users import get_user_by_username
    from database.db_query import get_ratings_for_user, upsert_rating, delete_rating

    uname = session.get("username")
    if button_id == "view_ratings_button":
        if not uname:
            return {"error": "not_logged_in"}, 401
        user_row = get_user_by_username(uname)
        if not user_row:
            return {"error": "user_not_found"}, 404
        # user_row may be tuple-like; assume id at index 0
        user_id = int(user_row[0])
        try:
            ratings = get_ratings_for_user(user_id)
            return {"ratings": ratings, "source": "db", "username": uname}
        except Exception as ex:
            logger.exception("view_ratings failed")
            return {"error": "internal"}, 500

    if button_id == "add_rating_submit":
        if not uname:
            return {"ok": False, "error": "not_logged_in"}, 401
        movie_id = payload.get("movie_id") or payload.get("movie")
        rating = payload.get("rating")
        if movie_id is None or rating is None:
            return {"ok": False, "error": "movie_id and rating required"}, 400
        user_row = get_user_by_username(uname)
        if not user_row:
            return {"ok": False, "error": "user_not_found"}, 404
        user_id = int(user_row[0])
        try:
            upsert_rating(user_id=user_id, movie_id=int(movie_id), rating=float(rating))
            return {"ok": True, "message": "Rating saved"}
        except Exception as ex:
            logger.exception("Failed to save rating")
            return {"ok": False, "error": str(ex)}, 500

    if button_id in ("remove_rating_button", "remove_rating"):
        if not uname:
            return {"ok": False, "error": "not_logged_in"}, 401
        movie_id = payload.get("movie_id") or payload.get("movie")
        if movie_id is None:
            return {"ok": False, "error": "movie_id required"}, 400
        user_row = get_user_by_username(uname)
        if not user_row:
            return {"ok": False, "error": "user_not_found"}, 404
        user_id = int(user_row[0])
        try:
            deleted = delete_rating(user_id=user_id, movie_id=int(movie_id))
            return {"ok": True, "deleted": deleted}
        except Exception as ex:
            logger.exception("Failed to delete rating")
            return {"ok": False, "error": str(ex)}, 500

    # --- View Statistics (DB-backed only) ---
    if button_id == "view_statistics_button":
        from database.users import get_user_by_username
        from database.db_query import get_user_rating_stats

        if not uname:
            return {"error": "not_logged_in"}, 401

        user_row = get_user_by_username(uname)
        if not user_row:
            return {"error": "user_not_found"}, 404

        user_id = int(user_row[0])

        # DB-only stats (no JSON fallback)
        try:
            stats = get_user_rating_stats(user_id) or {}
            total_db = int(stats.get("total", 0) or 0)
            avg_db = float(stats["avg"]) if stats.get("avg") is not None else 0.0
            by_genre_db = stats.get("by_genre", []) or []

            statistics = {
                "total_ratings": total_db,
                "average_rating": avg_db,
                "top_genres": [
                    {"genre": g["genre"], "count": int(g.get("count", 0))}
                    for g in by_genre_db
                ],
            }
            return {"statistics": statistics, "source": "stats_db"}
        except Exception:
            logger.exception("stats: DB query failed")
            return {"error": "internal"}, 500

    # --- Get Recommendations (DB-backed user id) ---
    if button_id == "get_rec_button":
        from recommender.baseline import recommend_titles_for_user
        from database.users import get_user_by_username

        try:
            if uname:
                user_row = get_user_by_username(uname)
                uid = int(user_row[0]) if user_row else None
            else:
                uid = None

            # if no user available, pass None/anonymous to recommender
            recs = recommend_titles_for_user(uid) if uid is not None else recommend_titles_for_user(None)

            results = []
            for item in recs:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    first, score = item[0], item[1]
                    title = id_to_title(first) if isinstance(first, int) else normalize_title(str(first))
                    try:
                        rating_val = float(score)
                    except Exception:
                        rating_val = None
                    results.append({"title": title, "movie": title, "rating": rating_val})
                else:
                    title = _resolve_title_from_entry(item if isinstance(item, dict) else {"movie": item})
                    results.append({"title": title, "movie": title, "rating": None})

            return {"ratings": results, "source": "recs_db"}
        except Exception:
            logger.exception("recs: failed")
            return {"error": "internal"}, 500

    # --- Add Rating: save to DB directly ---
    if button_id == "add_rating_submit":
        movie_id = payload.get("movie_id") or payload.get("movie")
        rating = payload.get("rating")
        if movie_id is None:
            return {"ok": False, "error": "No movie_id provided."}
        if rating is None:
            return {"ok": False, "error": "No rating provided."}

        try:
            if not uname:
                return {"ok": False, "error": "not_logged_in"}, 401

            from database.users import get_user_by_username
            from database.db_query import upsert_rating

            user_row = get_user_by_username(uname)
            if not user_row:
                return {"ok": False, "error": "user_not_found"}, 404
            user_id = int(user_row[0])

            upsert_rating(user_id=user_id, movie_id=int(movie_id), rating=float(rating))

            # invalidate any in-process cache elsewhere if needed (already handled server-side cache)
            return {"ok": True, "message": "Rating saved", "user_id": user_id}
        except Exception as ex:
            logger.exception("Failed to add rating")
            return {"ok": False, "error": str(ex)}

    # --- Remove Rating ---
    if button_id in ("remove_rating_button", "remove_rating"):
        movie_id = payload.get("movie_id") or payload.get("movie")
        if movie_id is None:
            return {"ok": False, "error": "No movie_id provided."}
        try:
            if not uname:
                return {"ok": False, "error": "not_logged_in"}, 401

            from database.users import get_user_by_username
            from database.db_query import delete_rating

            user_row = get_user_by_username(uname)
            if not user_row:
                return {"ok": False, "error": "user_not_found"}, 404
            user_id = int(user_row[0])

            deleted = delete_rating(user_id=user_id, movie_id=int(movie_id))
            return {"ok": True, "message": f"Deleted {deleted} rows", "deleted": deleted}
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
                title = r.get("title") or (id_to_title(r.get("movie_id")) if r.get("movie_id") else None)
                display = title if title else (f"ID {r.get('movie_id')}" if r.get("movie_id") else "Untitled")
                results.append({
                    "movie_id": r.get("movie_id"),
                    "title": display,
                    "movie": display,
                    "year": r.get("year"),
                    "genres": r.get("genres"),
                })
            return {"ratings": results, "source": "search", "query": query}
        except Exception as ex:
            logger.exception("Search failed")
            return {"ratings": [], "source": "search", "error": str(ex)}

    # --- Fallback ---
    return {"error": f"Unhandled button id: {button_id}"}


def save_rating(user_id, movie_id, rating):
    """
    Save a user's rating for a movie into the database.
    Upsert style (delete then insert) to keep a single row per (user, movie).
    """
    from database.paramstyle import PH
    with get_db(readonly=False) as conn:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM ratings WHERE user_id = {PH} AND movie_id = {PH};", (user_id, movie_id))
        cur.execute(
            f"INSERT INTO ratings (user_id, movie_id, rating, timestamp) VALUES ({PH}, {PH}, {PH}, {PH});",
            (user_id, movie_id, float(rating), int(time.time()))
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
                "WHERE r.user_id = %s;" if conn.__class__.__module__.startswith("psycopg2")
                else "SELECT r.movie_id, r.rating, m.title "
                     "FROM ratings r LEFT JOIN movies m ON m.movie_id = r.movie_id "
                     "WHERE r.user_id = ?;",
                (user_id,)
            )
        except Exception:
            # minimal fallback
            cur.execute(
                "SELECT movie_id, rating FROM ratings WHERE user_id = %s;" if conn.__class__.__module__.startswith("psycopg2")
                else "SELECT movie_id, rating FROM ratings WHERE user_id = ?;",
                (user_id,)
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
        "favorites": favorites
    }
    return profile
