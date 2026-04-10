from flask import Blueprint, jsonify, request

from ..services.reservation_service import (
    create_reservation_request,
    get_reservation_request,
    list_reservation_requests,
    update_reservation_status,
)

reservations_bp = Blueprint("reservations", __name__, url_prefix="/reservations")


@reservations_bp.route("/requests", methods=["POST"])
def create_request():
    # Cree une nouvelle demande de location.
    data = request.get_json(silent=True) or {}

    tenant_id = data.get("tenant_id")
    housing_id = data.get("housing_id")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    notes = data.get("notes")

    if not tenant_id or not housing_id or not start_date or not end_date:
        return jsonify({"error": "Missing required fields"}), 400

    # Le service metier effectue aussi les verifications inter-services (user/housing).
    reservation = create_reservation_request(
        tenant_id=tenant_id,
        housing_id=housing_id,
        start_date=start_date,
        end_date=end_date,
        notes=notes,
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
    # Liste les demandes avec filtres optionnels par statut et locataire.
    status = request.args.get("status")
    tenant_id = request.args.get("tenant_id")

    if tenant_id is not None:
        try:
            tenant_id = int(tenant_id)
        except ValueError:
            return jsonify({"error": "tenant_id must be an integer"}), 400

    reservations = list_reservation_requests(status=status, tenant_id=tenant_id)
    return jsonify(reservations)


@reservations_bp.route("/requests/<int:reservation_id>", methods=["GET"])
def get_request(reservation_id):
    # Retourne le detail d'une demande par identifiant.
    reservation = get_reservation_request(reservation_id)

    if not reservation:
        return jsonify({"error": "Reservation request not found"}), 404

    return jsonify(reservation)


@reservations_bp.route("/requests/<int:reservation_id>/status", methods=["PATCH"])
def patch_request_status(reservation_id):
    # Fait evoluer la demande dans le workflow de location.
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