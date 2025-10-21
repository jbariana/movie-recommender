from flask import Blueprint, request, jsonify
from database.connection import get_db

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/search", methods=["GET"])
def search_movies():
    """
    Search movies by keyword and return basic info (title, year, rating)
    """
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
