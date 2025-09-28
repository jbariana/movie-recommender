from ui.CLI import cli
from database.load_movielens import main as load_db


if __name__ == "__main__":
    load_db("data/ml-latest-small") # Load the database
    cli()                           # Start UI (CLI in this case)
