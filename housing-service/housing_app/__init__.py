from flask import Flask
from flasgger import Swagger


TAG_NAME = "housing-service"


def _init_swagger(app: Flask) -> None:
    template = {
        "openapi": "3.0.3",
        "info": {"title": "Housing Service API", "version": "1.0.0"},
        "tags": [{"name": TAG_NAME, "description": "Housing endpoints"}],
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

    from housing_app.routes.housing import housing_bp

    app.register_blueprint(housing_bp)

    return app