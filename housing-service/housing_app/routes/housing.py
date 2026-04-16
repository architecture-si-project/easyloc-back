import os

import jwt
from flask import Blueprint, jsonify, request

from housing_app.services.housing_service import create, delete, get_all, get_by_id, get_by_owner, search, update

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


@housing_bp.route("", methods=["GET"])
def get_housings():
    """List housing units.
    ---
    tags:
      - housing-service
    security:
      - bearerAuth: []
    responses:
      200:
        description: Housing list
      401:
        description: Missing or invalid token
    """
    _, auth_error = _require_token()
    if auth_error:
        return auth_error

    return jsonify(get_all())


@housing_bp.route("/search", methods=["GET"])
def search_housings():
    """Search housing units.
    ---
    tags:
      - housing-service
    security:
      - bearerAuth: []
    parameters:
      - in: query
        name: location
        schema:
          type: string
      - in: query
        name: property_type
        schema:
          type: string
      - in: query
        name: price_max
        schema:
          type: number
      - in: query
        name: owner_id
        schema:
          type: integer
    responses:
      200:
        description: Filtered housing list
      401:
        description: Missing or invalid token
    """
    _, auth_error = _require_token()
    if auth_error:
        return auth_error

    result = search(
        location=request.args.get("location"),
        property_type=request.args.get("property_type"),
        price_max=request.args.get("price_max", type=float),
        owner_id=request.args.get("owner_id", type=int),
    )
    return jsonify(result)


@housing_bp.route("/mine", methods=["GET"])
def get_housings_by_owner():
    """List housing units owned by authenticated user.
    ---
    tags:
      - housing-service
    security:
      - bearerAuth: []
    responses:
      200:
        description: Housing list for current owner
      401:
        description: Missing or invalid token
    """
    payload, auth_error = _require_token()
    if auth_error:
        return auth_error

    return jsonify(get_by_owner(payload["user_id"]))


@housing_bp.route("/<int:housing_id>", methods=["GET"])
def get_housing(housing_id):
    """Get a housing unit by ID.
    ---
    tags:
      - housing-service
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: housing_id
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Housing details
      401:
        description: Missing or invalid token
      404:
        description: Housing not found
    """
    _, auth_error = _require_token()
    if auth_error:
        return auth_error

    housing = get_by_id(housing_id)
    if not housing:
        return jsonify({"error": "Housing not found"}), 404
    return jsonify(housing)


@housing_bp.route("", methods=["POST"])
def create_housing():
    """Create a housing unit.
    ---
    tags:
      - housing-service
    security:
      - bearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              title:
                type: string
              property_type:
                type: string
              location:
                type: string
              price_per_night:
                type: number
            required: [title, property_type, location, price_per_night]
    responses:
      201:
        description: Housing created
      400:
        description: Missing or invalid required fields
      401:
        description: Missing or invalid token
    """
    payload, auth_error = _require_token()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    # owner_id comes from JWT to prevent client-side impersonation.
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
    """Update a housing unit.
    ---
    tags:
      - housing-service
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: housing_id
        required: true
        schema:
          type: integer
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
    responses:
      200:
        description: Housing updated
      401:
        description: Missing or invalid token
      404:
        description: Housing not found
    """
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
    """Delete a housing unit.
    ---
    tags:
      - housing-service
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: housing_id
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Housing deleted
      401:
        description: Missing or invalid token
      404:
        description: Housing not found
    """
    _, auth_error = _require_token()
    if auth_error:
        return auth_error

    deleted = delete(housing_id)

    if not deleted:
        return jsonify({"error": "Housing not found"}), 404

    return jsonify({"message": "Housing deleted"})
