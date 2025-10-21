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


def search_movies_by_keyword(keyword):
    from database.connection import get_db
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT title, year, rating
        FROM movies
        WHERE title LIKE ?
        LIMIT 20
    """, (f"%{keyword}%",))
    rows = cursor.fetchall()
    return [{"title": r[0], "year": r[1], "rating": r[2]} for r in rows]
