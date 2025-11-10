from flask import Flask, render_template, session
from pathlib import Path
import logging
from datetime import timedelta
import json
import os
from dotenv import load_dotenv

app = Flask(__name__, template_folder="ui/web/templates", static_folder="ui/web/static")
load_dotenv()
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
app.permanent_session_lifetime = timedelta(hours=2)

@app.before_request
def make_session_permanent():
    session.permanent = True

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _database_needs_init() -> bool:
    from database.connection import DB_PATH, DATABASE_URL, get_db
    if DATABASE_URL:
        try:
            with get_db(readonly=True) as conn:
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM movies LIMIT 1;")
                cur.fetchone()
            return False
        except Exception:
            return True
    if not DB_PATH.exists():
        return True
    try:
        with get_db(readonly=True) as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='movies';")
            return cur.fetchone() is None
    except Exception:
        return True

def init():
    try:
        from api.init_and_sync import init_database_and_sync
        if _database_needs_init():
            profile_path = Path(__file__).parent / "user_profile" / "user_profile.json"
            init_database_and_sync(data_path="data/ml-latest-small", profile_path=profile_path)
            logger.info("Database initialized")
        else:
            logger.info("Database ready; skipping initialization")
    except Exception:
        logger.exception("Database initialization failed")

init()

from api.routes import api_bp
app.register_blueprint(api_bp)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/browse")
def browse_page():
    return render_template("browse.html")

@app.route("/profile")
def profile_page():
    return render_template("profile.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)
