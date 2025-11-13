from flask import Blueprint, request

webhook_bp = Blueprint("webhooks", __name__)


@webhook_bp.route("/tally", methods=["POST"])
def handle_tally_webhook():
    """Endpoint para receber webhooks do Tally.so"""

    # TODO: remove this.
    with open("exemplo.json", "wb") as f:
        f.write(request.data)

    return "Em breve"
