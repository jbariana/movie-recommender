from flask import Flask, render_template, request, jsonify, session
from pathlib import Path
import logging
import sqlite3
import traceback
import random
from datetime import timedelta

app = Flask(
    __name__,
    template_folder="ui/web/templates",
    static_folder="ui/web/static",
)

# Enable Flask sessions
app.secret_key = "supersecretkey"
app.permanent_session_lifetime = timedelta(hours=2)

@app.before_request
def make_session_permanent():
    session.permanent = True

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prefer the same DB file used by database.connection
try:
    from database.connection import DB_PATH as DB_CONN_PATH
except Exception:
    DB_CONN_PATH = Path("data/ml-latest-small/movies.db")


# Helper function to initialize database if needed
def init():
    if DB_CONN_PATH.exists():
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


init()

# Import and register API blueprint after init()
from api.routes import api_bp
app.register_blueprint(api_bp)


# ------------------- Random movie helpers -------------------
def get_all_movies():
    try:
        conn = sqlite3.connect(DB_CONN_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM movies")  # Assuming 'movies' table exists
        movies = cursor.fetchall()
        conn.close()
        return movies
    except Exception as e:
        logger.error(f"Error fetching movies: {e}")
        return []


def randomize_movie():
    movies = get_all_movies()
    if not movies:
        return "No movies available."
    movie_id, movie_title = random.choice(movies)
    return f"Movie ID: {movie_id}, Title: {movie_title}"


# ------------------- Flask routes -------------------
@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/random_movie", methods=["GET"])
def random_movie_route():
    movie = randomize_movie()
    return jsonify({"random_movie": movie})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)
