from pathlib import Path

def init_database_and_sync(data_path: str = "data/ml-latest-small", profile_path: Path | str | None = None):
    from database.init_db import main as init_db
    from database.load_movielens import main as load_db
    from database.sync_json import sync_user_ratings

    init_db()
    load_db(data_path)
    path_to_local = Path(profile_path) if profile_path else Path(__file__).parent / "profile" / "user_profile.json"
    sync_user_ratings(path_to_local)

if __name__ == "__main__":
    init_database_and_sync()