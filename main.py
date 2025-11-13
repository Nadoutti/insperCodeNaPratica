from app import create_app

app = create_app()


def main():
    """Função principal para executar a aplicação"""
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    main()
