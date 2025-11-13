import json
from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlmodel import Session, select

from app.models.form_response import FormResponse
from app.tasks import process_form_response
from app.utils.database import engine

webhook_bp = Blueprint("webhooks", __name__)


@webhook_bp.route("/tally", methods=["POST"])
def handle_tally_webhook():
    """
    Endpoint para receber webhooks do Tally.so

    Fluxo:
    1. Recebe payload do Tally
    2. Extrai email e nome
    3. Faz upsert no banco (se email já existe, atualiza)
    4. Dispara task assíncrona do Celery
    5. Retorna 202 (Accepted) imediatamente
    """

    try:
        payload = request.get_json()

        if not payload:
            return jsonify({"error": "Payload vazio"}), 400

        # Extrair dados básicos do payload
        data = payload.get("data", {})
        fields = data.get("fields", [])

        # Buscar nome e email
        name = ""
        email = ""
        for field in fields:
            label = field.get("label", "").lower()
            if "nome" in label:
                name = field.get("value", "")
            elif "e-mail" in label or "email" in label:
                email = field.get("value", "")

        if not email:
            return jsonify({"error": "Email não encontrado no payload"}), 400

        if not name:
            return jsonify({"error": "Nome não encontrado no payload"}), 400

        # Salvar no banco
        with Session(engine) as session:
            # Verificar se já existe (upsert)
            statement = select(FormResponse).where(FormResponse.email == email)
            existing = session.exec(statement).first()

            if existing:
                # Atualizar registro existente
                existing.name = name
                existing.raw_payload = json.dumps(payload)
                existing.tally_response_id = data.get("responseId", "")
                existing.submitted_at = datetime.utcnow()
                existing.updated_at = datetime.utcnow()
                # Resetar flags de processamento
                existing.processed = False
                existing.pdf_generated = False
                existing.email_sent = False
                existing.error_message = None
                response_record = existing
            else:
                # Criar novo registro
                response_record = FormResponse(
                    email=email,
                    name=name,
                    raw_payload=json.dumps(payload),
                    tally_response_id=data.get("responseId", ""),
                )
                session.add(response_record)

            session.commit()
            session.refresh(response_record)
            response_id = response_record.id

        # Disparar task assíncrona do Celery
        process_form_response.delay(response_id)  # type: ignore

        return jsonify(
            {
                "status": "success",
                "message": "Webhook recebido e processamento iniciado",
                "response_id": response_id,
            }
        ), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500
