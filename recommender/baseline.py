from __future__ import annotations
import numpy as np
import pandas as pd
from typing import List, Dict

class BaselineRecommender:
    def __init__(self, min_ratings_per_item: int = 5):
        self.min_ratings_per_item = min_ratings_per_item
        self.item_popularity_: pd.Series | None = None
        self.item_index_: Dict[int, int] = {}
        self.index_item_: List[int] = []
        self.item_item_sim_: np.ndarray | None = None

    def fit(self, ratings: pd.DataFrame) -> "BaselineRecommender":
        counts = ratings.groupby("movieId")["rating"].count()
        self.item_popularity_ = counts[counts >= self.min_ratings_per_item].sort_values(ascending=False)

        self.index_item_ = list(self.item_popularity_.index)
        self.item_index_ = {mid: i for i, mid in enumerate(self.index_item_)}
        users = ratings["userId"].unique()
        user_index = {u: i for i, u in enumerate(users)}

        M = np.zeros((len(users), len(self.index_item_)), dtype=np.float32)
        for row in ratings.itertuples(index=False):
            if row.movieId in self.item_index_:
                M[user_index[row.userId], self.item_index_[row.movieId]] = row.rating

        col_norms = np.linalg.norm(M, axis=0) + 1e-8
        M_norm = M / col_norms
        self.item_item_sim_ = M_norm.T @ M_norm
        np.fill_diagonal(self.item_item_sim_, 0.0)
        return self

    def recommend_for_user(self, ratings: pd.DataFrame, user_id: int, k_sim: int = 30, top_n: int = 10) -> List[int]:
        assert self.item_item_sim_ is not None and self.item_popularity_ is not None, "Call fit() first."
        user_hist = ratings[ratings["userId"] == user_id]
        seen = set(user_hist["movieId"].tolist())
        scores = np.zeros(len(self.index_item_), dtype=np.float32)

        for row in user_hist.itertuples(index=False):
            if row.movieId in self.item_index_:
                j = self.item_index_[row.movieId]
                sims = self.item_item_sim_[j]
                if k_sim and k_sim < len(sims):
                    top_idx = np.argpartition(-sims, k_sim)[:k_sim]
                    scores[top_idx] += sims[top_idx] * row.rating
                else:
                    scores += sims * row.rating

        candidates = []
        for idx in np.argsort(-scores):
            mid = self.index_item_[idx]
            if mid not in seen and scores[idx] > 0:
                candidates.append(mid)
            if len(candidates) >= top_n:
                break

        if len(candidates) < top_n:
            for mid in self.item_popularity_.index:
                if mid not in seen and mid not in candidates:
                    candidates.append(mid)
                if len(candidates) >= top_n:
                    break
        return candidates[:top_n]
