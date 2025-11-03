"""
db_query.py
database query helpers for user ratings, movie search, and recommendations
"""

from typing import List, Dict, Tuple, Optional
from database.connection import get_db
from database.paramstyle import PH
from .id_to_title import id_to_title


#get all ratings for a specific user with movie metadata
def get_ratings_for_user(user_id: int) -> List[Dict]:
    #query database for user's ratings joined with movie details
    with get_db(readonly=True) as conn:
        cur = conn.cursor()
        #join ratings with movies table to get full metadata
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

    #build list of rating dicts with resolved titles
    results: List[Dict] = []
    #process each rating row into structured dict
    for movie_id, title_db, year, rating, ts, poster_url in rows:
        #prefer in-memory title map, fallback to database title
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


#search movies by keyword in title
def search_movies_by_keyword(keyword: str, limit: int = 20) -> List[Dict]:
    #convert keyword to lowercase with wildcards for LIKE query
    q = f"%{keyword.strip().lower()}%"
    
    #query database for matching movies
    with get_db(readonly=True) as conn:
        cur = conn.cursor()
        #use LOWER() for case-insensitive search on both postgres and sqlite
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

    #convert rows to list of dicts
    results: List[Dict] = []
    #process each movie result
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


#add or update a rating for a user/movie pair
def upsert_rating(user_id: int, movie_id: int, rating: float) -> None:
    import time
    ts = int(time.time())
    
    #delete old rating and insert new one to maintain single row per user/movie
    with get_db(readonly=False) as conn:
        cur = conn.cursor()
        #delete existing rating for this user/movie pair
        cur.execute(f"DELETE FROM ratings WHERE user_id = {PH} AND movie_id = {PH};", (user_id, movie_id))
        #insert new rating with current timestamp
        cur.execute(
            f"""
            INSERT INTO ratings (user_id, movie_id, rating, timestamp)
            VALUES ({PH}, {PH}, {PH}, {PH})
            """,
            (user_id, movie_id, rating, ts),
        )

        
#recommend popular movies user hasn't seen using bayesian weighted ratings
def top_unseen_for_user(user_id: int, limit: int = 20, min_votes: int = 50, m_param: int = 50) -> List[Dict]:
    #query for highly-rated movies the user hasn't rated yet
    with get_db(readonly=True) as conn:
        cur = conn.cursor()
        #bayesian weighted rating formula:
        #WR = (v/(v+m))*R + (m/(v+m))*C
        #where R=movie avg, v=vote count, C=global avg, m=prior weight
        #this prevents movies with 1 five-star rating from ranking above movies with 100 four-star ratings
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

    #convert query results to list of movie dicts
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