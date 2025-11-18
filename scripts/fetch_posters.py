"""
fetch_posters.py
Fetch movie poster URLs from TMDb API and store in database
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv

# ✅ Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database.connection import get_db

load_dotenv()

# ✅ FIX: Get the API key by variable name, not by value
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"  # w500 = 500px wide posters

if not TMDB_API_KEY:
    print("❌ Error: TMDB_API_KEY not found in .env file")
    print("Get your free API key from: https://www.themoviedb.org/settings/api")
    exit(1)


def search_tmdb(title: str, year: int = None):
    """Search TMDb for a movie and return poster path"""
    try:
        params = {
            "api_key": TMDB_API_KEY,
            "query": title,
            "include_adult": "false",
        }
        
        if year:
            params["year"] = year
        
        response = requests.get(
            f"{TMDB_BASE_URL}/search/movie",
            params=params,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                poster_path = data["results"][0].get("poster_path")
                if poster_path:
                    return f"{TMDB_IMAGE_BASE}{poster_path}"
        
        return None
    except Exception as e:
        print(f"❌ Error searching TMDb: {e}")
        return None


def fetch_and_store_posters(limit: int = None, skip_existing: bool = True):
    """
    Fetch poster URLs for movies and store in database
    
    Args:
        limit: Max number of movies to process (None = all)
        skip_existing: Skip movies that already have poster URLs (real TMDb URLs only)
    """
    with get_db(readonly=False) as conn:
        cur = conn.cursor()
        
        # ✅ FIXED: Better query to find movies without REAL poster URLs
        if skip_existing:
            query = """
                SELECT movie_id, title, year 
                FROM movies 
                WHERE poster_url IS NULL 
                   OR poster_url = '' 
                   OR poster_url = 'N/A'
                   OR NOT poster_url LIKE 'https://image.tmdb.org%'
                ORDER BY movie_id
            """
        else:
            query = "SELECT movie_id, title, year FROM movies ORDER BY movie_id"
        
        if limit:
            query += f" LIMIT {limit}"
        
        cur.execute(query)
        movies = cur.fetchall()
        
        total = len(movies)
        print(f"📊 Found {total} movies to process")
        
        if total == 0:
            print("ℹ️  All movies already have posters!")
            print("   Use --all flag to re-fetch all posters")
            return
        
        success_count = 0
        fail_count = 0
        
        for idx, (movie_id, title, year) in enumerate(movies, 1):
            # Remove year from title if present (e.g., "Movie (1999)" -> "Movie")
            clean_title = title
            if title and "(" in title and ")" in title:
                clean_title = title[:title.rfind("(")].strip()
            
            print(f"[{idx}/{total}] Searching: {clean_title} ({year or 'N/A'})", end=" ... ")
            
            poster_url = search_tmdb(clean_title, year)
            
            if poster_url:
                # Update database
                from database.paramstyle import PH
                cur.execute(
                    f"UPDATE movies SET poster_url = {PH} WHERE movie_id = {PH}",
                    (poster_url, movie_id)
                )
                conn.commit()  # ✅ Commit after each update
                print(f"✅ Found")
                success_count += 1
            else:
                print("❌ Not found")
                fail_count += 1
            
            # Rate limiting: TMDb allows 40 requests per 10 seconds
            if idx % 40 == 0:
                print("⏳ Rate limit pause (10s)...")
                time.sleep(10)
            else:
                time.sleep(0.25)  # Small delay between requests
        
        print(f"\n📊 Complete: {success_count} found, {fail_count} not found")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch movie posters from TMDb")
    parser.add_argument("--limit", type=int, help="Max number of movies to process")
    parser.add_argument("--all", action="store_true", help="Re-fetch all posters (including existing)")
    
    args = parser.parse_args()
    
    # ✅ Show what we're doing
    if args.all:
        print("🔄 Re-fetching ALL movie posters...")
    else:
        print("🔍 Fetching posters for movies without TMDb poster URLs...")
    
    fetch_and_store_posters(
        limit=args.limit,
        skip_existing=not args.all
    )


if __name__ == "__main__":
    main()
