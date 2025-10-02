from typing import Optional
from database.connection import get_db

def id_to_title(movie_id: int) -> Optional[str]:
    if movie_id is None:
        return None
    try:
        mid = int(movie_id)
    except Exception:
        return None

    try:
        with get_db(readonly=True) as conn:
            cur = conn.execute("SELECT title, year FROM movies WHERE movie_id = ? LIMIT 1", (mid,))
            row = cur.fetchone()
            if not row:
                return None
            title, year = row
            if year is None:
                return title
            return f"{title} ({year})"
    except Exception:
        return None