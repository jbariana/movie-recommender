from typing import Optional
from database.connection import get_db
import re

_ARTICLE_RE = re.compile(r"^(?P<body>.+),\s*(?P<article>(The|A|An))$", flags=re.I)

def normalize_title(title: Optional[str]) -> Optional[str]:
    if title is None:
        return None
    t = title.strip()
    m = _ARTICLE_RE.match(t)
    if m:
        article = m.group("article").capitalize()
        body = m.group("body").strip()
        return f"{article} {body}"
    return t

def id_to_title(movie_id: int) -> Optional[str]:
    if movie_id is None:
        return None
    try:
        mid = int(movie_id)
    except Exception:
        return None
    try:
        conn = get_db(readonly=True)
        cur = conn.execute("SELECT title, year FROM movies WHERE movie_id = ? LIMIT 1", (mid,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        title, year = row
        title = normalize_title(title) if title else title
        if year:
            return f"{title} ({year})"
        return title
    except Exception:
        return None