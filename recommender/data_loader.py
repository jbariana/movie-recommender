"""
data_loader.py
Convenience functions to read from SQLite for training/evaluation.

Examples:
    from recommender.data_loader import load_ratings_df, iter_user_ratings

    df = load_ratings_df()
    for user_id, movie_id, rating in iter_user_ratings(user_ids=[1,2,3]):
        ...
"""

from __future__ import annotations
import sqlite3
from typing import Generator, Iterable, Tuple
import pandas as pd
from pathlib import Path

# Reuse the same DB helper
from database.connection import get_db

def load_movies_df(columns: list[str] | None = None) -> pd.DataFrame:
    cols = columns or ["movie_id", "title", "year", "genres"]
    q = f"SELECT {', '.join(cols)} FROM movies"
    with get_db(readonly=True) as conn:
        return pd.read_sql_query(q, conn)

def load_ratings_df(min_ratings_per_user: int | None = None) -> pd.DataFrame:
    """
    Returns a DataFrame with columns: user_id, movie_id, rating, timestamp.
    Optionally filters to users with at least `min_ratings_per_user` ratings.
    """
    with get_db(readonly=True) as conn:
        if min_ratings_per_user is None:
            return pd.read_sql_query("SELECT * FROM ratings", conn)
        q = """
            WITH cnt AS (
              SELECT user_id, COUNT(*) AS n FROM ratings GROUP BY user_id
            )
            SELECT r.*
            FROM ratings r
            JOIN cnt ON cnt.user_id = r.user_id
            WHERE cnt.n >= ?
        """
        return pd.read_sql_query(q, conn, params=(min_ratings_per_user,))

def load_user_item_matrix() -> pd.DataFrame:
    """
    Returns a pivoted user-item matrix (users as rows, movies as columns).
    Useful for baseline/item-item recommenders.
    """
    df = load_ratings_df()
    return df.pivot_table(index="user_id", columns="movie_id", values="rating")

def iter_user_ratings(user_ids: Iterable[int] | None = None) -> Generator[Tuple[int,int,float,int], None, None]:
    """
    Yields (user_id, movie_id, rating, timestamp) one row at a time.
    Use for streaming/online algorithms without loading everything into memory.
    """
    with get_db(readonly=True) as conn:
        cur = conn.cursor()
        if user_ids:
            q = f"SELECT user_id, movie_id, rating, timestamp FROM ratings WHERE user_id IN ({','.join('?'*len(list(user_ids)))}) ORDER BY user_id"
            cur.execute(q, list(user_ids))
        else:
            cur.execute("SELECT user_id, movie_id, rating, timestamp FROM ratings ORDER BY user_id")
        for row in cur:
            yield int(row[0]), int(row[1]), float(row[2]), int(row[3])

def get_movie_titles(movie_ids: Iterable[int]) -> dict[int, str]:
    """
    Returns {movie_id: title} for a list of IDs — handy for pretty outputs.
    """
    ids = list(movie_ids)
    if not ids:
        return {}
    placeholders = ",".join("?" * len(ids))
    q = f"SELECT movie_id, title FROM movies WHERE movie_id IN ({placeholders})"
    with get_db(readonly=True) as conn:
        rows = conn.execute(q, ids).fetchall()
    return {int(mid): title for (mid, title) in rows}
