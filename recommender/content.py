# recommender/content.py
from __future__ import annotations
from typing import List, Tuple, Dict
import numpy as np
import pandas as pd

from recommender.data_loader import load_movies_df, load_ratings_df
from database.connection import get_db
from database.paramstyle import ph_list
from database.db_query import top_unseen_for_user

# ----------------------------
# Feature building (genres + year)
# ----------------------------
def _build_item_features() -> tuple[pd.DataFrame, np.ndarray, dict[int, int]]:
    """
    Returns:
      meta_df: DataFrame with columns [movie_id, title, year, genres]
      X:       numpy array (n_items x n_features)
      id2row:  dict mapping movie_id -> row index in X
    """
    meta = load_movies_df(columns=["movie_id", "title", "year", "genres"]).copy()

    # Genres: pipe-separated -> multi-hot columns
    genres_split = (
        meta["genres"]
        .fillna("")
        .apply(lambda s: [t.strip() for t in str(s).split("|") if t.strip() and t.lower() != "(no genres listed)"])
    )
    all_genres = sorted({g for lst in genres_split for g in lst})
    for g in all_genres:
        meta[f"g::{g}"] = genres_split.apply(lambda lst, gg=g: 1.0 if gg in lst else 0.0)

    # Year: standardize (robust to missing)
    year = pd.to_numeric(meta["year"], errors="coerce")
    yr_mean = year.mean(skipna=True)
    yr_std = year.std(skipna=True) or 1.0
    meta["year_z"] = ((year.fillna(yr_mean) - yr_mean) / yr_std).astype(float)

    # Assemble feature matrix: [genres..., year_z]
    feat_cols = [c for c in meta.columns if c.startswith("g::")] + ["year_z"]
    X = meta[feat_cols].to_numpy(dtype=float)

    # L2 normalize item feature rows to make cosine easy later
    norms = np.linalg.norm(X, axis=1, keepdims=True) + 1e-9
    X = X / norms

    id2row = {int(mid): i for i, mid in enumerate(meta["movie_id"].astype(int).tolist())}
    return meta[["movie_id", "title", "year", "genres"]], X, id2row


def _user_profile_vector(user_id: int, X: np.ndarray, id2row: dict[int, int]) -> tuple[np.ndarray, list[int]]:
    """
    Build a user profile as a weighted average of the features of items they've rated.
    Returns (uvec, seen_movie_ids). If user has no ratings, returns (None, []).
    """
    df = load_ratings_df()
    u = df[df["user_id"] == user_id]
    if u.empty:
        return None, []

    # Keep only items present in our feature space
    rows = []
    weights = []
    for _, r in u.iterrows():
        mid = int(r["movie_id"])
        if mid in id2row:
            rows.append(id2row[mid])
            # Weight by normalized rating (0..1); you can also use (rating - mean) for mean-centering
            weights.append(float(r["rating"]) / 5.0)

    if not rows:
        return None, []

    V = X[rows, :]
    w = np.asarray(weights, dtype=float).reshape(-1, 1)
    uvec = (V * w).sum(axis=0)
    u_norm = np.linalg.norm(uvec) + 1e-9
    uvec = uvec / u_norm
    seen = [int(x) for x in u["movie_id"].tolist()]
    return uvec, seen


# ----------------------------
# Public API
# ----------------------------
def recommend_for_user(user_id: int, k: int = 20) -> List[Tuple[int, float]]:
    """
    Content-based recommendations for a user using genres + year.
    Returns list of (movie_id, score) sorted by score desc.
    Falls back to popular-unseen if user has no usable ratings.
    """
    meta, X, id2row = _build_item_features()
    uvec, seen = _user_profile_vector(user_id, X, id2row)

    if uvec is None:
        # Cold-start: no ratings -> fall back
        fallback = top_unseen_for_user(user_id, limit=k)
        return [(row["movie_id"], row["weighted_rating"]) for row in fallback]

    # Cosine similarity to all items
    scores = X @ uvec  # (n_items,)

    # Mask already-seen items
    if seen:
        seen_idx = [id2row[mid] for mid in seen if mid in id2row]
        scores[np.array(seen_idx, dtype=int)] = -np.inf

    # Top-k indices
    k = int(min(k, scores.shape[0]))
    if k <= 0:
        return []

    top_idx = np.argpartition(scores, -k)[-k:]
    top_idx = top_idx[np.argsort(scores[top_idx])[::-1]]

    mids = meta.iloc[top_idx]["movie_id"].astype(int).tolist()
    vals = scores[top_idx].astype(float).tolist()
    return list(zip(mids, vals))


def recommend_titles_for_user(user_id: int, k: int = 20) -> List[Dict]:
    """
    Same as recommend_for_user, but returns movie metadata for convenience:
    [{movie_id, title, score, year, genres, poster_url}]
    """
    recs = recommend_for_user(user_id=user_id, k=k)
    mids = [mid for mid, _ in recs]
    if not mids:
        return []

    with get_db(readonly=True) as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT movie_id, title, poster_url, year, genres
            FROM movies
            WHERE movie_id IN ({ph_list(len(mids))})
            """,
            mids,
        )
        rows = cur.fetchall()

    m = {
        int(mid): {"title": title, "poster_url": poster, "year": year, "genres": genres}
        for (mid, title, poster, year, genres) in rows
    }

    out = []
    for mid, score in recs:
        info = m.get(
            mid,
            {"title": f"ID {mid}", "poster_url": None, "year": None, "genres": None},
        )
        out.append(
            {
                "movie_id": mid,
                "title": info["title"],
                "score": float(score),
                "poster_url": info["poster_url"],
                "year": info["year"],
                "genres": info["genres"],
            }
        )
    return out
