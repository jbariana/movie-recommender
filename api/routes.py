from flask import Blueprint, request, jsonify
from api import api

api_bp = Blueprint("api_bp", __name__)

@api_bp.route("/api/button-click", methods=["POST"])
def button_click():
    payload = request.get_json() or {}
    button_id = payload.get("button")
    print(f"Button clicked: {button_id}")

    # pass the full payload to api handler so add-rating can include movie_id
    result = api.handle_button_click(button_id, payload)

    # Return its result (assuming it returns something JSON-serializable)
    return jsonify(result)