from flask import Flask, render_template, session
from pathlib import Path
import logging
import traceback
from datetime import timedelta

app = Flask(
    __name__,
    template_folder="ui/web/templates",
    static_folder="ui/web/static",
)

# Enable Flask sessions
app.secret_key = "supersecretkey"
app.permanent_session_lifetime = timedelta(hours=2)

@app.before_request
def make_session_permanent():
    session.permanent = True

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prefer the same DB file used by database.connection
try:
    from database.connection import DB_PATH as DB_CONN_PATH
except Exception:
    DB_CONN_PATH = Path("data/ml-latest-small/movies.db")

def init():
    if DB_CONN_PATH.exists():
        logger.info("Database already exists, skipping initialization.")
        return

    try:
        from api.init_and_sync import init_database_and_sync
        profile_path = Path(__file__).parent / "user_profile" / "user_profile.json"
        init_database_and_sync(
            data_path="data/ml-latest-small",
            profile_path=profile_path
        )
        logger.info("Database initialized successfully.")
    except Exception:
        logger.error("Database initialization failed:")
        traceback.print_exc()

init()

# Import and register API blueprint after init()
from api.routes import api_bp
app.register_blueprint(api_bp)

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)
