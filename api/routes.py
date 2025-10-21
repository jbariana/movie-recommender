from flask import Blueprint, request, jsonify, session
from api import api
from pathlib import Path
import json
import logging

# create a Flask Blueprint instance
api_bp = Blueprint("api_bp", __name__)

logger = logging.getLogger(__name__)

@api_bp.route("/login", methods=["POST"])
def login():
    """
    Handles user login by saving their username in the Flask session and
    persisting the selected user id into user_profile.json, then attempting a sync.
    """

    # Parse the JSON data sent in the request body
    data = request.get_json() or {}
    username = data.get("username")

    # no username is provided, return a 400 (Bad Request) error
    if not username:
        return jsonify({"error": "Username is required"}), 400

    # Save the username in Flask's session object (allows it to persist w/ cookies)
    session["username"] = username

    profile_path = Path(__file__).resolve().parent.parent / "user_profile" / "user_profile.json"
    profile_path.parent.mkdir(parents=True, exist_ok=True)

    uid = None
    # Try to find/create username in DB and obtain numeric user_id
    try:
        from database.connection import get_db
        conn = get_db(readonly=False)
        cur = conn.cursor()
        # try exact match by username
        cur.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if row:
            uid = int(row[0])
        else:
            # create new user row and get autoincrement id
            cur.execute("INSERT INTO users (username) VALUES (?)", (username,))
            conn.commit()
            uid = int(cur.lastrowid)
        conn.close()
    except Exception as ex:
        logger.warning(f"User lookup/creation in DB failed: {ex}")
        # fallback: if username is numeric, use it; otherwise leave no numeric id
        try:
            uid = int(username)
        except Exception:
            uid = None

    # load ratings from DB if we have a numeric uid
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

    # persist profile JSON with both username and numeric user_id (when available)
    profile_json = {"username": username, "user_id": uid if uid is not None else username, "ratings": ratings}
    profile_path.write_text(json.dumps(profile_json, indent=2), encoding="utf-8")

    # best-effort: trigger sync hook (only works if numeric uid is present)
    try:
        from api.sync_user_json import sync_user_ratings
        sync_user_ratings(profile_path)
    except Exception as ex_sync:
        logger.warning(f"Profile sync after login failed: {ex_sync}")

    # Return a success message as JSON with status code 200 (OK)
    return jsonify({"message": f"Logged in as {username}", "loaded_ratings": len(ratings), "user_id": uid}), 200


@api_bp.route("/logout", methods=["POST"])
def logout():
    """
    Handles user logout by removing their username from the session.
    """

    # Remove the 'username' key from the session (if it exists)
    session.pop("username", None)

    # Return confirmation as JSON
    return jsonify({"message": "Logged out"}), 200


@api_bp.route("/session", methods=["GET"])
def get_session():
    """
    Returns information about the current session (if a user is logged in).
    """

    # retrieve the username from the session
    username = session.get("username")

    # respond with the username
    return jsonify({"username": username}), 200



@api_bp.route("/api/button-click", methods=["POST"])
def button_click():
    """
    Handles a button click event sent from the client.
    """

    #extract JSON payload from the request body
    payload = request.get_json() or {}

    #retrieve which button was clicked
    button_id = payload.get("button")

    #print to server console for debugging
    print(f"Button clicked: {button_id}")

    #check if a user is logged in
    username = session.get("username")
    if not username:
        # Return structured JSON so frontend can show a friendly message
        return jsonify({"error": "not_logged_in", "message": "Please log in to use this action."}), 401

    #if a user is logged in, attach their username to the payload so backend logic knows which user triggered the event
    payload["username"] = username  

    #call handler function 
    try:
        result = api.handle_button_click(button_id, payload)
        return jsonify(result)
    except Exception as ex:
        logger.exception("Error in handle_button_click")
        return jsonify({"error": "server_error", "message": str(ex)}), 500
