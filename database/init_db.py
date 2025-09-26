"""
init_db.py
Creates the SQLite schema for the movie recommender.

Run:
    python -m database.init_db
"""

from __future__ import annotations
import sqlite3
from .connection import get_db

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS movies (
    movie_id     INTEGER PRIMARY KEY,
    title        TEXT NOT NULL,
    year         INTEGER,
    genres       TEXT
);

CREATE TABLE IF NOT EXISTS ratings (
    user_id      INTEGER NOT NULL,
    movie_id     INTEGER NOT NULL,
    rating       REAL    NOT NULL,
    timestamp    INTEGER NOT NULL,
    PRIMARY KEY (user_id, movie_id, timestamp),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id)
);

CREATE TABLE IF NOT EXISTS tags (
    user_id      INTEGER NOT NULL,
    movie_id     INTEGER NOT NULL,
    tag          TEXT    NOT NULL,
    timestamp    INTEGER NOT NULL,
    PRIMARY KEY (user_id, movie_id, tag, timestamp),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id)
);

CREATE TABLE IF NOT EXISTS links (
    movie_id     INTEGER PRIMARY KEY,
    imdb_id      INTEGER,
    tmdb_id      INTEGER,
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id)
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_ratings_user  ON ratings(user_id);
CREATE INDEX IF NOT EXISTS idx_ratings_movie ON ratings(movie_id);
CREATE INDEX IF NOT EXISTS idx_tags_movie    ON tags(movie_id);
"""

def main() -> None:
    with get_db(readonly=False) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    print("✅ Database schema created at database/movies.db")

if __name__ == "__main__":
    main()
