from __future__ import annotations
import re
from pathlib import Path
import os
import pandas as pd
from sqlalchemy import create_engine, text
from database.connection import get_db

# Speed up bulk inserts
TO_SQL_KW = dict(chunksize=10_000, method="multi")

YEAR_RE = re.compile(r"\((\d{4})\)$")
IS_PG = bool(os.getenv("DATABASE_URL", "").strip())

def parse_year(title: str) -> int | None:
    if not isinstance(title, str):
        return None
    m = YEAR_RE.search(title.strip())
    return int(m.group(1)) if m else None

def _engine():
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return create_engine(url, future=True)
    from database.connection import DB_PATH
    return create_engine(f"sqlite:///{DB_PATH}", future=True)

def clear_tables(keep_users: bool = False) -> None:
    """
    Clears data in FK-safe order.
    - Postgres + keep_users=True: TRUNCATE child tables and reset identities, don't touch users.
    - Otherwise: DELETE in FK-safe order. If keep_users=True, skip users.
    """
    with get_db(readonly=False) as conn:
        cur = conn.cursor()
        if IS_PG and keep_users:
            # Fast + resets sequences; relies on FKs to cascade where needed.
            cur.execute("TRUNCATE ratings, tags, links, movies RESTART IDENTITY CASCADE;")
        else:
            # SQLite (no TRUNCATE) or full clean seed (also wipe users)
            order = ["ratings", "tags", "links", "movies"]
            if not keep_users:
                order.append("users")
            for table in order:
                cur.execute(f"DELETE FROM {table};")
                
def load_movies(path: Path, eng) -> None:
    df = pd.read_csv(path / "movies.csv")
    df["year"] = df["title"].apply(parse_year)
    df["title"] = df["title"].apply(lambda t: re.sub(r"\s*\(\d{4}\)\s*$", "", t) if isinstance(t, str) else t)
    df.rename(columns={"movieId": "movie_id"}, inplace=True)
    df = df[["movie_id", "title", "year", "genres"]]
    df.to_sql("movies", eng, if_exists="append", index=False, **TO_SQL_KW)

def load_users_from_ratings(path: Path, eng) -> None:
    # Build users from distinct userId in ratings.csv
    df = pd.read_csv(path / "ratings.csv", usecols=["userId"])
    users = df["userId"].drop_duplicates().astype(int)

    # Provide usernames to satisfy NOT NULL + UNIQUE
    users_df = pd.DataFrame({
        "user_id": users,
        "username": users.map(lambda x: f"user_{x}")
    })

    # Speed up bulk insert
    TO_SQL_KW = {"chunksize": 10_000, "method": "multi"}

    users_df.to_sql("users", eng, if_exists="append", index=False, **TO_SQL_KW)

    # Reset the SERIAL/identity sequence so future inserts don't collide
    if IS_PG:
        with eng.begin() as conn:
            conn.execute(text("""
                SELECT setval(
                  pg_get_serial_sequence('users','user_id'),
                  COALESCE((SELECT MAX(user_id) FROM users), 1),
                  true
                )
            """))

def load_ratings(path: Path, eng) -> None:
    df = pd.read_csv(path / "ratings.csv")
    df.rename(columns={"movieId": "movie_id", "userId": "user_id"}, inplace=True)
    df.to_sql("ratings", eng, if_exists="append", index=False, **TO_SQL_KW)

def load_tags(path: Path, eng) -> None:
    tags_csv = path / "tags.csv"
    if not tags_csv.exists():
        return
    df = pd.read_csv(tags_csv)
    df.rename(columns={"movieId": "movie_id", "userId": "user_id"}, inplace=True)
    df.to_sql("tags", eng, if_exists="append", index=False, **TO_SQL_KW)

def load_links(path: Path, eng) -> None:
    df = pd.read_csv(path / "links.csv")
    df.rename(columns={"movieId": "movie_id", "imdbId": "imdb_id", "tmdbId": "tmdb_id"}, inplace=True)
    df.to_sql("links", eng, if_exists="append", index=False, **TO_SQL_KW)
    
def main(data_path, keep_users: bool = False) -> None:
    src = Path(data_path)
    if not (src / "movies.csv").exists():
        raise FileNotFoundError(f"Could not find movies.csv under {src}. Did you unzip the dataset?")

    eng = _engine()

    # Clear old data with the chosen strategy
    clear_tables(keep_users=keep_users)

    # Load in FK-safe order
    load_movies(src, eng)
    if not keep_users:
        # Only rebuild users from ratings when doing a clean seed
        load_users_from_ratings(src, eng)
    load_ratings(src, eng)
    load_tags(src, eng)
    load_links(src, eng)
    print("✅ Loaded MovieLens.")