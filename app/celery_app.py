from celery import Celery

from app.config import Config


def create_celery_app():
    """Factory function para criar aplicação Celery"""
    celery = Celery("insper_forms")

    celery.conf.update(
        broker_url=Config.CELERY_BROKER_URL,
        result_backend=Config.CELERY_RESULT_BACKEND,
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )

    celery.autodiscover_tasks(["app.tasks"])

    return celery


celery = create_celery_app()
