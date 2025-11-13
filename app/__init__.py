from flask import Flask

from app.api.health import health_bp
from app.api.webhooks import webhook_bp
from app.config import Config
from app.utils.database import create_db_and_tables


def create_app():
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)

    create_db_and_tables()

    # Registrar blueprints
    app.register_blueprint(webhook_bp, url_prefix="/api/v1/webhooks")
    app.register_blueprint(health_bp, url_prefix="/api/v1/health")

    return app
