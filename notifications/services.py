"""Serviço central de envio de emails.

Todas as apps enviam email por aqui: informam o tipo, o destinatário e um
contexto. O serviço renderiza os templates HTML + texto, monta o assunto e
envia. Falhas são logadas e NÃO propagam — email nunca deve interromper um
fluxo crítico (ex.: confirmação de matrícula).
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .emails import REGISTRY

logger = logging.getLogger(__name__)


def _contexto_base():
    """Dados institucionais injetados em todos os templates (cabeçalho/rodapé)."""
    return {
        'instituicao_nome': settings.INSTITUICAO_NOME,
        'contato_email': settings.INSTITUICAO_CONTATO_EMAIL,
        'contato_telefone': settings.INSTITUICAO_CONTATO_TELEFONE,
        'logo_url': settings.INSTITUICAO_LOGO_URL,
    }


def enviar_notificacao(tipo, destinatario, contexto=None):
    """Renderiza e envia o email do ``tipo`` para ``destinatario``.

    ``destinatario`` pode ser uma string ou lista de strings. Retorna True em
    caso de sucesso e False (logando) em caso de falha — nunca levanta exceção.
    """
    meta = REGISTRY.get(tipo)
    if meta is None:
        logger.error('Tipo de email desconhecido: %s', tipo)
        return False
    subject, template = meta

    destinatarios = [destinatario] if isinstance(destinatario, str) else list(destinatario)
    ctx = {**_contexto_base(), **(contexto or {})}

    try:
        corpo_txt = render_to_string(f'notifications/{template}.txt', ctx)
        corpo_html = render_to_string(f'notifications/{template}.html', ctx)
        msg = EmailMultiAlternatives(
            subject=f'{subject} — {settings.INSTITUICAO_NOME}',
            body=corpo_txt,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=destinatarios,
        )
        msg.attach_alternative(corpo_html, 'text/html')
        msg.send()
        return True
    except Exception:
        logger.exception('Falha ao enviar email %s para %s', tipo, destinatarios)
        return False


def enviar_para_admin(tipo, contexto=None):
    """Atalho para notificações internas — sempre vão para ADMIN_EMAIL."""
    return enviar_notificacao(tipo, settings.ADMIN_EMAIL, contexto)
