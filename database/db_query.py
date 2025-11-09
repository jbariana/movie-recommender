"""
db_query.py
database query helpers for user ratings, movie search, and recommendations
"""

from typing import List, Dict, Tuple, Optional
from database.connection import get_db
from database.paramstyle import PH
from .id_to_title import id_to_title


# -----------------------------
# Ratings for a user (with movie meta)
# -----------------------------
def get_ratings_for_user(user_id: int) -> List[Dict]:
    """
    Return this user's ratings joined with movie info.
    """
    with get_db(readonly=True) as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT r.movie_id, m.title, m.year, r.rating, r.timestamp, m.poster_url
            FROM ratings r
            LEFT JOIN movies m ON r.movie_id = m.movie_id
            WHERE r.user_id = {PH}
            ORDER BY r.timestamp DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()

    results: List[Dict] = []
    for movie_id, title_db, year, rating, ts, poster_url in rows:
        # Prefer in-memory title map; fallback to DB
        title = id_to_title(movie_id) or (f"{title_db} ({year})" if title_db and year else title_db)
        results.append(
            {
                "movie_id": int(movie_id),
                "title": title if title is not None else None,
                "rating": float(rating),
                "timestamp": int(ts),
                "poster_url": poster_url,
            }
        )
    return results


# -----------------------------
# Title keyword search
# -----------------------------
def search_movies_by_keyword(keyword: str, limit: int = 20) -> List[Dict]:
    """
    Case-insensitive LIKE search on title.
    """
    q = f"%{keyword.strip().lower()}%"

    with get_db(readonly=True) as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT movie_id, title, year, genres, poster_url
            FROM movies
            WHERE LOWER(title) LIKE {PH}
            ORDER BY title ASC
            LIMIT {PH}
            """,
            (q, limit),
        )
        rows = cur.fetchall()

    results: List[Dict] = []
    for movie_id, title, year, genres, poster_url in rows:
        results.append(
            {
                "movie_id": int(movie_id),
                "title": title,
                "year": int(year) if year is not None else None,
                "genres": genres,
                "poster_url": poster_url,
            }
        )
    return results


# -----------------------------
# Insert/replace a rating
# -----------------------------
def upsert_rating(user_id: int, movie_id: int, rating: float) -> None:
    """
    Keep a single row per (user, movie). Insert with current timestamp.
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


# -----------------------------
# Popular unseen (Bayesian weighted)
# -----------------------------
def top_unseen_for_user(user_id: int, limit: int = 20, min_votes: int = 50, m_param: int = 50) -> List[Dict]:
    """
    Recommend highly rated movies a user hasn't rated yet using
    a Bayesian weighted rating:
      WR = (v/(v+m))*R + (m/(v+m))*C
    """
    with get_db(readonly=True) as conn:
        cur = conn.cursor()
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


# ======================================================================
# Browse helpers (genres + pageable/sortable movie list)
# ======================================================================

def get_all_genres() -> List[str]:
    """
    Parse distinct tokens from movies.genres (pipe-separated).
    """
    genres_set = set()
    with get_db(readonly=True) as conn:
        cur = conn.cursor()
        cur.execute("SELECT genres FROM movies WHERE genres IS NOT NULL AND genres <> ''")
        for (g,) in cur.fetchall():
            if not g:
                continue
            for tok in str(g).split("|"):
                tok = tok.strip()
                if tok and tok.lower() != "(no genres listed)":
                    genres_set.add(tok)
    return sorted(genres_set)


def list_movies(
    genre: Optional[str],
    sort: str = "title",       # title|year|rating
    direction: str = "asc",    # asc|desc
    page: int = 1,
    page_size: int = 20,
) -> Dict:
    """
    Return a page of movies filtered by genre (token match),
    sorted by title/year/avg rating, including pagination metadata.
    """
    sort_map = {"title": "m.title", "year": "m.year", "rating": "avg_rating"}
    sort_col = sort_map.get(sort, "m.title")
    direction_sql = "DESC" if str(direction).lower() == "desc" else "ASC"

    page = max(int(page), 1)
    page_size = max(min(int(page_size), 100), 1)
    offset = (page - 1) * page_size

    genre_filter_sql = ""
    params: Tuple = tuple()
    if genre:
        # exact token match inside a pipe-separated field
        genre_filter_sql = "WHERE ('|' || COALESCE(m.genres,'') || '|') LIKE " + PH
        params += (f"%|{genre}|%",)

    with get_db(readonly=True) as conn:
        cur = conn.cursor()

        # total for pager
        cur.execute(f"SELECT COUNT(*) FROM movies m {genre_filter_sql};", params)
        total = int(cur.fetchone()[0])

        # main page (include avg rating)
        cur.execute(
            f"""
            WITH rating_stats AS (
              SELECT movie_id, AVG(rating) AS avg_rating
              FROM ratings
              GROUP BY movie_id
            )
            SELECT
              m.movie_id, m.title, m.year, m.genres,
              COALESCE(rs.avg_rating, 0) AS avg_rating
            FROM movies m
            LEFT JOIN rating_stats rs ON rs.movie_id = m.movie_id
            {genre_filter_sql}
            ORDER BY {sort_col} {direction_sql}, m.movie_id ASC
            LIMIT {page_size} OFFSET {offset};
            """,
            params,
        )
        rows = cur.fetchall()

    items = [
        {
            "movie_id": int(mid),
            "title": title,
            "year": int(year) if year is not None else None,
            "genres": genres,
            "avg_rating": float(avg) if avg is not None else 0.0,
        }
        for (mid, title, year, genres, avg) in rows
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": (offset + len(items)) < total,
        "has_prev": page > 1,
    }

# --- User rating stats ---
def get_user_rating_stats(user_id: int) -> dict:
    """
    Returns:
      {
        "total": int,                # number of ratings by this user
        "avg": float | None,         # average rating (None if no ratings)
        "by_genre": list[{"genre": str, "count": int, "avg": float}]
      }
    """
    from database.connection import get_db
    from database.paramstyle import PH

    with get_db(readonly=True) as conn:
        cur = conn.cursor()
        # total + avg
        cur.execute(
            f"SELECT COUNT(*), AVG(rating) FROM ratings WHERE user_id = {PH};",
            (user_id,),
        )
        total, avg = cur.fetchone()

        # per-genre breakdown (optional, nice to show)
        cur.execute(
            f"""
            WITH ur AS (
              SELECT r.movie_id, r.rating
              FROM ratings r
              WHERE r.user_id = {PH}
            )
            SELECT g.genre, COUNT(*), AVG(ur.rating)
            FROM ur
            JOIN movies m ON m.movie_id = ur.movie_id
            CROSS JOIN LATERAL (
              SELECT TRIM(value) AS genre
              FROM json_each_text( ('["' || REPLACE(COALESCE(m.genres,''),'|','","') || '"]') )
            ) g
            GROUP BY g.genre
            ORDER BY COUNT(*) DESC, g.genre ASC;
            """,
            (user_id,),
        )
        by_genre = [
            {"genre": g, "count": int(c or 0), "avg": float(a) if a is not None else None}
            for g, c, a in cur.fetchall()
        ]

    return {
        "total": int(total or 0),
        "avg": float(avg) if avg is not None else None,
        "by_genre": by_genre,
    }
