from flask import Flask


def create_app():
    app = Flask(__name__)

    from housing_app.routes.housing import housing_bp

    app.register_blueprint(housing_bp)

    return app