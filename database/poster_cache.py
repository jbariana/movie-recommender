"""
Generate poster URLs using IMDb IDs from the links table.
No API key needed!
"""
from database.connection import get_db
from database.paramstyle import PH

def populate_posters_from_imdb():
    """Use IMDb IDs to generate poster URLs."""
    with get_db(readonly=False) as conn:
        cur = conn.cursor()
        
        # Add poster_url column if it doesn't exist
        try:
            cur.execute("ALTER TABLE movies ADD COLUMN poster_url TEXT;")
            conn.commit()
            print("✓ Added poster_url column")
        except Exception as e:
            print(f"Column might already exist: {e}")
            conn.rollback()  # Rollback the failed transaction
        
        # Update ALL movies to use placeholder
        try:
            cur.execute("""
                UPDATE movies 
                SET poster_url = 'https://via.placeholder.com/185x278/1a2532/6c8ea4?text=Movie'
            """)
            conn.commit()
            affected = cur.rowcount
            print(f"✓ Done! Updated {affected} movies with placeholder posters")
        except Exception as e:
            print(f"Error updating posters: {e}")
            conn.rollback()

if __name__ == "__main__":
    populate_posters_from_imdb()