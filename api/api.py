from pathlib import Path
import json
from database.id_to_title import id_to_title, normalize_title

PROFILE_PATH = Path(__file__).resolve().parent.parent / "user_profile" / "user_profile.json"

def _resolve_title_from_entry(entry):
    # entry may contain "title", "movie" (id or name) or "movie_id"
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

def handle_button_click(button_id):
    if button_id == "view_ratings_button":
        data = json.loads(PROFILE_PATH.read_text())
        results = []
        for r in data.get("ratings", []):
            title = _resolve_title_from_entry(r)
            results.append({"title": title, "rating": r.get("rating"), "timestamp": r.get("timestamp")})
        return {"ratings": results, "source": "profile"}

    if button_id == "get_rec_button":
        from recommender.baseline import recommend_titles_for_user

        recs = recommend_titles_for_user(99)

        results = []
        for item in recs:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                first, score = item[0], item[1]
                if isinstance(first, int):
                    title = id_to_title(first) or f"Movie ID {first}"
                else:
                    title = normalize_title(str(first))
                try:
                    rating_val = float(score)
                except Exception:
                    rating_val = None
                results.append({"title": title, "rating": rating_val})
            else:
                if isinstance(item, dict):
                    title = _resolve_title_from_entry(item)
                elif isinstance(item, int):
                    title = id_to_title(item) or f"Movie ID {item}"
                else:
                    title = normalize_title(str(item))
                results.append({"title": title, "rating": None})
        return {"ratings": results, "source": "recs"}

    # fallback example for other buttons
    return {
        "ratings": [
            {"title": "Inception", "rating": 5},
            {"title": "Titanic", "rating": 4},
        ],
        "source": "fallback",
    }