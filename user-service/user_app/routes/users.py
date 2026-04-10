import os

import jwt
from flask import Blueprint, jsonify, request



SECRET_KEY = os.getenv('SECRET_KEY')

users_bp = Blueprint("users", __name__, url_prefix="/users")

@users_bp.route("", methods=["GET"])
def get_users():
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return jsonify({"error": "Missing token"}), 401

    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except Exception:
        return jsonify({"error": "Invalid token"}), 401
    return jsonify([])

@users_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    return jsonify({"id": user_id})