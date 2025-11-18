"""
routes.py
flask API routes for authentication, session management, and user interactions

handles:
- user signup/login/logout (hashed password via Werkzeug)
- legacy JSON /login disabled
- profile sync and button-click dispatcher
"""

from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from pathlib import Path
import json
import logging
import importlib
from werkzeug.security import generate_password_hash, check_password_hash

# DB helpers for users (you already have this module)
from database.users import get_user_by_username, create_user, set_password  # noqa: F401

# create flask blueprint
api_bp = Blueprint("api_bp", __name__)
logger = logging.getLogger(__name__)

# path to user profile JSON
PROFILE_PATH = Path(__file__).resolve().parent.parent / "user_profile" / "user_profile.json"
PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)


# ------------------------------
# Legacy JSON login: DISABLED
# ------------------------------
@api_bp.route("/login", methods=["POST"])
def login():
    """
    Legacy username-only login is disabled.
    Use /auth/login (form) with password hashing.
    """
    return jsonify({"error": "This endpoint is disabled. Use /auth/login."}), 410


# ------------------------------
# Session info (used by your JS)
# ------------------------------
@api_bp.route("/session", methods=["GET"])
def session_info():
    """Return logged-in username if any."""
    return jsonify({"username": session.get("username")}), 200


# ------------------------------
# JSON logout that also syncs profile
# (kept for your existing JS buttons)
# ------------------------------
@api_bp.route("/logout", methods=["POST"])
def logout():
    """
    Sync local profile JSON to database then clear session.
    """
    try:
        from api.sync_user_json import sync_user_ratings
        if PROFILE_PATH.exists():
            sync_user_ratings(PROFILE_PATH)
    except Exception:
        logger.exception("sync failed on logout")

    session.pop("username", None)
    return jsonify({"message": "logged out"}), 200


# ------------------------------
# New AUTH PAGES (hashed)
# ------------------------------
@api_bp.route("/auth/signup", methods=["GET", "POST"])
def auth_signup():
    """signup page and handler"""
    if request.method == "GET":
        return render_template("signup.html")

    #handle form submission (not JSON)
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not username or not password:
        flash("username and password required", "error")
        return redirect(url_for("api_bp.auth_signup"))

    #check if user already exists
    existing = get_user_by_username(username)
    if existing:
        flash("username already taken", "error")
        return redirect(url_for("api_bp.auth_signup"))

    #create user with hashed password
    from werkzeug.security import generate_password_hash
    pw_hash = generate_password_hash(password)
    
    try:
        user_id = create_user(username, pw_hash)
        
        #IMPORTANT: log them in by setting session
        session["username"] = username
        session.permanent = True
        
        #sync to user_profile.json
        from database.db_query import get_ratings_for_user
        ratings = get_ratings_for_user(user_id)
        profile_json = {"username": username, "user_id": user_id, "ratings": ratings}
        PROFILE_PATH.write_text(json.dumps(profile_json, indent=2), encoding="utf-8")
        
        flash("account created successfully!", "success")
        
        #redirect to home page (user is now logged in)
        return redirect(url_for("index"))
        
    except Exception as ex:
        logger.exception("signup failed")
        flash(f"error creating account: {ex}", "error")
        return redirect(url_for("api_bp.auth_signup"))


@api_bp.route("/auth/login", methods=["GET", "POST"])
def auth_login():
    """login page and handler"""
    if request.method == "GET":
        return render_template("login.html")

    #handle both form data (from HTML form) and JSON (from JS fetch)
    if request.is_json:
        payload = request.get_json()
        username = payload.get("username", "").strip()
        password = payload.get("password", "").strip()
    else:
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

    if not username or not password:
        if request.is_json:
            return jsonify({"error": "username and password required"}), 400
        flash("username and password required", "error")
        return redirect(url_for("api_bp.auth_login"))

    #get user from database
    user = get_user_by_username(username)
    if not user:
        if request.is_json:
            return jsonify({"error": "invalid credentials"}), 401
        flash("invalid username or password", "error")
        return redirect(url_for("api_bp.auth_login"))

    user_id, stored_username, stored_hash = user
    
    #check password
    from werkzeug.security import check_password_hash
    if not check_password_hash(stored_hash, password):
        if request.is_json:
            return jsonify({"error": "invalid credentials"}), 401
        flash("invalid username or password", "error")
        return redirect(url_for("api_bp.auth_login"))

    #login successful
    session["username"] = stored_username
    session.permanent = True

    #sync to user_profile.json
    from database.db_query import get_ratings_for_user
    ratings = get_ratings_for_user(user_id)
    profile_json = {"username": stored_username, "user_id": user_id, "ratings": ratings}
    PROFILE_PATH.write_text(json.dumps(profile_json, indent=2), encoding="utf-8")

    if request.is_json:
        return jsonify({"message": "logged in", "username": stored_username}), 200
    
    flash("logged in successfully!", "success")
    return redirect(url_for("index"))


@api_bp.route("/auth/logout", methods=["POST"])
def auth_logout():
    session.pop("username", None)
    flash("Logged out.", "success")
    return redirect(url_for("index"))


# ------------------------------
# UI Action Dispatcher (your app)
# ------------------------------
@api_bp.route("/api/button-click", methods=["POST"])
def button_click():
    """
    Dispatch front-end button actions to api.api.handle_button_click
    """
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

# ---------- BROWSE API: genres ----------
@api_bp.get("/api/genres")
def api_genres():
    """
    Return a sorted list of distinct genres parsed from movies.genres
    """
    from database.db_query import get_all_genres
    return jsonify({"genres": get_all_genres()}), 200


# ---------- BROWSE API: movies (filter/sort/paginate) ----------
@api_bp.get("/api/movies")
def api_movies():
    """
    Query params:
      genre: optional string; match token inside movies.genres (pipe-separated)
      sort:  title|year|rating  (default=title)
      dir:   asc|desc           (default=asc)
      page:  1-based page number (default=1)
      page_size: per-page items  (default=20)
    """
    from database.db_query import list_movies

    genre = (request.args.get("genre") or "").strip()
    sort = (request.args.get("sort") or "title").lower()
    direction = (request.args.get("dir") or "asc").lower()
    page = max(int(request.args.get("page") or 1), 1)
    page_size = min(max(int(request.args.get("page_size") or 20), 1), 100)

    data = list_movies(
        genre=genre or None,
        sort=sort,
        direction=direction,
        page=page,
        page_size=page_size,
    )
    return jsonify(data), 200

@api_bp.get("/api/ping")
def api_ping():
    return "ok", 200


@api_bp.get("/api/stats")
def api_stats():
    """
    Stats for the logged-in user.
    Robust user_id extraction regardless of tuple/dict Row shape.
    """
    from database.db_query import get_user_rating_stats

    uname = session.get("username")
    if not uname:
        return jsonify({"error": "not_logged_in"}), 401

    user_row = get_user_by_username(uname)
    if not user_row:
        return jsonify({"error": "user_not_found"}), 404

    # accept tuple/list/dict/Row
    user_id = None
    try:
        user_id = int(user_row[0])   # tuple-like (id, username, hash)
    except Exception:
        pass
    if user_id is None:
        try:
            for k in ("user_id", "id", "USER_ID", "ID"):
                if k in user_row:
                    user_id = int(user_row[k])
                    break
        except Exception:
            pass

    if user_id is None:
        return jsonify({"error": "could_not_resolve_user_id"}), 500

    stats = get_user_rating_stats(user_id)
    return jsonify(stats), 200

# ---------- RECS: content-based (genres + year) ----------
@api_bp.get("/api/recommendations/content")
def api_content_recs():
    """
    Content-based recommendations for the current user (or a provided user_id).
    Query params:
      user_id: optional int; if omitted, use the logged-in session user
      k:       optional int; default 20
    """
    from recommender.content import recommend_titles_for_user
    from database.users import get_user_by_username

    # resolve user_id
    user_id_param = request.args.get("user_id")
    k = int(request.args.get("k") or 20)

    if user_id_param:
        try:
            user_id = int(user_id_param)
        except ValueError:
            return jsonify({"error": "invalid_user_id"}), 400
    else:
        uname = session.get("username")
        if not uname:
            return jsonify({"error": "not_logged_in"}), 401
        user_row = get_user_by_username(uname)
        if not user_row:
            return jsonify({"error": "user_not_found"}), 404
        try:
            user_id = int(user_row[0])  # (id, username, hash)
        except Exception:
            # fallback dict-like
            for kname in ("user_id", "id", "USER_ID", "ID"):
                if kname in user_row:
                    user_id = int(user_row[kname])
                    break
            else:
                return jsonify({"error": "could_not_resolve_user_id"}), 500

    items = recommend_titles_for_user(user_id=user_id, k=k)
    return jsonify({"user_id": user_id, "items": items}), 200

@api_bp.route("/api/movies/search", methods=["GET"])
def search_movies():
    """
    Search movies by title (fuzzy matching)
    """
    query = request.args.get("q", "").strip()
    limit = int(request.args.get("limit", 20))
    
    if not query or len(query) < 2:
        return jsonify({
            "results": [],
            "count": 0,
            "query": query
        })
    
    from database.db_query import search_movies_by_title
    
    try:
        results = search_movies_by_title(query, limit=limit)
        return jsonify({
            "results": results,
            "count": len(results),
            "query": query
        })
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route("/api/movies/<int:movie_id>", methods=["GET"])
def get_movie_details(movie_id):
    """
    Get details for a specific movie by ID
    """
    from database.db_query import get_movie_by_id
    
    try:
        movie = get_movie_by_id(movie_id)
        if not movie:
            return jsonify({"error": "Movie not found"}), 404
        
        return jsonify(movie)
    except Exception as e:
        logger.error(f"Failed to get movie {movie_id}: {e}")
        return jsonify({"error": str(e)}), 500
