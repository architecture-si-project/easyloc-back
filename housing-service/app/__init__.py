from flask import Flask

from .routes.house import houses_bp

def create_app():
    app = Flask(__name__)

    app.register_blueprint(houses_bp)

    return app