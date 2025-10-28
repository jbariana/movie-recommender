from flask import Blueprint, request, jsonify, session
from pathlib import Path
import json
import logging
import importlib

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
        from database.connection import get_db
        from database.paramstyle import PH
        from database.db_query import get_ratings_for_user
        
        with get_db(readonly=False) as conn:
            cur = conn.cursor()
            cur.execute(
                f"INSERT INTO users (username) VALUES ({PH}) "
                f"ON CONFLICT (username) DO UPDATE SET username = EXCLUDED.username "
                f"RETURNING user_id;", (username,)
            )
            uid = int(cur.fetchone()[0])

        # load their ratings (list of dicts)
        ratings = get_ratings_for_user(uid)
        # persist a tiny local profile (optional helper)
        profile_json = {"username": username, "user_id": uid, "ratings": ratings}
        PROFILE_PATH.write_text(json.dumps(profile_json, indent=2), encoding="utf-8")
    except Exception as ex:
        logger.exception("Login failed")
        return jsonify({"error": f"database error: {ex}"}), 500

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
            sync_user_ratings(PROFILE_PATH)
    except Exception:
        logger.exception("sync failed on logout")

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
