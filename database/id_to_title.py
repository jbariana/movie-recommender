from typing import Optional
from database.connection import get_db
from database.paramstyle import PH
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
        with get_db(readonly=True) as conn:
            cur = conn.cursor()
            cur.execute(
                f"SELECT title, year FROM movies WHERE movie_id = {PH} LIMIT 1",
                (mid,),
            )
            row = cur.fetchone()
        if not row:
            return None

        # row can be tuple or Row-like
        try:
            title, year = row[0], row[1]
        except Exception:
            title = row["title"]
            year = row["year"]

        title = normalize_title(title) if title else title
        return f"{title} ({year})" if (title and year) else title
    except Exception:
        return None