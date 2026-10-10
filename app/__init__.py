from flask import Flask

from app.config import Config


def create_app() -> Flask:
    """Crea y configura la aplicación Flask."""

    app = Flask(__name__)

    app.config["MAX_CONTENT_LENGTH"] = (
        Config.MAX_CONTENT_LENGTH
    )

    from app.routes import main

    app.register_blueprint(main)

    return app