import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configurações da aplicação"""

    # Endpoint público
    DOMAIN = os.getenv("DOMAIN", "https://example.com")

    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://admin:password@localhost:5432/insper_forms"
    )

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Celery
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

    # SMTP
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587") or "587")
    SMTP_USER = os.getenv("SMTP_USER", None)
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", None)

    # Tally
    TALLY_API_KEY = os.getenv("TALLY_API_KEY", None)

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")

    # SQLModel
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
