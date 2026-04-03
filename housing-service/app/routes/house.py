from flask import Blueprint, jsonify

houses_bp = Blueprint("houses", __name__, url_prefix="/houses")

@houses_bp.route("", methods=["GET"])
def get_houses():
    return jsonify([])

@houses_bp.route("/<int:house_id>", methods=["GET"])
def get_house(house_id):
    return jsonify({"id": house_id})