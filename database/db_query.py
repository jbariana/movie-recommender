from typing import List, Dict, Tuple, Optional
from database.connection import get_db
from database.paramstyle import PH  # e.g., "%s" for Postgres, "?" for SQLite
from .id_to_title import id_to_title

def get_ratings_for_user(user_id: int) -> List[Dict]:
    """Return recent ratings for a user with movie titles."""
    with get_db(readonly=True) as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT r.movie_id, m.title, m.year, r.rating, r.timestamp
            FROM ratings r
            LEFT JOIN movies m ON r.movie_id = m.movie_id
            WHERE r.user_id = {PH}
            ORDER BY r.timestamp DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()

    results: List[Dict] = []
    for movie_id, title_db, year, rating, ts in rows:
        # prefer your in-memory map, fallback to "Title (Year)" if present
        title = id_to_title(movie_id) or (f"{title_db} ({year})" if title_db and year else title_db)
        results.append(
            {
                "movie_id": int(movie_id),
                "title": title if title is not None else None,
                "rating": float(rating),
                "timestamp": int(ts),
            }
        )
    return results


def search_movies_by_keyword(keyword: str, limit: int = 20) -> List[Dict]:
    """
    Case-insensitive substring search on title.
    Uses LOWER(title) LIKE {PH} to work on both Postgres and SQLite.
    """
    q = f"%{keyword.strip().lower()}%"
    with get_db(readonly=True) as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT movie_id, title, year, genres
            FROM movies
            WHERE LOWER(title) LIKE {PH}
            ORDER BY title ASC
            LIMIT {PH}
            """,
            (q, limit),
        )
        rows = cur.fetchall()

    results: List[Dict] = []
    for movie_id, title, year, genres in rows:
        results.append(
            {
                "movie_id": int(movie_id),
                "title": title,
                "year": int(year) if year is not None else None,
                "genres": genres,
            }
        )
    return results


# Optional helpers 

def upsert_rating(user_id: int, movie_id: int, rating: float) -> None:
    """
    Keep one row per (user, movie): delete previous then insert fresh with current epoch.
    Portable: generate timestamp in Python, avoid DB-specific functions.
    """
    import time
    ts = int(time.time())
    with get_db(readonly=False) as conn:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM ratings WHERE user_id = {PH} AND movie_id = {PH};", (user_id, movie_id))
        cur.execute(
            f"""
            INSERT INTO ratings (user_id, movie_id, rating, timestamp)
            VALUES ({PH}, {PH}, {PH}, {PH})
            """,
            (user_id, movie_id, rating, ts),
        )
        
def top_unseen_for_user(user_id: int, limit: int = 20, min_votes: int = 50, m_param: int = 50) -> List[Dict]:
    """
    Recommend popular, well-rated movies the user hasn't rated yet.
    Uses Bayesian average: WR = (v/(v+m))*R + (m/(v+m))*C
      - R = movie's mean rating
      - v = movie's rating count
      - C = global mean rating
      - m = m_param (weight of prior), default 50
    Excludes movies already rated by `user_id`.
    """
    with get_db(readonly=True) as conn:
        cur = conn.cursor()
        # Order of params: user_id, m_param, m_param, m_param, min_votes, limit
        cur.execute(
            f"""
            WITH stats AS (
                SELECT movie_id, AVG(rating) AS R, COUNT(*) AS v
                FROM ratings
                GROUP BY movie_id
            ),
            global_mean AS (
                SELECT AVG(rating) AS C FROM ratings
            ),
            seen AS (
                SELECT movie_id FROM ratings WHERE user_id = {PH}
            )
            SELECT
                s.movie_id,
                m.title,
                m.year,
                s.v::INTEGER AS votes,
                ROUND(s.R::numeric, 3) AS avg_rating,
                ROUND(((s.v::numeric / (s.v + {PH})) * s.R
                    + ({PH}::numeric / (s.v + {PH})) * g.C)::numeric, 3) AS weighted_rating
            FROM stats s
            CROSS JOIN global_mean g
            JOIN movies m ON m.movie_id = s.movie_id
            LEFT JOIN seen se ON se.movie_id = s.movie_id
            WHERE se.movie_id IS NULL
              AND s.v >= {PH}
            ORDER BY weighted_rating DESC, s.v DESC
            LIMIT {PH};
            """,
            (user_id, m_param, m_param, m_param, min_votes, limit),
        )
        rows = cur.fetchall()

    return [
        {
            "movie_id": int(mid),
            "title": title,
            "year": int(year) if year is not None else None,
            "votes": int(votes),
            "avg_rating": float(avg),
            "weighted_rating": float(wr),
        }
        for (mid, title, year, votes, avg, wr) in rows
    ]