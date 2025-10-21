from typing import List, Dict
from .connection import get_db
from .id_to_title import id_to_title

def get_ratings_for_user(user_id: int) -> List[Dict]:
    conn = get_db(readonly=True)
    try:
        cur = conn.execute(
            """
            SELECT r.movie_id, m.title, m.year, r.rating, r.timestamp
            FROM ratings r
            LEFT JOIN movies m ON r.movie_id = m.movie_id
            WHERE r.user_id = ?
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        results = []
        for row in rows:
            movie_id, title_db, year, rating, ts = row
            title = id_to_title(movie_id) or (f"{title_db} ({year})" if title_db and year else title_db)
            results.append(
                {
                    "movie_id": movie_id,
                    "title": title if title is not None else None,
                    "rating": rating,
                    "timestamp": ts,
                }
            )
        return results
    finally:
        conn.close()


def search_movies_by_keyword(keyword: str, limit: int = 20):
    from database.connection import get_db
    db = get_db(readonly=True)
    cur = db.cursor()
    q = f"%{keyword.strip()}%"
    cur.execute(
        """
        SELECT movie_id, title, year, genres
        FROM movies
        WHERE LOWER(title) LIKE LOWER(?)
        ORDER BY title ASC
        LIMIT ?
        """,
        (q, limit),
    )
    rows = cur.fetchall()
    # rows are sqlite3.Row or tuples
    results = []
    for r in rows:
        try:
            mid = int(r["movie_id"]) if "movie_id" in r.keys() else int(r[0])
            title = r["title"] if "title" in r.keys() else r[1]
            year = r["year"] if "year" in r.keys() else r[2]
            genres = r["genres"] if "genres" in r.keys() else (r[3] if len(r) > 3 else None)
        except Exception:
            # fallback tuple unpack
            mid, title, year, *rest = r
            genres = rest[0] if rest else None
        results.append({"movie_id": mid, "title": title, "year": year, "genres": genres})
    db.close()
    return results
