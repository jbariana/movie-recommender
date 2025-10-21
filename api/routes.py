from flask import Blueprint, request, jsonify, session
from pathlib import Path
import json
import logging
from database.connection import get_db
from api import api

# Create a Flask Blueprint instance
api_bp = Blueprint("api_bp", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

# ------------------- User session routes -------------------
@api_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    if not username:
        return jsonify({"error": "Username is required"}), 400

    session["username"] = username
    profile_path = Path(__file__).resolve().parent.parent / "user_profile" / "user_profile.json"
    profile_path.parent.mkdir(parents=True, exist_ok=True)

    uid = None
    try:
        conn = get_db(readonly=False)
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if row:
            uid = int(row[0])
        else:
            cur.execute("INSERT INTO users (username) VALUES (?)", (username,))
            conn.commit()
            uid = int(cur.lastrowid)
        conn.close()
    except Exception as ex:
        logger.warning(f"User lookup/creation in DB failed: {ex}")
        try:
            uid = int(username)
        except Exception:
            uid = None

    ratings = []
    if isinstance(uid, int):
        try:
            from database.db_query import get_ratings_for_user
            db_rows = get_ratings_for_user(uid)
            for r in db_rows:
                ratings.append({
                    "movie_id": r.get("movie_id"),
                    "rating": r.get("rating"),
                    "timestamp": r.get("timestamp"),
                })
        except Exception as ex:
            logger.info(f"No DB ratings loaded for user {uid}: {ex}")

    profile_json = {"username": username, "user_id": uid if uid is not None else username, "ratings": ratings}
    profile_path.write_text(json.dumps(profile_json, indent=2), encoding="utf-8")

    try:
        from api.sync_user_json import sync_user_ratings
        sync_user_ratings(profile_path)
    except Exception as ex_sync:
        logger.warning(f"Profile sync after login failed: {ex_sync}")

    return jsonify({"message": f"Logged in as {username}", "loaded_ratings": len(ratings), "user_id": uid}), 200

@api_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return jsonify({"message": "Logged out"}), 200

@api_bp.route("/session", methods=["GET"])
def get_session():
    username = session.get("username")
    return jsonify({"username": username}), 200

@api_bp.route("/button-click", methods=["POST"])
def button_click():
    payload = request.get_json() or {}
    button_id = payload.get("button")
    print(f"Button clicked: {button_id}")

    username = session.get("username")
    if not username:
        return jsonify({"error": "not_logged_in", "message": "Please log in to use this action."}), 401

    payload["username"] = username  
    try:
        result = api.handle_button_click(button_id, payload)
        return jsonify(result)
    except Exception as ex:
        logger.exception("Error in handle_button_click")
        return jsonify({"error": "server_error", "message": str(ex)}), 500

# ------------------- Movie search route -------------------
@api_bp.route("/search", methods=["GET"])
def search_movies():
    keyword = request.args.get("q", "").strip().lower()
    if not keyword:
        return jsonify({"error": "Missing search keyword"}), 400

    db = get_db()
    cursor = db.cursor()

    query = """
        SELECT title, year, rating
        FROM movies
        WHERE LOWER(title) LIKE ?
        ORDER BY rating DESC
        LIMIT 10;
    """
    cursor.execute(query, (f"%{keyword}%",))
    results = cursor.fetchall()

    movies = [
        {"title": row[0], "year": row[1], "rating": row[2]}
        for row in results
    ]

    return jsonify(movies)
