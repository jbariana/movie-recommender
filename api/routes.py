"""
routes.py
flask API routes for authentication, session management, and user interactions

handles:
- user login/logout and session persistence
- profile synchronization between JSON and database
- button-click action dispatcher for UI interactions
"""

from flask import Blueprint, request, jsonify, session
from pathlib import Path
import json
import logging
import importlib

#create flask blueprint for organizing API routes
api_bp = Blueprint("api_bp", __name__)
logger = logging.getLogger(__name__)

#path to user profile JSON file (stores ratings locally for quick access)
PROFILE_PATH = Path(__file__).resolve().parent.parent / "user_profile" / "user_profile.json"
PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)



#authentication and session stuff
@api_bp.route("/login", methods=["POST"])
def login():
    """
    Handle user login - creates/retrieves user account and loads their ratings.
    
    
    Extract username from request body
    Store username in Flask session (server-side state)
    Insert/update user in database (upsert operation)
    Load user's existing ratings from database
    Save profile JSON locally for quick access
    
    Request Body:
        {
            "username": "alice"
        }
    
    Returns:
        200: {"message": "logged in", "username": "alice", "user_id": 123}
        400: {"error": "username required"}
        500: {"error": "database error: ..."}
    """
    #parse JSON request body
    payload = request.get_json() or {}
    username = payload.get("username")
    
    #validate username is provided
    if not username:
        return jsonify({"error": "username required"}), 400

    #store username in Flask session
    session["username"] = username

    try:
        #import database utilities
        from database.connection import get_db
        from database.paramstyle import PH  # Placeholder for SQL parameters (? or %s)
        from database.db_query import get_ratings_for_user
        
        #insert new user or get existing users ID
        with get_db(readonly=False) as conn:
            cur = conn.cursor()
            # ON CONFLICT DO UPDATE ensures we get the user_id even if user exists
            cur.execute(
                f"INSERT INTO users (username) VALUES ({PH}) "
                f"ON CONFLICT (username) DO UPDATE SET username = EXCLUDED.username "
                f"RETURNING user_id;", (username,)
            )
            uid = int(cur.fetchone()[0])

        #load user's ratings from database (returns list of rating dicts)
        ratings = get_ratings_for_user(uid)
        
        #create profile JSON structure
        profile_json = {"username": username, "user_id": uid, "ratings": ratings}
        
        #save profile to local JSON file for quick access by other modules
        PROFILE_PATH.write_text(json.dumps(profile_json, indent=2), encoding="utf-8")
        
    except Exception as ex:
        #log full traceback and return error to client
        logger.exception("Login failed")
        return jsonify({"error": f"database error: {ex}"}), 500

    return jsonify({"message": "logged in", "username": username, "user_id": uid}), 200

#check current session status - returns logged in username if any.
@api_bp.route("/session", methods=["GET"])
def session_info():
    """
    determine if user is logged in on page load
    
    Returns:
        200: {"username": "alice"} if logged in
        200: {"username": null} if not logged in
    """
    return jsonify({"username": session.get("username")}), 200

#handle user logout - syncs profile to database and clears session
@api_bp.route("/logout", methods=["POST"])
def logout():
    """
    sync any pending changes from JSON profile to database
    clear username from flask session
    return success message
    
    sync errors logged but don't prevent logout
    
    Returns:
        200: {"message": "logged out"}
    """
    #sync local profile JSON to database before logout
    try:
        from api.sync_user_json import sync_user_ratings
        if PROFILE_PATH.exists():
            #update database
            sync_user_ratings(PROFILE_PATH)
    except Exception:
        #log error but continue with logout (don't block user)
        logger.exception("sync failed on logout")

    #remove username from session
    session.pop("username", None)
    return jsonify({"message": "logged out"}), 200


#routes button clicks to appropriate handlers in api.py module

#UI Action Dispatcher
@api_bp.route("/api/button-click", methods=["POST"])
def button_click():
    """
    Supports:
    view_ratings_button: show user's rated movies
    view_statistics_button: display rating statistics
    get_rec_button: generate movie recommendations
    add_rating_submit: add a movie rating
    remove_rating_button: remove a rating
    search: search for movies
    
    Request Body:
        {
            "button": "get_rec_button",
            "query": "inception",     // optional, for search
            "movie_id": 123,           // optional, for add/remove
            "rating": 4.5              // optional, for add
        }
    
    Returns:
        200: Result from handler (format varies by action)
        500: {"error": "..."}
    """
    #parse request payload
    payload = request.get_json() or {}
    button_id = payload.get("button")
    
    #log incoming request for debugging
    logger.info("Button clicked: %s payload: %s", button_id, payload)
    
    try:
        #import api module
        api_module = importlib.import_module("api.api")
        
        #call main handler function with button ID and full payload
        result = api_module.handle_button_click(button_id, payload)
        
        #log response structure for debugging (not full data to avoid spam)
        logger.info(
            "button_click result: %s",
            {"button": button_id, "result_keys": list(result.keys()) if isinstance(result, dict) else type(result)}
        )
        
        return jsonify(result)
        
    except Exception as ex:
        #log full error traceback and return error to client
        logger.exception("Error in handle_button_click")
        return jsonify({"error": str(ex)}), 500
