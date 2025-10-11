from flask import Blueprint

webhook_bp = Blueprint("webhooks", __name__)


@webhook_bp.route("/tally", methods=["POST"])
def handle_tally_webhook():
    """Endpoint para receber webhooks do Tally.so"""

    return "Em breve"
