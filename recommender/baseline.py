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
    ui = load_user_item_matrix()
    if user_id not in ui.index:
        return []
    sim, movie_ids = fit_item_item()
    num_movies = sim.shape[0]
    if num_movies == 0:
        return []
    k = min(k, num_movies)

    user_ratings = ui.loc[user_id]
    rated = user_ratings.dropna()
    if rated.empty:
        return []

    id_to_idx = {mid: i for i, mid in enumerate(movie_ids)}
    rated_idx = np.array([id_to_idx[m] for m in rated.index if m in id_to_idx], dtype=int)
    if rated_idx.size == 0:
        return []

    weights = rated.values[: rated_idx.size]
    scores = (sim[:, rated_idx] @ weights)

    # mask already-rated
    for ri in rated_idx:
        scores[ri] = -np.inf

    top_idx = np.argpartition(scores, -k)[-k:]
    top_idx = top_idx[np.argsort(scores[top_idx])[::-1]]
    recs = [(int(movie_ids[i]), float(scores[i])) for i in top_idx if np.isfinite(scores[i])]
    return recs[:k]

def recommend_titles_for_user(user_id: int, k: int = 10):
    recs = recommend_for_user(user_id, k)
    titles = get_movie_titles([mid for mid, _ in recs])
    return [(titles[mid], score) for mid, score in recs]
