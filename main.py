from ui.cli import cli
from database.load_movielens import main as load_db
from database.init_db import main as init_db


if __name__ == "__main__":
    init_db()                       # Initialize database
    load_db("data/ml-latest-small") # Load the database
    cli()                           # Start UI (CLI in this case)
