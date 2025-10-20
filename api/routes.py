from flask import Blueprint, request, jsonify, session
from api import api

# create a Flask Blueprint instance
api_bp = Blueprint("api_bp", __name__)


@api_bp.route("/login", methods=["POST"])
def login():
    """
    Handles user login by saving their username in the Flask session.
    This allows the server to remember the user between requests.
    """

    # Parse the JSON data sent in the request body
    data = request.get_json() or {}
    username = data.get("username")

    # no username is provided, return a 400 (Bad Request) error
    if not username:
        return jsonify({"error": "Username is required"}), 400

    # Save the username in Flask's session object (allows it to persist w/ cookies)
    session["username"] = username

    # Return a success message as JSON with status code 200 (OK)
    return jsonify({"message": f"Logged in as {username}"}), 200


@api_bp.route("/logout", methods=["POST"])
def logout():
    """
    Handles user logout by removing their username from the session.
    """

    # Remove the 'username' key from the session (if it exists)
    session.pop("username", None)

    # Return confirmation as JSON
    return jsonify({"message": "Logged out"}), 200


@api_bp.route("/session", methods=["GET"])
def get_session():
    """
    Returns information about the current session (if a user is logged in).
    """

    # retrieve the username from the session
    username = session.get("username")

    # respond with the username
    return jsonify({"username": username}), 200



@api_bp.route("/api/button-click", methods=["POST"])
def button_click():
    """
    Handles a button click event sent from the client.
    For example, when the user clicks a button on the frontend,
    the client sends an HTTP POST request here.
    """

    #extract JSON payload from the request body
    payload = request.get_json() or {}

    #retrieve which button was clicked
    button_id = payload.get("button")

    #print to server console for debugging
    print(f"Button clicked: {button_id}")

    #check if a user is logged in
    username = session.get("username")

    #if a user is logged in, attach their username to the payload so backend logic knows which user triggered the event
    if username:
        payload["username"] = username  

    #call handler function 
    result = api.handle_button_click(button_id, payload)

    # Return the result of that handler as JSON to the client
    return jsonify(result)
