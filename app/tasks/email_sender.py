import mimetypes
import os
import re
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, parseaddr

from sqlmodel import Session

from app.config import Config
from app.models.form_response import FormResponse
from app.utils.database import engine

_FILENAME_SAFE_RE = re.compile(r"[^A-Za-z0-9_.-]")  # para sanitizar nomes de arquivo


def _sanitize_filename(name: str) -> str:
    """Substitui caracteres inseguros por underscore e limita tamanho."""
    safe = _FILENAME_SAFE_RE.sub("_", name)
    return safe[:200] or "file"


def _extract_display_name(raw_from: str, smtp_user: str) -> str:
    """
    Recebe uma string (ex: "Nome <email@dominio>" ou "nome" ou "email@dominio")
    e retorna um display name razoável.
    """
    raw_from = (raw_from or "").strip()
    name, email_addr = parseaddr(raw_from)

    # se parseaddr devolveu um email diferente de vazio e esse email != smtp_user,
    # ainda assim usaremos smtp_user como endereço no header, mas podemos preservar o name.
    if name:
        return name.strip()
    # se não tem name, mas raw_from parece um e-mail e é diferente do smtp_user -> usar parte local
    if email_addr and email_addr != smtp_user:
        local = email_addr.split("@", 1)[0]
        return local.replace(".", " ").replace("_", " ").strip().title()
    # fallback padrão
    return "Na Prática - Insper"


def send_email_with_pdf(response_id: int, pdf_path: str):
    """
    Envia e-mail com anexo usando EmailMessage.
    - Header From: usa display name tirado de Config.SMTP_FROM (ou fallback) e endereço = Config.SMTP_USER
    - Não é necessário especificar `from_addr` no envio (o header já é igual ao SMTP_USER)
    - Sanitiza filename e response.name para o anexo
    """

    # pega o response (somente leitura)
    with Session(engine) as session:
        response = session.get(FormResponse, response_id)
        if not response:
            raise Exception(f"Resposta {response_id} não encontrada")

    # validações mínimas de config
    if not (
        Config.SMTP_HOST
        and Config.SMTP_PORT
        and Config.SMTP_USER
        and Config.SMTP_PASSWORD
    ):
        raise Exception("Configurações SMTP incompletas")

    # checagem do anexo
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(pdf_path)

    # extrai display name a partir da configuração (pode ser "Nome <email>" ou só "Nome" ou só "email")
    display_name = _extract_display_name(
        Config.SMTP_FROM or Config.SMTP_USER, Config.SMTP_USER
    )

    # monta EmailMessage
    msg = EmailMessage()
    msg["Subject"] = "Seu Relatório de Estilos de Trabalho - Na Prática"
    # o endereço no header FROM será o SMTP_USER (evita 553) com o display name extraído
    msg["From"] = formataddr((display_name, Config.SMTP_USER))
    # To vem do registro
    msg["To"] = response.email

    # opcional Reply-To (se configurado)
    if reply_to := getattr(Config, "SMTP_REPLY_TO", None):
        _, reply_email = parseaddr(reply_to)
        if reply_email:
            msg["Reply-To"] = reply_email

    # corpo
    body = f"""Olá {response.name},

Obrigado por participar do Teste de Estilos de Trabalho!

Seu relatório personalizado está em anexo.

Atenciosamente,
Equipe Na Prática - Insper
"""
    msg.set_content(body)

    # anexo: detecta mime-type e anexa
    ctype, _ = mimetypes.guess_type(pdf_path)
    if not ctype:
        ctype = "application/octet-stream"
    maintype, subtype = ctype.split("/", 1)

    # filename seguro
    safe_name = f"relatorio_{_sanitize_filename(response.name.replace(' ', '_'))}.pdf"

    with open(pdf_path, "rb") as f:
        data = f.read()
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=safe_name)

    # envio
    port = int(Config.SMTP_PORT)
    use_tls = bool(Config.SMTP_USE_TLS)
    ctx = ssl.create_default_context()

    # Observação: não passamos explicitamente from_addr para send_message/sendmail.
    # Como msg["From"] já contém Config.SMTP_USER, o envelope MAIL FROM enviado pelo cliente
    # normalmente será esse mesmo; isso mantém sua condição "não especificar ADDR".
    if use_tls:
        with smtplib.SMTP(Config.SMTP_HOST, port, timeout=30) as s:
            s.set_debuglevel(1)  # remover em produção se quiser
            s.ehlo()
            s.starttls(context=ctx)
            s.ehlo()
            s.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            # send_message usa os headers para determinar envelope quando from_addr não é passado
            s.send_message(msg, to_addrs=[response.email])
    else:
        with smtplib.SMTP_SSL(Config.SMTP_HOST, port, context=ctx, timeout=30) as s:
            s.set_debuglevel(1)
            s.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            s.send_message(msg, to_addrs=[response.email])

    # tenta remover o PDF temporário (não explodir se falhar)
    try:
        os.remove(pdf_path)
    except Exception:
        pass
