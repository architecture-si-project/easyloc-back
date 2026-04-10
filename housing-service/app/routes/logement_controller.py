from flask import Blueprint, jsonify, request
from app.services import logement_service

logement_bp = Blueprint("logements", __name__, url_prefix="/logements")


@logement_bp.route("", methods=["GET"])
def get_all():
    return jsonify([l.to_dict() for l in logement_service.get_all()])


@logement_bp.route("/search", methods=["GET"])
def search():
    result = logement_service.search(
        localisation=request.args.get("localisation"),
        type_=request.args.get("type"),
        prix_max=request.args.get("prix_max", type=float),
    )
    return jsonify([l.to_dict() for l in result])


@logement_bp.route("/<int:logement_id>", methods=["GET"])
def get_one(logement_id):
    logement = logement_service.get_by_id(logement_id)
    if not logement:
        return jsonify({"error": "Logement non trouvé"}), 404
    return jsonify(logement.to_dict())


@logement_bp.route("", methods=["POST"])
def create():
    data = request.get_json()
    required = ["titre", "type", "localisation", "prix_par_nuit", "proprietaire_id"]
    if not all(k in data for k in required):
        return jsonify({"error": f"Champs requis: {required}"}), 400
    logement = logement_service.create(data)
    return jsonify(logement.to_dict()), 201


@logement_bp.route("/<int:logement_id>", methods=["PUT"])
def update(logement_id):
    logement = logement_service.get_by_id(logement_id)
    if not logement:
        return jsonify({"error": "Logement non trouvé"}), 404
    logement = logement_service.update(logement, request.get_json())
    return jsonify(logement.to_dict())


@logement_bp.route("/<int:logement_id>", methods=["DELETE"])
def delete(logement_id):
    logement = logement_service.get_by_id(logement_id)
    if not logement:
        return jsonify({"error": "Logement non trouvé"}), 404
    logement_service.delete(logement)
    return jsonify({"message": "Logement supprimé"})
