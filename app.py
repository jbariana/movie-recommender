from flask import Flask, render_template, request, jsonify, session
from pathlib import Path
from api.routes import api_bp
import logging
import sqlite3
import traceback
import random

app = Flask(
    __name__,
    template_folder="ui/web/templates",
    static_folder="ui/web/static",
)
app.register_blueprint(api_bp)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = Path("data/ml-latest-small/movies.db")

# Helper function to initialize what needs to be initialized (currently just the DB)
def init():
    if DB_PATH.exists():
        logger.info("Database already exists, skipping initialization.")
        return

    try:
        from api.init_and_sync import init_database_and_sync
        profile_path = Path(__file__).parent / "user_profile" / "user_profile.json"
        init_database_and_sync(
            data_path="data/ml-latest-small",
            profile_path=profile_path
        )
        logger.info("Database initialized successfully.")
    except Exception:
        logger.error("Database initialization failed:")
        traceback.print_exc()

# Function to get all movies from the database
def get_all_movies():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM movies")  # Assuming 'movies' table exists
        movies = cursor.fetchall()
        conn.close()
        return movies
    except Exception as e:
        logger.error(f"Error fetching movies: {e}")
        return []

# Function to randomize movie
def randomize_movie():
    movies = get_all_movies()
    
    if not movies:
        return "No movies available."

    # Randomly select a movie
    movie_id, movie_title = random.choice(movies)
    return f"Movie ID: {movie_id}, Title: {movie_title}"

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/random_movie", methods=["GET"])
def random_movie():
    movie = randomize_movie()
    return jsonify({"random_movie": movie})

if __name__ == "__main__":
    init()
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)
