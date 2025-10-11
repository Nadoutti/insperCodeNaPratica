from app.celery_app import celery


@celery.task
def generate_pdf(response_id: int):
    """Task para gerar PDF baseado nas respostas do formulário"""
    # TODO: Implementar geração de PDF
