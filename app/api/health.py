from datetime import datetime, timezone

from flask import Blueprint, jsonify
from sqlmodel import text

from app.utils.database import engine

health_bp = Blueprint("health", __name__)


@health_bp.route("/", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        # Verificar conexão com banco de dados
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return jsonify(
            {
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ), 200

    except Exception as e:
        return jsonify(
            {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ), 503


@health_bp.route("/ready", methods=["GET"])
def readiness_check():
    """Readiness check endpoint"""
    return jsonify(
        {"status": "ready", "message": "Application is ready to receive requests"}
    ), 200
