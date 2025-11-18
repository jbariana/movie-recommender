"""
Quick script to check if posters are actually in the database
"""

import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database.connection import get_db

with get_db(readonly=True) as conn:
    cur = conn.cursor()
    
    # Check total movies
    cur.execute("SELECT COUNT(*) FROM movies")
    total = cur.fetchone()[0]
    
    # Check how many have poster URLs
    cur.execute("SELECT COUNT(*) FROM movies WHERE poster_url IS NOT NULL AND poster_url != '' AND poster_url LIKE 'https://image.tmdb.org%'")
    with_posters = cur.fetchone()[0]
    
    # Show some examples
    cur.execute("SELECT movie_id, title, poster_url FROM movies WHERE poster_url LIKE 'https://image.tmdb.org%' LIMIT 5")
    examples = cur.fetchall()
    
    print(f"📊 Total movies: {total}")
    print(f"🖼️  Movies with TMDb posters: {with_posters}")
    print(f"📈 Percentage: {(with_posters/total)*100:.1f}%")
    print(f"\n✅ Sample movies with posters:")
    for mid, title, url in examples:
        print(f"  • {title} (ID {mid})")
        print(f"    {url}")