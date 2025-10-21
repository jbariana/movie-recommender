from flask import Blueprint, request, jsonify, session
from pathlib import Path
import json
import logging

api_bp = Blueprint("api_bp", __name__)
logger = logging.getLogger(__name__)

PROFILE_PATH = Path(__file__).resolve().parent.parent / "user_profile" / "user_profile.json"
PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)


@api_bp.route("/login", methods=["POST"])
def login():
    payload = request.get_json() or {}
    username = payload.get("username")
    if not username:
        return jsonify({"error": "username required"}), 400

    # persist username in session
    session["username"] = username

    # Ensure user exists in DB and obtain numeric user_id when possible
    uid = None
    try:
        from database.connection import get_db
        conn = get_db(readonly=False)
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if row:
            # sqlite3.Row supports dict-style access
            try:
                uid = int(row["user_id"])
            except Exception:
                uid = int(row[0])
        else:
            cur.execute("INSERT INTO users (username) VALUES (?)", (username,))
            conn.commit()
            uid = int(cur.lastrowid)
        conn.close()
    except Exception as ex:
        logger.warning(f"User lookup/creation failed: {ex}")
        # fallback: if username is numeric, use it; otherwise leave uid None
        try:
            uid = int(username)
        except Exception:
            uid = None

    # Load ratings from DB for this user (if we have numeric uid)
    ratings = []
    if isinstance(uid, int):
        try:
            from database.db_query import get_ratings_for_user
            db_rows = get_ratings_for_user(uid)
            # get_ratings_for_user already returns normalized dicts
            ratings = db_rows
        except Exception as ex:
            logger.info(f"No DB ratings loaded for user {uid}: {ex}")

    # Persist profile JSON with both username and numeric user_id (when available)
    profile_json = {"username": username, "user_id": uid if uid is not None else username, "ratings": ratings}
    try:
        PROFILE_PATH.write_text(json.dumps(profile_json, indent=2), encoding="utf-8")
    except Exception:
        logger.exception("Failed to write profile JSON on login")

    return jsonify({"message": "logged in", "username": username, "user_id": uid}), 200


@api_bp.route("/session", methods=["GET"])
def session_info():
    return jsonify({"username": session.get("username")}), 200


@api_bp.route("/logout", methods=["POST"])
def logout():
    # On logout, attempt to sync current profile JSON to DB (best-effort)
    try:
        from api.sync_user_json import sync_user_ratings
        if PROFILE_PATH.exists():
            ok = sync_user_ratings(PROFILE_PATH)
            if not ok:
                logger.warning("sync_user_ratings returned False on logout")
    except Exception:
        logger.exception("sync_user_ratings failed on logout")

    # clear session
    session.pop("username", None)
    return jsonify({"message": "logged out"}), 200


@api_bp.route("/api/button-click", methods=["POST"])
def button_click():
    payload = request.get_json() or {}
    button_id = payload.get("button")
    logger.info("Button clicked: %s payload: %s", button_id, payload)
    try:
        # import the api module robustly (avoid import-from-package edge cases)
        import importlib
        api_module = importlib.import_module("api.api")
        result = api_module.handle_button_click(button_id, payload)
        logger.info("button_click result: %s", {"button": button_id, "result_keys": list(result.keys()) if isinstance(result, dict) else type(result)})
        return jsonify(result)
    except Exception as ex:
        logger.exception("Error in handle_button_click")
        return jsonify({"error": str(ex)}), 500
