from flask import Flask

from .routes.reservations import reservations_bp


def create_app():
    app = Flask(__name__)

    app.register_blueprint(reservations_bp)

    return app