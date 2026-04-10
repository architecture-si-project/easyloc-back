from flask import Flask

from .routes.auth import auth_bp
from .routes.users import users_bp

def create_app():
    app = Flask(__name__)

    app.register_blueprint(users_bp)
    app.register_blueprint(auth_bp)

    return app