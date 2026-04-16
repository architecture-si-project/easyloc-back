import os

import jwt
from flask import Blueprint, jsonify, request

from ..services.reservation_service import (
    create_reservation_request,
    get_reservation_request,
    list_reservation_requests,
    update_reservation_status,
)

reservations_bp = Blueprint("reservations", __name__, url_prefix="/reservations")
SECRET_KEY = os.getenv("SECRET_KEY")


def _require_token():
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None, (jsonify({"error": "Missing token"}), 401)

    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if "user_id" not in payload:
            return None, (jsonify({"error": "Invalid token"}), 401)
    except Exception:
        return None, (jsonify({"error": "Invalid token"}), 401)

    return payload, None


@reservations_bp.route("/requests", methods=["POST"])
def create_request():
    """Create a reservation request.
    ---
    tags:
      - reservation-service
    security:
      - bearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              housing_id:
                type: integer
              start_date:
                type: string
                format: date
              end_date:
                type: string
                format: date
              notes:
                type: string
            required: [housing_id, start_date, end_date]
    responses:
      201:
        description: Reservation created
      400:
        description: Invalid payload
      401:
        description: Missing or invalid token
      404:
        description: Related entity not found
      409:
        description: Reservation conflict
    """
    payload, auth_error = _require_token()
    if auth_error:
        return auth_error

    auth_header = request.headers.get("Authorization", "")
    auth_token = auth_header.split(" ")[1] if " " in auth_header else None

    data = request.get_json(silent=True) or {}

    tenant_id = payload["user_id"]
    housing_id = data.get("housing_id")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    notes = data.get("notes")

    if not housing_id or not start_date or not end_date:
        return jsonify({"error": "Missing required fields"}), 400

    reservation = create_reservation_request(
        tenant_id=tenant_id,
        housing_id=housing_id,
        start_date=start_date,
        end_date=end_date,
        notes=notes,
        auth_token=auth_token,
    )

    if reservation.get("error") == "tenant_not_found":
        return jsonify({"error": "Tenant not found in user-service"}), 404

    if reservation.get("error") == "housing_not_found":
        return jsonify({"error": "Housing not found in housing-service"}), 404

    if reservation.get("error") == "invalid_date_format":
        return jsonify({"error": "Dates must follow YYYY-MM-DD format"}), 400

    if reservation.get("error") == "invalid_date_range":
        return jsonify({"error": "start_date must be before or equal to end_date"}), 400

    if reservation.get("error") == "housing_not_available":
        return jsonify({"error": "Housing is currently unavailable"}), 409

    if reservation.get("error") == "overlapping_reservation":
        return jsonify({"error": "Housing is not available on the requested period"}), 409

    return jsonify(reservation), 201


@reservations_bp.route("/requests", methods=["GET"])
def list_requests():
    """List reservation requests.
    ---
    tags:
      - reservation-service
    security:
      - bearerAuth: []
    parameters:
      - in: query
        name: status
        schema:
          type: string
      - in: query
        name: tenant_id
        schema:
          type: integer
    responses:
      200:
        description: Reservation requests list
      400:
        description: Invalid query params
      401:
        description: Missing or invalid token
    """
    _, auth_error = _require_token()
    if auth_error:
        return auth_error

    status = request.args.get("status")
    tenant_id = request.args.get("tenant_id")

    if tenant_id is not None:
        try:
            tenant_id = int(tenant_id)
        except ValueError:
            return jsonify({"error": "tenant_id must be an integer"}), 400

    reservations = list_reservation_requests(status=status, tenant_id=tenant_id)
    return jsonify(reservations)


@reservations_bp.route("/requests/me", methods=["GET"])
def list_my_requests():
    """List authenticated user's reservation requests.
    ---
    tags:
      - reservation-service
    security:
      - bearerAuth: []
    parameters:
      - in: query
        name: status
        schema:
          type: string
    responses:
      200:
        description: User reservation requests list
      401:
        description: Missing or invalid token
    """
    payload, auth_error = _require_token()
    if auth_error:
        return auth_error

    status = request.args.get("status")
    reservations = list_reservation_requests(status=status, tenant_id=payload["user_id"])
    return jsonify(reservations)


@reservations_bp.route("/requests/<int:reservation_id>", methods=["GET"])
def get_request(reservation_id):
    """Get reservation request by ID.
    ---
    tags:
      - reservation-service
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: reservation_id
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Reservation request details
      401:
        description: Missing or invalid token
      404:
        description: Reservation request not found
    """
    _, auth_error = _require_token()
    if auth_error:
        return auth_error

    reservation = get_reservation_request(reservation_id)

    if not reservation:
        return jsonify({"error": "Reservation request not found"}), 404

    return jsonify(reservation)


@reservations_bp.route("/requests/<int:reservation_id>/status", methods=["PATCH"])
def patch_request_status(reservation_id):
    """Update reservation request status.
    ---
    tags:
      - reservation-service
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: reservation_id
        required: true
        schema:
          type: integer
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
              actor_id:
                type: integer
              comment:
                type: string
            required: [status]
    responses:
      200:
        description: Reservation request updated
      400:
        description: Invalid payload
      401:
        description: Missing or invalid token
      404:
        description: Reservation request not found
      409:
        description: Invalid status transition
    """
    _, auth_error = _require_token()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}

    new_status = data.get("status")
    actor_id = data.get("actor_id")
    comment = data.get("comment")

    if not new_status:
        return jsonify({"error": "Missing required field: status"}), 400

    result = update_reservation_status(
        reservation_id=reservation_id,
        new_status=new_status,
        actor_id=actor_id,
        comment=comment,
    )

    if result.get("error") == "invalid_status":
        return jsonify({"error": "Invalid reservation status"}), 400

    if result.get("error") == "not_found":
        return jsonify({"error": "Reservation request not found"}), 404

    if result.get("error") == "invalid_transition":
        return jsonify(
            {
                "error": "Invalid status transition",
                "from": result.get("current_status"),
                "to": new_status,
            }
        ), 409

    return jsonify(result["reservation"])

