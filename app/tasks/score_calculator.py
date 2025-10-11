from app.celery_app import celery


@celery.task
def calculate_scores(response_id: int):
    """Task para calcular scores baseado nas respostas do formulário"""
    # TODO: Implementar lógica de cálculo de scores
