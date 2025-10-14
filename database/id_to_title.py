from typing import Optional
from database.connection import get_db
import re

_ARTICLE_RE = re.compile(r"^(?P<body>.+),\s*(?P<article>(The|A|An))$", flags=re.I)

def _normalize_article(title: str) -> str:
    if not title:
        return title
    title = title.strip()
    m = _ARTICLE_RE.match(title)
    if m:
        article = m.group("article").capitalize()
        body = m.group("body").strip()
        return f"{article} {body}"
    return title

def normalize_title(title: Optional[str]) -> Optional[str]:
    if title is None:
        return None
    return _normalize_article(title)

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
            if title is None:
                return None
            title = _normalize_article(title)
            if year is None:
                return title
            return f"{title} ({year})"
    except Exception:
        return None