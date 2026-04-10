from flask import Blueprint, request, jsonify

from ..services.auth_service import register_user, authenticate_user

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
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
