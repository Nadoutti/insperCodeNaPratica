from flask import Flask

from app.api.health import health_bp
from app.api.webhooks import webhook_bp
from app.config import Config


def create_app():
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Registrar blueprints
    app.register_blueprint(webhook_bp, url_prefix="/api/v1/webhooks")
    app.register_blueprint(health_bp, url_prefix="/api/v1/health")

    return app
