"""
baseline.py
Very small item–item cosine similarity recommender using the SQLite-loaded data.
This is just to prove the DB + loader works for modeling.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import List, Tuple
from .data_loader import load_user_item_matrix, get_movie_titles

def _cosine_sim(A: np.ndarray) -> np.ndarray:
    # A: users x items (NaNs -> 0)
    A = np.nan_to_num(A, copy=False)
    norms = np.linalg.norm(A, axis=0, keepdims=True) + 1e-9
    A_norm = A / norms
    return A_norm.T @ A_norm   # items x items

def fit_item_item():
    ui = load_user_item_matrix()             # users x movies
    sim = _cosine_sim(ui.values)             # movies x movies
    movie_ids = ui.columns.to_numpy()
    return sim, movie_ids

def recommend_for_user(user_id: int, k: int = 10) -> List[Tuple[int, float]]:
    """
    Returns a list of (movie_id, score) for the given user.
    Simple score = sum(similarity to items the user rated) * rating.
    """
    ui = load_user_item_matrix()
    if user_id not in ui.index:
        return []
    sim, movie_ids = fit_item_item()

    user_ratings = ui.loc[user_id]           # Series of ratings indexed by movie_id
    rated = user_ratings.dropna()
    if rated.empty:
        return []

    # map rated movie ids to indices in sim matrix
    id_to_idx = {mid: i for i, mid in enumerate(movie_ids)}
    rated_idx = np.array([id_to_idx[m] for m in rated.index], dtype=int)

    # score all movies by similarity to rated ones, weighted by rating
    weights = rated.values
    scores = (sim[:, rated_idx] @ weights)   # shape: (num_movies,)
    # do not recommend already-rated
    scores[rated_idx] = -np.inf

    # top-k
    top_idx = np.argpartition(scores, -k)[-k:]
    top_idx = top_idx[np.argsort(scores[top_idx])[::-1]]
    recs = [(int(movie_ids[i]), float(scores[i])) for i in top_idx if np.isfinite(scores[i])]
    return recs[:k]

def recommend_titles_for_user(user_id: int, k: int = 10):
    recs = recommend_for_user(user_id, k)
    titles = get_movie_titles([mid for mid, _ in recs])
    return [(titles[mid], score) for mid, score in recs]
