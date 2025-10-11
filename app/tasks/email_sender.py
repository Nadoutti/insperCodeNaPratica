from app.celery_app import celery


@celery.task
def send_email(response_id: int):
    """Task para enviar email com PDF para o participante"""
    # TODO: Implementar envio de email
