from pathlib import Path
import json
import time
import logging
from collections import Counter
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


def handle_button_click(button_id, payload=None):
    payload = payload or {}

    # --- View Ratings ---
    if button_id == "view_ratings_button":
        try:
            data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except Exception:
            data = {"username": None, "user_id": None, "ratings": []}

        results = []
        for r in data.get("ratings", []):
            title = _resolve_title_from_entry(r) or (f"ID {r.get('movie_id')}" if r.get("movie_id") else "Untitled")
            results.append({
                "movie_id": r.get("movie_id") if r.get("movie_id") is not None else r.get("movie"),
                "title": title,
                "movie": title,  # legacy keys front-end may expect
                "rating": r.get("rating"),
                "timestamp": r.get("timestamp"),
            })
        return {
            "ratings": results,
            "source": "profile",
            "username": data.get("username"),
            "user_id": data.get("user_id"),
        }

    # --- View Statistics ---
    if button_id == "view_statistics_button":
        data = json.loads(PROFILE_PATH.read_text())
        raw_ratings = [r.get("rating") for r in data.get("ratings", []) if r.get("rating") is not None]
        total = len(raw_ratings)
        counts = Counter()
        for v in raw_ratings:
            try:
                iv = int(v)
            except Exception:
                continue
            counts[iv] += 1

        stats_items = [
            ("Num ratings", total),
            ("Num 5s", counts.get(5, 0)),
            ("Num 4s", counts.get(4, 0)),
            ("Num 3s", counts.get(3, 0)),
            ("Num 2s", counts.get(2, 0)),
            ("Num 1s", counts.get(1, 0)),
        ]
        results = [{"title": name, "rating": value} for name, value in stats_items]
        return {"ratings": results, "source": "stats"}

    # --- Get Recommendations ---
    if button_id == "get_rec_button":
        from recommender.baseline import recommend_titles_for_user
        try:
            profile = json.loads(PROFILE_PATH.read_text())
            uid = int(profile.get("user_id", 99))
        except Exception:
            uid = 99

        recs = recommend_titles_for_user(uid)

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

        return {"ratings": results, "source": "recs"}

    # --- Add Rating ---
    if button_id == "add_rating_submit":
        movie_id = payload.get("movie_id") or payload.get("movie")
        rating = payload.get("rating")
        if movie_id is None:
            return {"ok": False, "error": "No movie_id provided."}
        if rating is None:
            return {"ok": False, "error": "No rating provided."}

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

            # remove any existing rating for same movie
            prof["ratings"] = [
                r for r in prof.get("ratings", [])
                if str(r.get("movie_id") if r.get("movie_id") is not None else r.get("movie")) != str(movie_id)
            ]

            new_entry = {
                "movie_id": mid_val if mid_val is not None else movie_id,
                "rating": float(rating),
                "timestamp": int(time.time())
            }
            prof.setdefault("ratings", []).append(new_entry)
            PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            PROFILE_PATH.write_text(json.dumps(prof, indent=2), encoding="utf-8")

            # attempt sync to DB (best-effort)
            try:
                from api.sync_user_json import sync_user_ratings
                sync_user_ratings(PROFILE_PATH)
            except Exception as ex:
                logger.warning("sync_user_ratings failed on add: %s", ex)

            # return updated ratings with titles
            results = []
            for r in prof.get("ratings", []):
                title = _resolve_title_from_entry(r) or (f"ID {r.get('movie_id')}" if r.get("movie_id") else "Untitled")
                results.append({"title": title, "rating": r.get("rating"), "movie_id": r.get("movie_id"), "timestamp": r.get("timestamp")})

            return {"ok": True, "message": "Rating saved.", "ratings": results, "source": "profile"}

        except Exception as ex:
            logger.exception("Failed to add rating")
            return {"ok": False, "error": str(ex)}

    # --- Remove Rating ---
    if button_id == "remove_rating_button":
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
                r for r in prof.get("ratings", [])
                if str(r.get("movie_id") if r.get("movie_id") is not None else r.get("movie")) != str(movie_id)
            ]
            after = len(prof.get("ratings", []))
            PROFILE_PATH.write_text(json.dumps(prof, indent=2), encoding="utf-8")

            try:
                from api.sync_user_json import sync_user_ratings
                sync_user_ratings(PROFILE_PATH)
            except Exception as ex:
                logger.warning("sync_user_ratings failed on remove: %s", ex)

            return {"ok": True, "message": "Removed." if before != after else "No rating found.", "ratings": prof.get("ratings", []), "source": "profile"}
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

    # --- Get Recommendations / Search / other actions are handled elsewhere in codebase ---
    return {"error": f"Unhandled button id: {button_id}"}

def save_rating(user_id, movie_id, rating):
    """
    Save a user's rating for a movie into the database.
    """
    db = get_db()
    db.execute(
        "INSERT INTO user_ratings (user_id, movie_id, rating) VALUES (?, ?, ?)",
        (user_id, movie_id, rating)
    )
    db.commit()


def get_user_profile(user_id):
    """
    Return a summary of a user's profile, including average rating, ratings list, and favorites.
    """
    db = get_db()

    rows = db.execute(
        "SELECT movie_id, rating FROM user_ratings WHERE user_id = ?",
        (user_id,)
    ).fetchall()

    ratings = []
    total = 0
    for row in rows:
        title = id_to_title(row["movie_id"])
        ratings.append((title, row["rating"]))
        total += row["rating"]

    avg_rating = round(total / len(rows), 2) if rows else 0

    favorites = [(title,) for title, rating in ratings if rating >= 4]

    profile = {
        "username": f"user_{user_id}",
        "average_rating": avg_rating,
        "ratings": ratings,
        "favorites": favorites
    }

    return profile
