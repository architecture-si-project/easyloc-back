from flask import Flask
from flasgger import Swagger

from .routes.reservations import reservations_bp


TAG_NAME = "reservation-service"


def _init_swagger(app: Flask) -> None:
    template = {
        "openapi": "3.0.3",
        "info": {"title": "Reservation Service API", "version": "1.0.0"},
        "tags": [{"name": TAG_NAME, "description": "Reservation endpoints"}],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
        },
    }

    config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "openapi",
                "route": "/openapi.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "swagger_ui": False,
    }

    Swagger(app, template=template, config=config)


def create_app():
    app = Flask(__name__)
    _init_swagger(app)

    app.register_blueprint(reservations_bp)

    return app