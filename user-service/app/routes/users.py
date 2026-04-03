from flask import Blueprint, jsonify

users_bp = Blueprint("users", __name__, url_prefix="/users")

@users_bp.route("", methods=["GET"])
def get_users():
    return jsonify([])

@users_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    return jsonify({"id": user_id})