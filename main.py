from ui.cli import cli
from database.load_movielens import main as load_db
from database.init_db import main as init_db
from database.sync_json import sync_user_ratings
from pathlib import Path


if __name__ == "__main__":
    init_db()                                                                   # Initialize database
    load_db("data/ml-latest-small")                                             # Load the database

    path_to_local = Path(__file__).parent / "profile" / "user_profile.json"
    sync_user_ratings(path_to_local)                                            # Sync user ratings to db

    cli()                                                                       # Start UI (CLI in this case)
