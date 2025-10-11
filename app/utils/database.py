from sqlmodel import SQLModel, create_engine

from app.config import Config

engine = create_engine(Config.DATABASE_URL, echo=True)


def create_db_and_tables():
    """Criar banco de dados e tabelas"""
    SQLModel.metadata.create_all(engine)
