from app import create_app
from app.utils.database import create_db_and_tables

app = create_app()


def main():
    """Função principal para executar a aplicação"""
    create_db_and_tables()

    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    main()
