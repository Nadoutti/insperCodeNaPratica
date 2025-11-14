import os
import smtplib
import ssl
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlmodel import Session

from app.config import Config
from app.models.form_response import FormResponse
from app.utils.database import engine


def send_email_with_pdf(response_id: int, pdf_path: str):
    """Envia PDF anexo para o participante (versão simples)."""

    with Session(engine) as session:
        response = session.get(FormResponse, response_id)
        if not response:
            raise Exception(f"Resposta {response_id} não encontrada")

    # validações mínimas
    if not (
        Config.SMTP_HOST
        and Config.SMTP_PORT
        and Config.SMTP_USER
        and Config.SMTP_PASSWORD
    ):
        raise Exception("Configurações SMTP incompletas")

    port = int(Config.SMTP_PORT)
    use_tls = bool(Config.SMTP_USE_TLS)

    # montar mensagem
    msg = MIMEMultipart()
    # display name opcional, mas o endereço no header usa o SMTP_USER para evitar 553
    display = Config.SMTP_FROM or f"{Config.SMTP_USER}"
    # se SMTP_FROM estiver no formato "Nome <email>", mantemos; senão montamos com SMTP_USER
    if "<" in str(display) and ">" in str(display):
        msg["From"] = display
    else:
        msg["From"] = f"{display} <{Config.SMTP_USER}>"

    msg["To"] = response.email
    msg["Subject"] = "Seu Relatório de Estilos de Trabalho - Na Prática"

    body = f"""Olá {response.name},

Obrigado por participar do Teste de Estilos de Trabalho!

Seu relatório personalizado está em anexo.

Atenciosamente,
Equipe Na Prática - Insper
"""
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(pdf_path)

    with open(pdf_path, "rb") as f:
        part = MIMEApplication(f.read(), _subtype="pdf")
        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=f"relatorio_{response.name.replace(' ', '_')}.pdf",
        )
        msg.attach(part)

    envelope_from = Config.SMTP_USER  # garante MAIL FROM autorizado
    to_addrs = [response.email]
    ctx = ssl.create_default_context()

    # enviar (SSL direto ou STARTTLS conforme flag)
    if not use_tls:
        with smtplib.SMTP_SSL(Config.SMTP_HOST, port, context=ctx, timeout=30) as s:
            s.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            s.send_message(msg, from_addr=envelope_from, to_addrs=to_addrs)
    else:
        with smtplib.SMTP(Config.SMTP_HOST, port, timeout=30) as s:
            s.ehlo()
            s.starttls(context=ctx)
            s.ehlo()
            s.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            s.send_message(msg, from_addr=envelope_from, to_addrs=to_addrs)

    # remover arquivo temporário (tenta, mas não explode se falhar)
    try:
        os.remove(pdf_path)
    except Exception:
        pass
