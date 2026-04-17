from flask import Flask
from flasgger import Swagger

from .routes.auth import auth_bp
from .routes.users import users_bp


TAG_NAME = "user-service"


def _init_swagger(app: Flask) -> None:
    template = {
        "openapi": "3.0.3",
        "info": {"title": "User Service API", "version": "1.0.0"},
        "tags": [{"name": TAG_NAME, "description": "User and authentication endpoints"}],
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

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)

    return app