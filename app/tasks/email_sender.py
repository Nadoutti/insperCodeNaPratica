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
    Envia email com PDF anexo para o participante.

    Args:
        response_id: ID do FormResponse no banco
        pdf_path: Caminho do arquivo PDF gerado
    """
    with Session(engine) as session:
        response = session.get(FormResponse, response_id)
        if not response:
            raise Exception(f"❌ Resposta com ID {response_id} não encontrada")

        # Validar configurações SMTP
        if not Config.SMTP_HOST or not Config.SMTP_USER or not Config.SMTP_PASSWORD:
            raise Exception(
                "⚠️ Configurações SMTP incompletas. Verifique as variáveis de ambiente."
            )

        try:
            port = int(Config.SMTP_PORT)
        except ValueError:
            raise Exception("⚠️ A porta SMTP deve ser um número (ex: 465 ou 587).")

        use_tls = Config.SMTP_USE_TLS

        # Configurar email
        msg = MIMEMultipart()
        header_from = Config.SMTP_FROM or Config.SMTP_USER
        msg["From"] = header_from
        msg["To"] = response.email
        msg["Subject"] = "Seu Relatório de Estilos de Trabalho - Na Prática"

        # Corpo do email
        body = f"""Olá {response.name},

✨ Obrigado por participar do Teste de Estilos de Trabalho! ✨

Seu relatório personalizado está em anexo.
Este documento contém uma análise detalhada dos seus estilos de trabalho preferidos,
que podem ajudá-lo a identificar ambientes profissionais onde você tende a ser mais produtivo e satisfeito.

Caso tenha alguma dúvida sobre os resultados, não hesite em entrar em contato.

Atenciosamente,
Equipe Na Prática - Insper
"""

        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Anexar PDF
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"❌ Arquivo PDF não encontrado: {pdf_path}")

        with open(pdf_path, "rb") as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
            filename = (
                f"relatorio_estilos_trabalho_{response.name.replace(' ', '_')}.pdf"
            )
            pdf_attachment.add_header(
                "Content-Disposition", "attachment", filename=filename
            )
            msg.attach(pdf_attachment)

        # Enviar email
        context = ssl.create_default_context()
        envelope_from = Config.SMTP_USER
        to_addrs = [response.email]

        print(f"📡 Conectando a {Config.SMTP_HOST}:{port} (TLS: {use_tls})...")

        try:
            if not use_tls:
                # Envio com SSL direto (ex: porta 465)
                print("🔒 Usando conexão SMTP_SSL...")
                with smtplib.SMTP_SSL(
                    Config.SMTP_HOST, port, context=context, timeout=30
                ) as server:
                    server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                    server.send_message(msg, from_addr=envelope_from, to_addrs=to_addrs)
            else:
                # Envio com STARTTLS (ex: porta 587)
                print("🔐 Usando conexão STARTTLS...")
                with smtplib.SMTP(Config.SMTP_HOST, port, timeout=30) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.ehlo()
                    server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                    server.send_message(msg, from_addr=envelope_from, to_addrs=to_addrs)

            print(f"✅ E-mail enviado com sucesso para {response.email}")

        except smtplib.SMTPAuthenticationError:
            raise Exception(
                "❌ Falha na autenticação SMTP. Verifique usuário e senha (ou gere senha de app)."
            )
        except smtplib.SMTPRecipientsRefused:
            raise Exception("❌ O destinatário foi recusado pelo servidor SMTP.")
        except smtplib.SMTPException as e:
            raise Exception(f"❌ Erro SMTP: {type(e).__name__} - {e}")
        except Exception as e:
            raise Exception(f"❌ Erro inesperado: {type(e).__name__} - {e}")
        finally:
            # Limpar arquivo temporário
            if os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except Exception:
                    pass
