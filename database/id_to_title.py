from typing import Optional
from database.connection import get_db
from database.paramstyle import PH
import re

#regex pattern to match titles with trailing articles like "Matrix, The"
_ARTICLE_RE = re.compile(r"^(?P<body>.+),\s*(?P<article>(The|A|An))$", flags=re.I)

#convert "Movie, The" format to "The Movie"
def normalize_title(title: Optional[str]) -> Optional[str]:
    if title is None:
        return None
    t = title.strip()
    #check if title has trailing article pattern
    m = _ARTICLE_RE.match(t)
    if m:
        #move article to front and capitalize it
        article = m.group("article").capitalize()
        body = m.group("body").strip()
        return f"{article} {body}"
    return t

#look up movie title from database by movie_id
def id_to_title(movie_id: int) -> Optional[str]:
    if movie_id is None:
        return None
    #validate movie_id is numeric
    try:
        mid = int(movie_id)
    except Exception:
        return None

    #query database for movie title and year
    try:
        with get_db(readonly=True) as conn:
            cur = conn.cursor()
            cur.execute(
                f"SELECT title, year FROM movies WHERE movie_id = {PH} LIMIT 1",
                (mid,),
            )
            row = cur.fetchone()
        
        #return None if movie not found
        if not row:
            return None

        #extract title and year (handle both tuple and dict-like rows)
        try:
            title, year = row[0], row[1]
        except Exception:
            title = row["title"]
            year = row["year"]

        #normalize title format and append year if available
        title = normalize_title(title) if title else title
        return f"{title} ({year})" if (title and year) else title
    except Exception:
        return None