# api/sync_service.py
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from api.schemas import SyncProfileRequest, RecommendRequest
import pandas as pd
from pathlib import Path

# Your storage for extra user ratings
from database.sync_json import sync_user_ratings

app = FastAPI(title="Movie Recommender API", version="0.1.0")


# ---------- helpers ----------

def _load_movies_title_map() -> dict[int, str]:
    """Load MovieLens movieId -> title map."""
    movies_csv = Path("data/ml-latest-small/movies.csv")
    if not movies_csv.exists():
        return {}
    df = pd.read_csv(movies_csv, usecols=["movieId", "title"])
    return dict(zip(df["movieId"].astype(int), df["title"].astype(str)))


def _recommend_ids(user_id: int, top_n: int) -> list[int]:
    """
    Returns a list of movieIds for the given user, using whichever baseline you have:
    - If you implemented function-style baseline.recommend_for_user(user_id, k)
    - Otherwise, falls back to class-style BaselineRecommender with load_ratings_df()
    """
    # Try function-based baseline first (your version)
    try:
        from recommender.baseline import recommend_for_user as _func
        recs = _func(user_id=user_id, k=top_n)  # [(movieId, score)]
        return [int(mid) for mid, _ in recs]
    except Exception:
        # Fall back to class-based baseline (my version)
        try:
            from recommender.baseline import BaselineRecommender
            from recommender.data_loader import load_ratings_df
            ratings = load_ratings_df()
            model = BaselineRecommender().fit(ratings)
            return [int(mid) for mid in model.recommend_for_user(ratings, user_id=user_id, top_n=top_n)]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Recommendation error: {e}") from e


# ---------- endpoints ----------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/sync-profile")
def sync_profile(body: SyncProfileRequest):
    """
    Accepts: { "ratings": [ {userId, movieId, rating}, ... ] }
    Persists ratings to profile/user_profile.json (via database.sync_json).
    """
    try:
        df = pd.DataFrame([r.dict() for r in body.ratings])
        sync_user_ratings(df)
        return {"ok": True, "count": len(df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend")
def recommend(body: RecommendRequest):
    """
    Returns: { "userId": int, "recommendations": [movieId, ...] }
    """
    try:
        mids = _recommend_ids(user_id=body.userId, top_n=body.topN)
        return {"userId": body.userId, "recommendations": mids}
    except HTTPException:
        raise
    except AssertionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend-titles")
def recommend_with_titles(body: RecommendRequest):
    """
    Same as /recommend but includes movie titles for a nicer demo:
    Returns: { "userId": int, "recommendations": [ {movieId, title}, ... ] }
    """
    try:
        mids = _recommend_ids(user_id=body.userId, top_n=body.topN)
        title_map = _load_movies_title_map()
        return {
            "userId": body.userId,
            "recommendations": [
                {"movieId": mid, "title": title_map.get(mid, f"Movie {mid}")}
                for mid in mids
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
