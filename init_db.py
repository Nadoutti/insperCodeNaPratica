#!/usr/bin/env python3
"""Script para inicializar o banco de dados antes de iniciar o servidor"""
from app.utils.database import create_db_and_tables

if __name__ == "__main__":
    print("Criando tabelas do banco de dados...")
    create_db_and_tables()
    print("Tabelas criadas com sucesso!")
