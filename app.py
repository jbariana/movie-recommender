from flask import Flask, render_template, request, jsonify, session
from pathlib import Path
from api.routes import api_bp
import logging
import traceback
from datetime import timedelta

app = Flask(
    __name__,
    template_folder="ui/web/templates",
    static_folder="ui/web/static",
)

# Enable Flask sessions 
app.secret_key = "supersecretkey"  # replace later with env var
app.permanent_session_lifetime = timedelta(hours=2)

@app.before_request
def make_session_permanent():
    session.permanent = True


app.register_blueprint(api_bp)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = Path("data/ml-latest-small/movies.db")

#  Initialize database if needed 
def init():
    if DB_PATH.exists():
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

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    init()
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)
