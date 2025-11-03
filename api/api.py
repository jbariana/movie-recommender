"""
api.py
Core API handler for all button-click actions.
"""

from pathlib import Path
import json
import time
import logging
from collections import Counter
from database.id_to_title import id_to_title, normalize_title

logger = logging.getLogger(__name__)

PROFILE_PATH = Path(__file__).resolve().parent.parent / "user_profile" / "user_profile.json"

#extract and return a human-friendly movie title from a rating entry.
def _resolve_title_from_entry(entry):
    """
    Handles various entry formats:
    - 'title' field (direct title string)
    - 'movie' field (could be title string or numeric ID)
    - 'movie_id' field (numeric ID that needs lookup)
    
    Args:
        entry (dict): A rating entry dict with various possible keys
        
    Returns:
        str: Normalized movie title or "ID {movie_id}" if title lookup fails
        None: If entry is empty or invalid
    """
    if not entry:
        return None

    # check for explicit 'title' field
    if entry.get("title"):
        return normalize_title(str(entry.get("title")))

    # check 'movie' field - could be either title string or numeric ID
    m = entry.get("movie")
    if m is not None:
        try:
            mid = int(m)
            t = id_to_title(mid) 
            return t if t else f"ID {mid}"  
        except Exception:
            return normalize_title(str(m))

    # check 'movie_id' field - always numeric
    mid = entry.get("movie_id")
    if mid is not None:
        try:
            mid_i = int(mid)
            t = id_to_title(mid_i)  # Look up title from database
            return t if t else f"ID {mid_i}"  # Fallback to ID if lookup fails
        except Exception:
            return normalize_title(str(mid))

    # no valid title/ID found
    return None

#central dispatcher for all button-click actions from the frontend.
def handle_button_click(button_id, payload=None):
    """
    routes requests based on button_id and executes the corresponding action
    
    Args:
        button_id (str): Identifier for which action to perform
        payload (dict): Additional parameters for the action (optional)
        
    Returns:
        dict: JSON response with results, status, or error messages
    """
    payload = payload or {}

    # VIEW RATINGS - Display all movies the user has rated
    if button_id == "view_ratings_button":
        try:
            # load user profile JSON containing all ratings
            data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except Exception:
            # if file doesn't exist or is corrupt, return empty profile
            data = {"username": None, "user_id": None, "ratings": []}

        results = []

        # process each rating entry and resolve movie titles
        for r in data.get("ratings", []):
            # get human-readable title (handles various entry formats)
            title = _resolve_title_from_entry(r) or (f"ID {r.get('movie_id')}" if r.get("movie_id") else "Untitled")
            results.append({
                "movie_id": r.get("movie_id") if r.get("movie_id") is not None else r.get("movie"),
                "title": title,
                "movie": title,  #(old key)
                "rating": r.get("rating"),
                "timestamp": r.get("timestamp"),
            })
        return {
            "ratings": results,
            "source": "profile",
            "username": data.get("username"),
            "user_id": data.get("user_id"),
        }

    # VIEW STATISTICS - Calculate and display user rating statistics
    if button_id == "view_statistics_button":
        try:
            # load user profile to analyze ratings
            profile = json.loads(PROFILE_PATH.read_text())
            ratings_list = profile.get("ratings", [])
            
            if not ratings_list:
                #no ratings yet - return empty statistics
                return {"statistics": {"total_ratings": 0, "average_rating": 0, "top_genres": []}}
            
            # calculate statistics from ratings list
            total = len(ratings_list)
            rating_values = [r.get("rating") for r in ratings_list if r.get("rating") is not None]
            avg = sum(rating_values) / len(rating_values) if rating_values else 0
            
            #get genre data from database for genre preference analysis
            from database.connection import get_db
            from database.paramstyle import ph_list
            
            #extract movie IDs from ratings
            movie_ids = [r.get("movie_id") for r in ratings_list if r.get("movie_id") is not None]
            genre_counter = Counter()  # count occurrences of each genre
            
            if movie_ids:
                #query database for genre information
                with get_db(readonly=True) as conn:
                    cur = conn.cursor()
                    cur.execute(
                        f"SELECT genres FROM movies WHERE movie_id IN ({ph_list(len(movie_ids))})",
                        movie_ids
                    )
                    #process genres (stored as pipe-separated strings: "Action|Drama|Thriller")
                    for row in cur.fetchall():
                        genres_str = row[0] if row else ""
                        if genres_str:
                            for genre in genres_str.split("|"):
                                genre = genre.strip()
                                if genre:
                                    genre_counter[genre] += 1
            
            # get top 10 most common genres
            top_genres = [
                {"genre": genre, "count": count}
                for genre, count in genre_counter.most_common(10)
            ]
            
            return {
                "statistics": {
                    "total_ratings": total,
                    "average_rating": avg,
                    "top_genres": top_genres
                }
            }
        except Exception as e:
            logger.error(f"Statistics error: {e}")
            return {"statistics": {"total_ratings": 0, "average_rating": 0, "top_genres": []}}

    # GET RECOMMENDATIONS - Generate personalized movie recommendations
    if button_id == "get_rec_button":
        from recommender.baseline import recommend_titles_for_user
        try:
            #load user profile to get user_id for recommendations
            profile = json.loads(PROFILE_PATH.read_text())
            uid = int(profile.get("user_id", 99))
        except Exception:
            #fallback to default user ID if profile load fails
            uid = 99

        #generate 500 recommendations using collaborative filtering
        recs = recommend_titles_for_user(uid, k=500)

        results = []
        #process recommendations into consistent format
        for item in recs:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                #item is (movie_id, score) tuple
                first, score = item[0], item[1]
                title = id_to_title(first) if isinstance(first, int) else normalize_title(str(first))
                try:
                    rating_val = float(score)  # Predicted rating score
                except Exception:
                    rating_val = None
                results.append({"title": title, "movie": title, "rating": rating_val})
            else:
                #item is dict or other format
                title = _resolve_title_from_entry(item if isinstance(item, dict) else {"movie": item})
                results.append({"title": title, "movie": title, "rating": None})

        return {"ratings": results, "source": "recs"}

    # ADD RATING - Save a new rating or update existing one
    if button_id == "add_rating_submit":
        movie_id = payload.get("movie_id") or payload.get("movie")
        rating = payload.get("rating")
        
        # validate required parameters
        if movie_id is None:
            return {"ok": False, "error": "No movie_id provided."}
        if rating is None:
            return {"ok": False, "error": "No rating provided."}

        try:
            #load existing profile or create new one
            if PROFILE_PATH.exists():
                prof = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
            else:
                prof = {"username": None, "user_id": None, "ratings": []}

            #normalize movie_id to integer when possible
            try:
                mid_val = int(movie_id)
            except Exception:
                mid_val = None

            #remove any existing rating for the same movie (prevent duplicates)
            prof["ratings"] = [
                r for r in prof.get("ratings", [])
                if str(r.get("movie_id") if r.get("movie_id") is not None else r.get("movie")) != str(movie_id)
            ]

            #create new rating entry with timestamp
            new_entry = {
                "movie_id": mid_val if mid_val is not None else movie_id,
                "rating": float(rating),
                "timestamp": int(time.time())  # Unix timestamp
            }
            prof.setdefault("ratings", []).append(new_entry)
            
            #ensure directory exists and save updated profile
            PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            PROFILE_PATH.write_text(json.dumps(prof, indent=2), encoding="utf-8")

            #attempt to sync changes to database (best-effort, non-critical)
            try:
                from api.sync_user_json import sync_user_ratings
                sync_user_ratings(PROFILE_PATH)
            except Exception as ex:
                logger.warning("sync_user_ratings failed on add: %s", ex)

            #return updated ratings list with resolved titles
            results = []
            for r in prof.get("ratings", []):
                title = _resolve_title_from_entry(r) or (f"ID {r.get('movie_id')}" if r.get("movie_id") else "Untitled")
                results.append({
                    "title": title, 
                    "rating": r.get("rating"), 
                    "movie_id": r.get("movie_id"), 
                    "timestamp": r.get("timestamp")
                })

            return {"ok": True, "message": "Rating saved.", "ratings": results, "source": "profile"}

        except Exception as ex:
            logger.exception("Failed to add rating")
            return {"ok": False, "error": str(ex)}

    # REMOVE RATING - Delete a movie rating from user profile
    if button_id == "remove_rating_button":
        movie_id = payload.get("movie_id") or payload.get("movie")
        
        #validate required parameter
        if movie_id is None:
            return {"ok": False, "error": "No movie_id provided."}

        try:
            #load existing profile or create empty one
            if PROFILE_PATH.exists():
                prof = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
            else:
                prof = {"username": None, "user_id": None, "ratings": []}

            #track if anything was actually removed
            before = len(prof.get("ratings", []))
            
            #filter out the rating for the specified movie
            prof["ratings"] = [
                r for r in prof.get("ratings", [])
                if str(r.get("movie_id") if r.get("movie_id") is not None else r.get("movie")) != str(movie_id)
            ]
            after = len(prof.get("ratings", []))
            
            #save updated profile
            PROFILE_PATH.write_text(json.dumps(prof, indent=2), encoding="utf-8")

            #attempt to sync changes to database (best-effort)
            try:
                from api.sync_user_json import sync_user_ratings
                sync_user_ratings(PROFILE_PATH)
            except Exception as ex:
                logger.warning("sync_user_ratings failed on remove: %s", ex)

            return {
                "ok": True, 
                "message": "Removed." if before != after else "No rating found.", 
                "ratings": prof.get("ratings", []), 
                "source": "profile"
            }
        except Exception as ex:
            logger.exception("Failed to remove rating")
            return {"ok": False, "error": str(ex)}

    # SEARCH - Find movies by keyword (title, genre, etc.)
    if button_id == "search":
        query = (payload or {}).get("query") or ""
        query = str(query).strip()
        
        if not query:
            #empty search returns no results
            return {"ratings": [], "source": "search", "query": query}
        
        try:
            #query database for movies matching the search term
            from database.db_query import search_movies_by_keyword
            rows = search_movies_by_keyword(query, limit=30)  # Limit to 30 results
            
            results = []
            for r in rows:
                #resolve title from row data or movie_id
                title = r.get("title") or (id_to_title(r.get("movie_id")) if r.get("movie_id") else None)
                display = title if title else (f"ID {r.get('movie_id')}" if r.get("movie_id") else "Untitled")
                
                results.append({
                    "movie_id": r.get("movie_id"),
                    "title": display,
                    "movie": display,  #(old key)
                    "year": r.get("year"),
                    "genres": r.get("genres"),
                })
            
            return {"ratings": results, "source": "search", "query": query}
        except Exception as ex:
            logger.exception("Search failed")
            return {"ratings": [], "source": "search", "error": str(ex)}

    # FALLBACK - Unknown button_id
    return {"error": f"Unhandled button id: {button_id}"}
