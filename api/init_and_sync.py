"""
init_and_sync.py
Database initialization and user profile synchronization utility.
"""

from pathlib import Path
from typing import Optional, Union


def init_database_and_sync(
    data_path: str = "data/ml-latest-small",
    profile_path: Optional[Union[Path, str]] = None
):
    """
    Initialize database schema, load MovieLens data, and sync user profile.
    
    Args:
        data_path: Path to MovieLens CSV files (movies, ratings, tags, links)
        profile_path: Path to user_profile.json (defaults to api/profile/user_profile.json)
    """
    #import functions
    from database.init_db import main as init_db
    from database.load_movielens import main as load_db
    from api.sync_user_json import sync_user_ratings

    #create database tables and indexes
    init_db()
    
    #load MovieLens CSV data into database
    load_db(data_path)
    
    #sync user ratings from JSON to database
    path_to_local = Path(profile_path) if profile_path else Path(__file__).parent / "profile" / "user_profile.json"
    sync_user_ratings(path_to_local)


#run with default settings
if __name__ == "__main__":
    init_database_and_sync()
