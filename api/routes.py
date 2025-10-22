from flask import Blueprint, request, jsonify, session
from pathlib import Path
import json
import logging
import importlib

from database.connection import get_db
from database.paramstyle import PH  # gives "%s" on Postgres, "?" on SQLite
from database.db_query import (
    search_movies_by_keyword,
    get_ratings_for_user,
    upsert_rating,
)

from database.db_query import top_unseen_for_user

api_bp = Blueprint("api_bp", __name__)
logger = logging.getLogger(__name__)

PROFILE_PATH = Path(__file__).resolve().parent.parent / "user_profile" / "user_profile.json"
PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)


# ---------- Auth / Session ----------
@api_bp.route("/login", methods=["POST"])
def login():
    payload = request.get_json() or {}
    username = payload.get("username")
    if not username:
        return jsonify({"error": "username required"}), 400

    # keep in session
    session["username"] = username

    try:
        # One upsert + RETURNING to get the user_id (Postgres-safe, also OK on SQLite with UNIQUE)
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

        # load their ratings (list of dicts)
        ratings = get_ratings_for_user(uid)
    except Exception as ex:
        logger.exception("Login upsert/lookup failed")
        return jsonify({"error": f"database error: {ex}"}), 500

    # persist a tiny local profile (optional helper)
    try:
        profile_json = {"username": username, "user_id": uid, "ratings": ratings}
        PROFILE_PATH.write_text(json.dumps(profile_json, indent=2), encoding="utf-8")
    except Exception:
        logger.exception("Failed to write profile JSON on login")

    return jsonify({"message": "logged in", "username": username, "user_id": uid}), 200


@api_bp.route("/session", methods=["GET"])
def session_info():
    return jsonify({"username": session.get("username")}), 200


@api_bp.route("/logout", methods=["POST"])
def logout():
    # best-effort sync of local profile JSON to DB
    try:
        from api.sync_user_json import sync_user_ratings
        if PROFILE_PATH.exists():
            ok = sync_user_ratings(PROFILE_PATH)
            if not ok:
                logger.warning("sync_user_ratings returned False on logout")
    except Exception:
        logger.exception("sync_user_ratings failed on logout")

    session.pop("username", None)
    return jsonify({"message": "logged out"}), 200


# ---------- UI/Button callback ----------
@api_bp.route("/api/button-click", methods=["POST"])
def button_click():
    payload = request.get_json() or {}
    button_id = payload.get("button")
    logger.info("Button clicked: %s payload: %s", button_id, payload)
    try:
        api_module = importlib.import_module("api.api")
        result = api_module.handle_button_click(button_id, payload)
        logger.info(
            "button_click result: %s",
            {"button": button_id, "result_keys": list(result.keys()) if isinstance(result, dict) else type(result)}
        )
        return jsonify(result)
    except Exception as ex:
        logger.exception("Error in handle_button_click")
        return jsonify({"error": str(ex)}), 500


# ---------- Data APIs ----------
@api_bp.get("/api/search")
def api_search_movies():
    q = (request.args.get("q") or "").strip()
    try:
        limit = int(request.args.get("limit", 20))
    except ValueError:
        return jsonify({"error": "invalid limit"}), 400
    if not q:
        return jsonify({"error": "missing q"}), 400
    items = search_movies_by_keyword(q, limit)
    return jsonify({"items": items})


@api_bp.get("/api/ratings")
def api_get_ratings():
    try:
        user_id = int(request.args.get("user_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "missing/invalid user_id"}), 400
    items = get_ratings_for_user(user_id)
    return jsonify({"items": items})


@api_bp.post("/api/rate")
def api_rate_movie():
    data = request.get_json(force=True) or {}
    try:
        user_id = int(data["user_id"])
        movie_id = int(data["movie_id"])
        rating = float(data["rating"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "user_id, movie_id, rating required"}), 400

    if not (0.5 <= rating <= 5.0):
        return jsonify({"error": "rating out of range [0.5, 5.0]"}), 400

    try:
        upsert_rating(user_id, movie_id, rating)
        return jsonify({"ok": True, "user_id": user_id, "movie_id": movie_id, "rating": rating})
    except Exception as ex:
        logger.exception("rate failed")
        return jsonify({"error": f"database error: {ex}"}), 500
    

@api_bp.get("/api/recommendations")
def api_recommendations():
    # query params: user_id (required), limit, min_votes
    try:
        user_id = int(request.args.get("user_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "missing/invalid user_id"}), 400

    try:
        limit = int(request.args.get("limit", 20))
        min_votes = int(request.args.get("min_votes", 50))
    except ValueError:
        return jsonify({"error": "invalid numeric param"}), 400

    items = top_unseen_for_user(user_id=user_id, limit=limit, min_votes=min_votes, m_param=50)
    return jsonify({"items": items})