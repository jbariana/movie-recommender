from flask import Flask, render_template
from pathlib import Path
import logging
import traceback

app = Flask(
    __name__,
    template_folder="ui/web/templates",
    static_folder="ui/web/static",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = Path("data/ml-latest-small/movies.db")

#helper function to init db only when it doesn't exist already
def init_database():
    if DB_PATH.exists():
        logger.info("Database already exists, skipping initialization.")
        return

    try:
        from main import init_database_and_sync
        profile_path = Path(__file__).parent / "user_profile" / "user_profile.json"
        init_database_and_sync(
            data_path="data/ml-latest-small",
            profile_path=profile_path
        )
        logger.info("Database initialized successfully.")
    except Exception:
        logger.error("Database initialization failed:")
        traceback.print_exc()

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    init_database()
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)
