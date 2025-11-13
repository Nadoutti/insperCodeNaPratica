import json
from typing import Any

from sqlmodel import Session

from app.celery_app import celery
from app.models.form_response import FormResponse
from app.tasks.email_sender import send_email_with_pdf
from app.tasks.pdf_generator import generate_pdf
from app.tasks.score_calculator import process_webhook
from app.utils.database import engine


@celery.task(name="process_form_response", bind=True, max_retries=3)
def process_form_response(self: Any, response_id: int) -> dict[str, Any]:
    """
    Task principal que orquestra o processamento completo.

    Pipeline:
    1. Calcula scores
    2. Gera PDF
    3. Envia email

    Args:
        response_id: ID do FormResponse no banco
    """

    try:
        with Session(engine) as session:
            # Buscar registro
            response = session.get(FormResponse, response_id)
            if not response:
                raise Exception(f"Response {response_id} não encontrado")

            # 1. Calcular scores
            payload = json.loads(response.raw_payload)
            result = process_webhook(payload)
            scores = result["scores"]

            # Atualizar scores no banco
            response.score_agilidade = scores.get("AGILIDADE", 0)
            response.score_agressividade = scores.get("AGRESSIVIDADE", 0)
            response.score_atencao_detalhes = scores.get("ATENÇÃO_A_DETALHES", 0)
            response.score_enfase_recompensas = scores.get("ÊNFASE_EM_RECOMPENSAS", 0)
            response.score_estabilidade = scores.get("ESTABILIDADE", 0)
            response.score_informalidade = scores.get("INFORMALIDADE", 0)
            response.score_orientacao_resultados = scores.get(
                "ORIENTAÇÃO_A_RESULTADOS", 0
            )
            response.score_trabalho_equipe = scores.get("TRABALHO_EM_EQUIPE", 0)
            response.processed = True
            session.commit()
            session.refresh(response)

        # 2. Gerar PDF
        pdf_path = generate_pdf(response_id)

        with Session(engine) as session:
            response = session.get(FormResponse, response_id)
            if response:
                response.pdf_generated = True
                session.commit()

        # 3. Enviar email
        send_email_with_pdf(response_id, pdf_path)

        with Session(engine) as session:
            response = session.get(FormResponse, response_id)
            if response:
                response.email_sent = True
                session.commit()

        return {"status": "success", "response_id": response_id}

    except Exception as e:
        # Salvar erro no banco
        with Session(engine) as session:
            response = session.get(FormResponse, response_id)
            if response:
                response.error_message = str(e)
                session.commit()

        # Retry automático do Celery
        raise self.retry(exc=e, countdown=60)


__all__ = ["process_form_response"]
