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
    """
    Versão enxuta que replica o comportamento do teste manual:
    - força o envelope (MAIL FROM) para Config.SMTP_USER (evita 553),
    - monta um From legível usando o display name configurado,
    - usa sendmail(...) para garantir o envelope idêntico ao do teste manual,
    - opcional Reply-To via Config.SMTP_REPLY_TO.
    """

    # pega o response (mantemos a sessão só pra leitura)
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
    display = (Config.SMTP_FROM or Config.SMTP_USER).strip()

    # Extrair só o display name caso SMTP_FROM venha no formato "Nome <email>"
    if "<" in display and ">" in display:
        display_name = display.split("<", 1)[0].strip()
    else:
        # se o display é só um email igual ao SMTP_USER, usa um nome padrão
        display_name = display if display != Config.SMTP_USER else "Na Prática - Insper"

    # Header From: usar o display name, mas garantir que o endereço seja o SMTP_USER
    header_from = f"{display_name} <{Config.SMTP_USER}>"
    msg["From"] = header_from

    msg["To"] = response.email
    msg["Subject"] = "Seu Relatório de Estilos de Trabalho - Na Prática"

    body = f"""Olá {response.name},

Obrigado por participar do Teste de Estilos de Trabalho!

Seu relatório personalizado está em anexo.

Atenciosamente,
Equipe Na Prática - Insper
"""
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # anexo
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

    # Envelope deve ser o SMTP_USER (é isso que evitou o 553 nos seus testes)
    envelope_from = Config.SMTP_USER
    to_addrs = [response.email]
    ctx = ssl.create_default_context()

    # --- envio: usamos sendmail(...) (mesmo método que você testou manualmente) ---
    if use_tls:
        with smtplib.SMTP(Config.SMTP_HOST, port, timeout=30) as s:
            s.set_debuglevel(1)  # debug temporário — remova em produção
            s.ehlo()
            s.starttls(context=ctx)
            s.ehlo()
            s.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            s.sendmail(envelope_from, to_addrs, msg.as_string())
    else:
        with smtplib.SMTP_SSL(Config.SMTP_HOST, port, context=ctx, timeout=30) as s:
            s.set_debuglevel(1)
            s.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            s.sendmail(envelope_from, to_addrs, msg.as_string())

    # tentar remover o PDF temporário (não explodir se falhar)
    try:
        os.remove(pdf_path)
    except Exception:
        pass
