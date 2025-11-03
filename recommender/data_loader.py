"""
data_loader.py
Loads rating and movie data from the database into pandas DataFrames.
Provides utility functions for the recommendation engine.
"""

from __future__ import annotations
from typing import Generator, Iterable, Tuple
import pandas as pd
from database.connection import get_db, DATABASE_URL, DB_PATH
from database.paramstyle import PH, ph_list
from sqlalchemy import create_engine

def _get_sqlalchemy_url():
    """
    Convert DATABASE_URL or SQLite path to SQLAlchemy-compatible URL.
    """
    if DATABASE_URL:
        # PostgreSQL URL from environment
        return DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    else:
        # SQLite local database
        return f"sqlite:///{DB_PATH}"

def _sa_engine_for_loader():
    """Create and return a SQLAlchemy engine for pandas operations."""
    return create_engine(_get_sqlalchemy_url())

def load_movies_df(columns: list[str] | None = None) -> pd.DataFrame:
    """Load movies with specified columns using SQLAlchemy engine."""
    cols = columns or ["movie_id", "title", "year", "genres"]
    q = f"SELECT {', '.join(cols)} FROM movies"
    engine = _sa_engine_for_loader()
    try:
        return pd.read_sql_query(q, engine)
    finally:
        engine.dispose()

def load_ratings_df(min_ratings_per_user: int | None = None) -> pd.DataFrame:
    """
    Returns a DataFrame with columns: user_id, movie_id, rating, timestamp.
    Optionally filters to users with at least `min_ratings_per_user` ratings.
    Uses SQLAlchemy engine to avoid pandas warnings.
    """
    engine = _sa_engine_for_loader()
    try:
        if min_ratings_per_user is None:
            return pd.read_sql_query("SELECT * FROM ratings", engine)
        
        # Use parameterized query for filtering
        q = """
            WITH cnt AS (
              SELECT user_id, COUNT(*) AS n FROM ratings GROUP BY user_id
            )
            SELECT r.*
            FROM ratings r
            JOIN cnt ON cnt.user_id = r.user_id
            WHERE cnt.n >= ?
        """
        return pd.read_sql_query(q, engine, params=(min_ratings_per_user,))
    finally:
        engine.dispose()

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
            ids = list(user_ids)
            q = f"""
                SELECT user_id, movie_id, rating, timestamp
                FROM ratings
                WHERE user_id IN ({ph_list(len(ids))})
                ORDER BY user_id
            """
            cur.execute(q, ids)
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
    placeholders = ph_list(len(ids))
    q = f"SELECT movie_id, title FROM movies WHERE movie_id IN ({placeholders})"
    with get_db(readonly=True) as conn:
        cur = conn.cursor()
        cur.execute(q, ids)
        rows = cur.fetchall()
    return {int(mid): title for (mid, title) in rows}

def load_ratings_data():
    """Load ratings data using SQLAlchemy engine for pandas compatibility."""
    engine = _sa_engine_for_loader()
    try:
        return pd.read_sql_query("SELECT * FROM ratings", engine)
    finally:
        engine.dispose()

def load_movies_data():
    """Load movies data using SQLAlchemy engine for pandas compatibility."""
    engine = _sa_engine_for_loader()
    try:
        return pd.read_sql_query("SELECT * FROM movies", engine)
    finally:
        engine.dispose()
