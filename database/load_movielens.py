from __future__ import annotations
import re
from pathlib import Path
import os
import pandas as pd
from sqlalchemy import create_engine, text
from database.connection import get_db

#speed up bulk inserts with chunking and multi-row statements
TO_SQL_KW = dict(chunksize=10_000, method="multi")

#regex to extract year from titles like "Movie Title (1999)"
YEAR_RE = re.compile(r"\((\d{4})\)$")
IS_PG = bool(os.getenv("DATABASE_URL", "").strip())

#extract year from movie title string
def parse_year(title: str) -> int | None:
    if not isinstance(title, str):
        return None
    #search for (YYYY) pattern at end of title
    m = YEAR_RE.search(title.strip())
    return int(m.group(1)) if m else None

#create sqlalchemy engine for postgres or sqlite
def _engine():
    #use postgres if DATABASE_URL is set
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return create_engine(url, future=True)
    #fallback to sqlite
    from database.connection import DB_PATH
    return create_engine(f"sqlite:///{DB_PATH}", future=True)

#clear existing data from tables in FK-safe order
def clear_tables(keep_users: bool = False) -> None:
    """
    clears data in FK-safe order.
    - postgres + keep_users=True: TRUNCATE child tables and reset identities, don't touch users.
    - otherwise: DELETE in FK-safe order. if keep_users=True, skip users.
    """
    with get_db(readonly=False) as conn:
        cur = conn.cursor()
        #postgres supports TRUNCATE with CASCADE for fast cleanup
        if IS_PG and keep_users:
            #fast + resets sequences; relies on FKs to cascade where needed
            cur.execute("TRUNCATE ratings, tags, links, movies RESTART IDENTITY CASCADE;")
        else:
            #sqlite (no TRUNCATE) or full clean seed (also wipe users)
            #delete in FK-safe order: children first, then parents
            order = ["ratings", "tags", "links", "movies"]
            if not keep_users:
                order.append("users")
            for table in order:
                cur.execute(f"DELETE FROM {table};")

#load movies.csv into movies table
def load_movies(path: Path, eng) -> None:
    df = pd.read_csv(path / "movies.csv")
    df["year"] = df["title"].apply(parse_year)
    df["title"] = df["title"].apply(lambda t: re.sub(r"\s*\(\d{4}\)\s*$", "", t) if isinstance(t, str) else t)
    df.rename(columns={"movieId": "movie_id"}, inplace=True)
    df = df[["movie_id", "title", "year", "genres"]]

    df.to_sql(
        "movies",
        eng,
        if_exists="append",
        index=False,
        **TO_SQL_KW   # ← use ONLY this
    )

#build users table from distinct user_ids in ratings.csv
def load_users_from_ratings(path: Path, eng) -> None:
    #read only userId column from ratings CSV
    df = pd.read_csv(path / "ratings.csv", usecols=["userId"])
    #get unique user IDs
    users = df["userId"].drop_duplicates().astype(int)

    #create users dataframe with generated usernames
    users_df = pd.DataFrame({
        "user_id": users,
        "username": users.map(lambda x: f"user_{x}")  #satisfy NOT NULL + UNIQUE constraints
    })

    #bulk insert users into database
    TO_SQL_KW = {"chunksize": 10_000, "method": "multi"}
    users_df.to_sql("users", eng, if_exists="append", index=False, **TO_SQL_KW)

    #reset postgres sequence to prevent future ID collisions
    if IS_PG:
        with eng.begin() as conn:
            conn.execute(text("""
                SELECT setval(
                  pg_get_serial_sequence('users','user_id'),
                  COALESCE((SELECT MAX(user_id) FROM users), 1),
                  true
                )
            """))

#load ratings.csv into ratings table
def load_ratings(path: Path, eng) -> None:
    #read ratings CSV file
    df = pd.read_csv(path / "ratings.csv")
    #rename columns to match database schema
    df.rename(columns={"movieId": "movie_id", "userId": "user_id"}, inplace=True)
    #bulk insert into database
    df.to_sql("ratings", eng, if_exists="append", index=False, **TO_SQL_KW)

#load tags.csv into tags table if file exists
def load_tags(path: Path, eng) -> None:
    tags_csv = path / "tags.csv"
    #tags.csv is optional in some datasets
    if not tags_csv.exists():
        return
    #read tags CSV file
    df = pd.read_csv(tags_csv)
    #rename columns to match database schema
    df.rename(columns={"movieId": "movie_id", "userId": "user_id"}, inplace=True)
    #bulk insert into database
    df.to_sql("tags", eng, if_exists="append", index=False, **TO_SQL_KW)

#load links.csv into links table (contains IMDb and TMDb IDs)
def load_links(path: Path, eng) -> None:
    #read links CSV file
    df = pd.read_csv(path / "links.csv")
    #rename columns to match database schema
    df.rename(columns={"movieId": "movie_id", "imdbId": "imdb_id", "tmdbId": "tmdb_id"}, inplace=True)
    #bulk insert into database
    df.to_sql("links", eng, if_exists="append", index=False, **TO_SQL_KW)

#main entry point to load all MovieLens CSV files into database
def main(data_path, keep_users: bool = False) -> None:
    src = Path(data_path)
    #validate dataset directory exists
    if not (src / "movies.csv").exists():
        raise FileNotFoundError(f"Could not find movies.csv under {src}. Did you unzip the dataset?")

    #create database engine
    eng = _engine()

    #clear old data with the chosen strategy
    clear_tables(keep_users=keep_users)

    #load CSV files in FK-safe order (parents before children)
    load_movies(src, eng)
    if not keep_users:
        #only rebuild users from ratings when doing a clean seed
        load_users_from_ratings(src, eng)
    load_ratings(src, eng)
    load_tags(src, eng)
    load_links(src, eng)
    print("Loaded MovieLens")
