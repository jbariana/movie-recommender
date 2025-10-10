from flask import Flask, render_template
from pathlib import Path
import threading
import traceback
import logging

app = Flask(
    __name__,
    template_folder="ui/web/templates",
    static_folder="ui/web/static",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_init_lock = threading.Lock()
_initialized = False

def init_database():
    global _initialized
    with _init_lock:
        if _initialized:
            return
        try:
            # delegate initialization to main.init_database_and_sync so server stays minimal
            from main import init_database_and_sync

            profile_path = Path(__file__).parent / "user_profile" / "user_profile.json"
            init_database_and_sync(data_path="data/ml-latest-small", profile_path=profile_path)
            logger.info("✅ DB initialized.")
    
            _initialized = True
        except Exception:
            logger.error("DB initialization failed, see traceback below:")
            traceback.print_exc()

# register DB init in a way that works across Flask versions
if hasattr(app, "before_serving"):
    try:
        app.before_serving(init_database_once)
    except Exception:
        logger.warning("before_serving registration failed, falling back to on-demand init")
elif hasattr(app, "before_first_request"):
    try:
        app.before_first_request(init_database_once)
    except Exception:
        logger.warning("before_first_request registration failed, falling back to on-demand init")

@app.route("/")
@app.route("/index")
def index():
    init_database()
    return render_template("index.html")

if __name__ == "__main__":
    init_database()
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)