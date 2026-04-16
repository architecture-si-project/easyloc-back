from flask import Blueprint, request, jsonify

from ..services.auth_service import register_user, authenticate_user

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
TAG_NAME = "user-service"


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate a user and return a JWT token.
    ---
    tags:
      - user-service
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              email:
                type: string
                format: email
              password:
                type: string
            required: [email, password]
    responses:
      200:
        description: Authenticated
      400:
        description: Missing required fields
      401:
        description: Invalid credentials
    """
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing required fields"}), 400

    token = authenticate_user(email, password)

    if not token:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"token": token})


@auth_bp.route("/register", methods=["POST"])
def register():
    """Create a new user account.
    ---
    tags:
      - user-service
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              name:
                type: string
              email:
                type: string
                format: email
              password:
                type: string
            required: [name, email, password]
    responses:
      201:
        description: User created
      400:
        description: Missing required fields
      409:
        description: User already exists
    """
    data = request.json

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not email or not password or not name:
        return jsonify({"error": "Missing required fields"}), 400

    user = register_user(name, email, password)

    if not user:
        return jsonify({"error": "User already exists"}), 409

    return jsonify({
        "id": user["id"],
        "name": user["name"],
        "email": user["email"]
    }), 201
