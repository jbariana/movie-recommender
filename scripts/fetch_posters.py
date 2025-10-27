import requests
from database.connection import get_db

OMDB_API_KEY = "YOUR_KEY_HERE"

def fetch_poster(title):
    url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
    data = requests.get(url).json()
    return data.get("Poster")

def store_posters():
    db = get_db()
    movies = db.execute("SELECT id, title FROM movies").fetchall()

    for movie_id, title in movies:
        poster_url = fetch_poster(title)
        if poster_url:
            db.execute("UPDATE movies SET poster_url = ? WHERE id = ?", (poster_url, movie_id))
            print(f"Saved poster for {title}")
    
    db.commit()

if __name__ == "__main__":
    store_posters()
