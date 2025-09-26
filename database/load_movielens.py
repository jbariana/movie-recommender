"""
load_movielens.py
Loads MovieLens (ml-latest-small) CSVs into SQLite.

Run:
    python -m database.load_movielens --data-path data/ml-latest-small
"""

from __future__ import annotations
import argparse
import re
from pathlib import Path
import pandas as pd
from .connection import get_db

YEAR_RE = re.compile(r"\((\d{4})\)$")

def parse_year(title: str) -> int | None:
    """
    Extracts a 4-digit year from the end of the title like 'Toy Story (1995)'.
    Returns None if not found.
    """
    if not isinstance(title, str):
        return None
    m = YEAR_RE.search(title.strip())
    return int(m.group(1)) if m else None

def load_movies(path: Path, conn) -> None:
    df = pd.read_csv(path / "movies.csv")
    # Split out year and clean title
    df["year"] = df["title"].apply(parse_year)
    df["title"] = df["title"].apply(lambda t: re.sub(r"\s*\(\d{4}\)\s*$", "", t) if isinstance(t, str) else t)
    df.rename(columns={"movieId": "movie_id"}, inplace=True)
    df = df[["movie_id", "title", "year", "genres"]]
    df.to_sql("movies", conn, if_exists="append", index=False)

def load_ratings(path: Path, conn) -> None:
    df = pd.read_csv(path / "ratings.csv")
    df.rename(columns={"movieId": "movie_id", "userId": "user_id"}, inplace=True)
    # For small data we can write all at once; chunk if you switch to larger datasets
    df.to_sql("ratings", conn, if_exists="append", index=False)

def load_tags(path: Path, conn) -> None:
    tags_csv = path / "tags.csv"
    if not tags_csv.exists():
        return
    df = pd.read_csv(tags_csv)
    df.rename(columns={"movieId": "movie_id", "userId": "user_id"}, inplace=True)
    df.to_sql("tags", conn, if_exists="append", index=False)

def load_links(path: Path, conn) -> None:
    df = pd.read_csv(path / "links.csv")
    df.rename(columns={"movieId": "movie_id", "imdbId": "imdb_id", "tmdbId": "tmdb_id"}, inplace=True)
    df.to_sql("links", conn, if_exists="append", index=False)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", type=str, required=True, help="Path to MovieLens folder, e.g., data/ml-latest-small")
    args = parser.parse_args()

    src = Path(args.data_path)
    if not (src / "movies.csv").exists():
        raise FileNotFoundError(f"Could not find movies.csv under {src}. Did you unzip the dataset?")

    with get_db(readonly=False) as conn:
        # Clear any old data (safe for repeated runs during dev)
        for table in ("ratings", "tags", "links", "movies"):
            conn.execute(f"DELETE FROM {table}")
        conn.commit()

        load_movies(src, conn)
        load_ratings(src, conn)
        load_tags(src, conn)
        load_links(src, conn)
        conn.commit()
    print("✅ Loaded MovieLens into SQLite.")

if __name__ == "__main__":
    main()
