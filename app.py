from flask import Flask, render_template, request, jsonify, session
from pathlib import Path
import logging
import traceback
import random
from datetime import timedelta
import json

from database.connection import get_db
from database.paramstyle import PH, IS_PG
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
    try:
        from api.init_and_sync import init_database_and_sync
        profile_path = Path(__file__).parent / "user_profile" / "user_profile.json"
        init_database_and_sync(
            data_path="data/ml-latest-small",
            profile_path=profile_path
        )
        logger.info("Database initialized/loaded successfully.")
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
        with get_db(readonly=True) as conn:
            cur = conn.cursor()
            cur.execute("SELECT movie_id, title FROM movies")
            return cur.fetchall()
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


PROFILE_PATH = Path(__file__).resolve().parent / "user_profile" / "user_profile.json"
PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)

@app.route("/local-login", methods=["POST"])
def local_login():
    payload = request.get_json() or {}
    username = payload.get("username")
    if not username:
        return jsonify({"error": "username required"}), 400

    # remember in session
    session["username"] = username

    # --- DB: get-or-create user in ONE query (works on Postgres; also OK on SQLite if username is UNIQUE)
    try:
        with get_db(readonly=False) as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                INSERT INTO users (username)
                VALUES ({PH})
                ON CONFLICT (username) DO UPDATE SET username = EXCLUDED.username
                RETURNING user_id;
                """,
                (username,)
            )
            uid = int(cur.fetchone()[0])

            # fetch this user's ratings
            cur.execute(
                f"SELECT movie_id, rating, timestamp FROM ratings WHERE user_id = {PH}",
                (uid,)
            )
            rows = cur.fetchall()
            ratings = [{"movie_id": int(m), "rating": float(r), "timestamp": int(ts)} for (m, r, ts) in rows]
    except Exception:
        logger.exception("local-login DB upsert/lookup failed")
        return jsonify({"error": "database error during login"}), 500

    # --- persist a local profile JSON (optional/helper)
    profile = {"username": username, "user_id": uid, "ratings": ratings}
    try:
        PROFILE_PATH.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    except Exception as ex:
        logger.exception("Failed to write local profile JSON")
        return jsonify({"error": f"persist failed: {ex}"}), 500

    # --- optional sync after login
    try:
        from api.sync_user_json import sync_user_ratings
        ok = sync_user_ratings(PROFILE_PATH)
        if not ok:
            logger.warning("sync_user_ratings returned False after local-login")
    except Exception:
        logger.exception("sync_user_ratings failed after local-login")

    return jsonify({"message": "logged in (local)", "username": username, "user_id": uid}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)
