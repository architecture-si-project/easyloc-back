import os

import jwt
from flask import Blueprint, jsonify, request

from housing_app.services.housing_service import create, delete, get_all, get_by_id, search, update

SECRET_KEY = os.getenv("SECRET_KEY")

housing_bp = Blueprint("housing", __name__, url_prefix="/housing")


def _require_token():
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None, (jsonify({"error": "Missing token"}), 401)

    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload, None
    except Exception:
        return None, (jsonify({"error": "Invalid token"}), 401)


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
    _, auth_error = _require_token()
    if auth_error:
        return auth_error

    return jsonify(get_all())


@housing_bp.route("/search", methods=["GET"])
def search_housings():
    _, auth_error = _require_token()
    if auth_error:
        return auth_error

    result = search(
        location=request.args.get("location"),
        property_type=request.args.get("property_type"),
        price_max=request.args.get("price_max", type=float),
        available=_parse_boolean(request.args.get("available")),
        owner_id=request.args.get("owner_id", type=int),
    )
    return jsonify(result)


@housing_bp.route("/<int:housing_id>", methods=["GET"])
def get_housing(housing_id):
    _, auth_error = _require_token()
    if auth_error:
        return auth_error

    housing = get_by_id(housing_id)
    if not housing:
        return jsonify({"error": "Housing not found"}), 404
    return jsonify(housing)


@housing_bp.route("", methods=["POST"])
def create_housing():
    payload, auth_error = _require_token()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    # owner_id is extracted from the JWT token, not from the request body
    data["owner_id"] = payload["user_id"]

    required_fields = ["title", "property_type", "location", "price_per_night"]
    string_fields = {"title", "property_type", "location"}

    missing_or_invalid = [
        field for field in required_fields
        if field not in data
        or data[field] is None
        or (field in string_fields and (not isinstance(data[field], str) or not data[field].strip()))
    ]

    if missing_or_invalid:
        return jsonify({"error": f"Missing or invalid required fields: {missing_or_invalid}"}), 400

    housing = create(data)
    return jsonify(housing), 201


@housing_bp.route("/<int:housing_id>", methods=["PUT"])
def update_housing(housing_id):
    _, auth_error = _require_token()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    housing = update(housing_id, data)

    if not housing:
        return jsonify({"error": "Housing not found"}), 404

    return jsonify(housing)


@housing_bp.route("/<int:housing_id>", methods=["DELETE"])
def delete_housing(housing_id):
    _, auth_error = _require_token()
    if auth_error:
        return auth_error

    deleted = delete(housing_id)

    if not deleted:
        return jsonify({"error": "Housing not found"}), 404

    return jsonify({"message": "Housing deleted"})

