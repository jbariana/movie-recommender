from pathlib import Path
import json
from collections import Counter
from database.id_to_title import id_to_title, normalize_title

PROFILE_PATH = Path(__file__).resolve().parent.parent / "user_profile" / "user_profile.json"


def _resolve_title_from_entry(entry):
    if entry.get("title"):
        return normalize_title(entry.get("title"))
    mid = entry.get("movie_id") if entry.get("movie_id") is not None else entry.get("movie")
    if mid is None:
        return "Untitled"
    try:
        mid_int = int(mid)
        title = id_to_title(mid_int)
        return title or f"Movie ID {mid_int}"
    except Exception:
        return normalize_title(str(mid))


def handle_button_click(button_id, payload=None):
    payload = payload or {}

    # --- View Ratings ---
    if button_id == "view_ratings_button":
        data = json.loads(PROFILE_PATH.read_text())
        results = []
        for r in data.get("ratings", []):
            title = _resolve_title_from_entry(r)
            results.append({
                "title": title,
                "rating": r.get("rating"),
                "timestamp": r.get("timestamp")
            })
        return {"ratings": results, "source": "profile"}

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
        recs = recommend_titles_for_user(99)

        results = []
        for item in recs:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                first, score = item[0], item[1]
                title = id_to_title(first) if isinstance(first, int) else normalize_title(str(first))
                try:
                    rating_val = float(score)
                except Exception:
                    rating_val = None
                results.append({"title": title, "rating": rating_val})
            else:
                title = _resolve_title_from_entry(item if isinstance(item, dict) else {"movie": item})
                results.append({"title": title, "rating": None})

        return {"ratings": results, "source": "recs"}

    # --- Add Rating ---
    if button_id == "add_rating_submit":
        movie_id = payload.get("movie_id")
        rating = payload.get("rating")

        if not movie_id:
            return {"ok": False, "error": "No movie ID provided."}
        if rating is None:
            return {"ok": False, "error": "No rating provided."}

        try:
            data = json.loads(PROFILE_PATH.read_text())

            # Remove previous rating for the same movie
            data["ratings"] = [
                r for r in data.get("ratings", [])
                if str(r.get("movie_id")) != str(movie_id)
            ]

            # Add new rating
            new_entry = {
                "movie_id": movie_id,
                "rating": int(rating),
                "timestamp": "now"
            }
            data["ratings"].append(new_entry)
            PROFILE_PATH.write_text(json.dumps(data, indent=2))

            # Try syncing to DB
            from api.sync_user_json import sync_user_ratings
            sync_user_ratings(movie_id)

            # Return updated list
            results = []
            for r in data["ratings"]:
                title = _resolve_title_from_entry(r)
                results.append({
                    "title": title,
                    "rating": r.get("rating"),
                    "timestamp": r.get("timestamp")
                })

            return {
                "ok": True,
                "message": f"Added rating {rating} for movie ID {movie_id}.",
                "ratings": results,
                "source": "profile"
            }

        except Exception as ex:
            return {"ok": False, "error": f"Failed to update: {ex}"}

    # --- Remove Rating ---
    if button_id == "remove_rating_button":
        movie_id = payload.get("movie_id")
        if not movie_id:
            return {"ok": False, "error": "No movie ID provided."}

        try:
            data = json.loads(PROFILE_PATH.read_text())
            before = len(data.get("ratings", []))
            data["ratings"] = [
                r for r in data.get("ratings", [])
                if str(r.get("movie_id")) != str(movie_id)
            ]
            after = len(data["ratings"])
            PROFILE_PATH.write_text(json.dumps(data, indent=2))

            removed = before != after
            return {
                "ok": True,
                "message": "Rating removed." if removed else "No rating found for that movie ID.",
                "ratings": data["ratings"],
                "source": "profile"
            }

        except Exception as ex:
            return {"ok": False, "error": f"Failed to remove rating: {ex}"}

    # --- Default ---
    return {
        "ratings": [
            {"title": "Inception", "rating": 5},
            {"title": "Titanic", "rating": 4},
        ],
        "source": "fallback",
    }
