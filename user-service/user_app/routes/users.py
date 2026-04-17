from flask import Blueprint, jsonify

from ..services.auth_service import get_user_by_id

users_bp = Blueprint("users", __name__, url_prefix="/users")
TAG_NAME = "user-service"


@users_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """Get user by ID.
    ---
    tags:
      - user-service
    parameters:
      - in: path
        name: user_id
        required: true
        schema:
          type: integer
    responses:
      200:
        description: User details
      404:
        description: User not found
    """
    user = get_user_by_id(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user)
