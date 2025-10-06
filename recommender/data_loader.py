# recommender/data_loader.py
from __future__ import annotations
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/ml-latest-small")
PROFILE_JSON = Path("profile/user_profile.json")

def _load_core_ratings() -> pd.DataFrame:
    """MovieLens ratings.csv -> DataFrame[userId,movieId,rating]"""
    return pd.read_csv(DATA_DIR / "ratings.csv", usecols=["userId", "movieId", "rating"])

def _load_extra_ratings() -> pd.DataFrame:
    """Ratings saved by /sync-profile -> same columns (may be empty)."""
    if not PROFILE_JSON.exists():
        return pd.DataFrame(columns=["userId", "movieId", "rating"])
    data = pd.read_json(PROFILE_JSON)
    rows = data.get("ratings", [])
    if isinstance(rows, list):
        return pd.DataFrame(rows, columns=["userId", "movieId", "rating"])
    return pd.DataFrame(columns=["userId", "movieId", "rating"])

def load_ratings_df() -> pd.DataFrame:
    """Core MovieLens + any user-synced ratings."""
    base = _load_core_ratings()
    extra = _load_extra_ratings()
    if not extra.empty:
        base = pd.concat([base, extra], ignore_index=True)
    return base

def load_user_item_matrix() -> pd.DataFrame:
    """
    Pivot to users x movies float matrix with NaN for unrated.
    This is what your baseline() expects.
    """
    df = load_ratings_df()
    ui = df.pivot_table(index="userId", columns="movieId", values="rating", aggfunc="mean")
    return ui.sort_index(axis=0).sort_index(axis=1)

def get_movie_titles(movie_ids: list[int]) -> dict[int, str]:
    """Return {movieId: title} for the ids requested."""
    m = pd.read_csv(DATA_DIR / "movies.csv", usecols=["movieId", "title"])
    m["movieId"] = m["movieId"].astype(int)
    subset = m[m["movieId"].isin(movie_ids)]
    return dict(zip(subset["movieId"], subset["title"]))
