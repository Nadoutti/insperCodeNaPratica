import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlmodel import Session

from app.config import Config
from app.models.form_response import FormResponse
from app.utils.database import engine


def send_email_with_pdf(response_id: int, pdf_path: str):
    """
    Envia email com PDF anexo para o participante.

    Args:
        response_id: ID do FormResponse no banco
        pdf_path: Caminho do arquivo PDF gerado
    """
    with Session(engine) as session:
        response = session.get(FormResponse, response_id)
        if not response:
            raise Exception(f"Response {response_id} não encontrado")

        # Validar configurações SMTP
        if not Config.SMTP_USER or not Config.SMTP_PASSWORD:
            raise Exception(
                "Configurações SMTP não definidas. Configure SMTP_USER e SMTP_PASSWORD."
            )

        # Configurar email
        msg = MIMEMultipart()
        msg["From"] = Config.SMTP_FROM or Config.SMTP_USER
        msg["To"] = response.email
        msg["Subject"] = "Seu Relatório de Estilos de Trabalho - Na Prática"

        # Corpo do email
        body = f"""Olá {response.name},

Obrigado por participar do Teste de Estilos de Trabalho!

Seu relatório personalizado está em anexo. Este documento contém uma análise detalhada dos seus estilos de trabalho preferidos, que podem ajudá-lo a identificar ambientes profissionais onde você tende a ser mais produtivo e satisfeito.

Caso tenha alguma dúvida sobre os resultados, não hesite em entrar em contato.

Atenciosamente,
Equipe Na Prática - Insper
"""

        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Anexar PDF
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Arquivo PDF não encontrado: {pdf_path}")

        with open(pdf_path, "rb") as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
            pdf_attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=f"relatorio_estilos_trabalho_{response.name.replace(' ', '_')}.pdf",
            )
            msg.attach(pdf_attachment)

        # Enviar email
        try:
            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                server.send_message(msg)
        except Exception as e:
            raise Exception(f"Erro ao enviar email: {str(e)}")

        # Limpar arquivo temporário
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass  # Não falhar se não conseguir deletar o arquivo temporário
