from flask import Blueprint, jsonify, request

users_bp = Blueprint("users", __name__, url_prefix="/users")

# Utilisateur factice pour l'équipe auth
users = [
    {
        "id": 1,
        "username": "aa",
        "password": "bb",  # à hasher quand l'équipe auth implémente la sécurité
        "role": "locataire",
        "email": "aa@easyloc.fr",
    }
]
next_id = 2


@users_bp.route("", methods=["GET"])
def get_users():
    safe = [{k: v for k, v in u.items() if k != "password"} for u in users]
    return jsonify(safe)


@users_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    safe = {k: v for k, v in user.items() if k != "password"}
    return jsonify(safe)


@users_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user = next((u for u in users if u["username"] == username and u["password"] == password), None)
    if not user:
        return jsonify({"error": "Identifiants invalides"}), 401
    safe = {k: v for k, v in user.items() if k != "password"}
    # L'équipe auth peut remplacer ce retour par un vrai JWT
    return jsonify({"message": "Connexion réussie", "user": safe})


@users_bp.route("", methods=["POST"])
def create_user():
    global next_id
    data = request.get_json()
    required = ["username", "password", "role"]
    if not all(k in data for k in required):
        return jsonify({"error": f"Champs requis: {required}"}), 400
    if any(u["username"] == data["username"] for u in users):
        return jsonify({"error": "Nom d'utilisateur déjà pris"}), 409

    user = {
        "id": next_id,
        "username": data["username"],
        "password": data["password"],
        "role": data["role"],
        "email": data.get("email", ""),
    }
    users.append(user)
    next_id += 1
    safe = {k: v for k, v in user.items() if k != "password"}
    return jsonify(safe), 201