import os

import jwt
from flask import Blueprint, jsonify, request

from housing_app.services.housing_service import create, delete, get_all, get_by_id, search, update

SECRET_KEY = os.getenv("SECRET_KEY")

housing_bp = Blueprint("housing", __name__, url_prefix="/housing")


def _require_token():
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return jsonify({"error": "Missing token"}), 401

    try:
        token = auth_header.split(" ")[1]
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except Exception:
        return jsonify({"error": "Invalid token"}), 401

    return None


def _parse_boolean(value):
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False

    return None


@housing_bp.route("", methods=["GET"])
def get_housings():
    auth_error = _require_token()
    if auth_error:
        return auth_error

    return jsonify(get_all())


@housing_bp.route("/search", methods=["GET"])
def search_housings():
    auth_error = _require_token()
    if auth_error:
        return auth_error

    result = search(
        location=request.args.get("location"),
        property_type=request.args.get("property_type"),
        price_max=request.args.get("price_max", type=float),
        available=_parse_boolean(request.args.get("available")),
    )
    return jsonify(result)


@housing_bp.route("/<int:housing_id>", methods=["GET"])
def get_housing(housing_id):
    auth_error = _require_token()
    if auth_error:
        return auth_error

    housing = get_by_id(housing_id)
    if not housing:
        return jsonify({"error": "Housing not found"}), 404
    return jsonify(housing)


@housing_bp.route("", methods=["POST"])
def create_housing():
    auth_error = _require_token()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    required_fields = ["title", "property_type", "location", "price_per_night", "owner_id"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields: {required_fields}"}), 400

    housing = create(data)
    return jsonify(housing), 201


@housing_bp.route("/<int:housing_id>", methods=["PUT"])
def update_housing(housing_id):
    auth_error = _require_token()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    housing = update(housing_id, data)

    if not housing:
        return jsonify({"error": "Housing not found"}), 404

    return jsonify(housing)


@housing_bp.route("/<int:housing_id>", methods=["DELETE"])
def delete_housing(housing_id):
    auth_error = _require_token()
    if auth_error:
        return auth_error

    deleted = delete(housing_id)

    if not deleted:
        return jsonify({"error": "Housing not found"}), 404

    return jsonify({"message": "Housing deleted"})

