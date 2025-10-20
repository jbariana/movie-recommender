from flask import Blueprint, request, jsonify, session
from api import api

api_bp = Blueprint("api_bp", __name__)

# User session routes
@api_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")

    if not username:
        return jsonify({"error": "Username is required"}), 400

    session["username"] = username
    return jsonify({"message": f"Logged in as {username}"}), 200


@api_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return jsonify({"message": "Logged out"}), 200


@api_bp.route("/session", methods=["GET"])
def get_session():
    username = session.get("username")
    return jsonify({"username": username}), 200


@api_bp.route("/api/button-click", methods=["POST"])
def button_click():
    payload = request.get_json() or {}
    button_id = payload.get("button")
    print(f"Button clicked: {button_id}")

    # You can optionally attach the username to the payload
    username = session.get("username")
    if username:
        payload["username"] = username  # makes user info available to api.handle_button_click()

    result = api.handle_button_click(button_id, payload)
    return jsonify(result)
