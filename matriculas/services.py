"""Regras da matrícula: preço, parcelamento, reserva de vaga, pagamento e confirmação.

Princípios:
- A vaga é reservada numa transação curta (com lock nas turmas) e a chamada ao
  Asaas acontece fora dela, para não segurar o lock durante a rede.
- Confirmar é idempotente: webhook do Asaas e consulta da página podem chegar
  em qualquer ordem, quantas vezes for.
- Expiração é preguiçosa: reserva vencida simplesmente deixa de ocupar vaga;
  o status vira EXPIRADA na próxima vez que alguém olha a matrícula.
"""
import logging
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from cursos.models import Turma
from notifications.emails import EmailType
from notifications.services import enviar_notificacao

from .asaas import AsaasError, get_asaas_client
from .models import Aluno, Cupom, Matricula, Promocao, TaxaParcelamento, Vaga

logger = logging.getLogger(__name__)
ZERO = Decimal('0.00')
CENTAVO = Decimal('0.01')


class PagamentoIndisponivel(Exception):
    """O Asaas não respondeu; a reserva foi desfeita e o aluno pode tentar de novo."""


# ---------------------------------------------------------------------------
# Preço
# ---------------------------------------------------------------------------


def promocao_vigente(turma, hoje=None):
    """Promoção ativa que se aplica à turma; a mais específica vence."""
    hoje = hoje or timezone.localdate()
    candidatas = [
        p for p in Promocao.objects.filter(
            is_ativa=True, data_inicio__lte=hoje, data_fim__gte=hoje
        )
        if p.aplica_a(turma)
    ]
    return max(candidatas, key=lambda p: (p.especificidade, p.pk), default=None)


def resolver_cupom(codigo, turma):
    if not codigo:
        return None
    cupom = Cupom.objects.filter(codigo__iexact=codigo.strip()).first()
    if cupom is None or not cupom.esta_valido(turma):
        raise ValidationError({'codigo_cupom': 'Cupom inválido, expirado ou esgotado.'})
    return cupom


def calcular_preco(turma, cupom=None, hoje=None):
    """Preço à vista: preço da turma − promoção − cupom (nunca negativo)."""
    original = Decimal(turma.preco)
    promocao = promocao_vigente(turma, hoje)
    desc_promo = promocao.calcular_desconto(original) if promocao else ZERO
    desc_cupom = cupom.calcular_desconto(original) if cupom else ZERO
    a_vista = max(original - desc_promo - desc_cupom, ZERO)
    return {
        'valor_original': original,
        'desconto_promocao': desc_promo,
        'desconto_cupom': desc_cupom,
        'valor_a_vista': a_vista,
        'promocao': promocao,
    }


def opcoes_parcelamento(valor_a_vista):
    """[{parcelas, valor_parcela, valor_total}] de 1x até MAX_PARCELAS, com o
    acréscimo cadastrado repassado ao aluno."""
    taxas = dict(TaxaParcelamento.objects.values_list('parcelas', 'acrescimo_percentual'))
    opcoes = []
    for n in range(1, settings.MAX_PARCELAS + 1):
        acrescimo = Decimal(taxas.get(n, 0)) if n > 1 else ZERO
        total = (valor_a_vista * (1 + acrescimo / 100)).quantize(CENTAVO, ROUND_HALF_UP)
        opcoes.append({
            'parcelas': n,
            'valor_parcela': (total / n).quantize(CENTAVO, ROUND_HALF_UP),
            'valor_total': total,
            'com_juros': acrescimo > 0,
        })
    return opcoes


def _valor_total(valor_a_vista, parcelas):
    return opcoes_parcelamento(valor_a_vista)[parcelas - 1]['valor_total']


# ---------------------------------------------------------------------------
# Início da matrícula
# ---------------------------------------------------------------------------


def _descricao(turma):
    return f'Matrícula — {turma.produto.nome} ({turma.codigo})'


@transaction.atomic
def _reservar(*, turma_id, aluno_dados, metodo, parcelas, codigo_cupom, ip):
    """Valida e cria a matrícula PENDENTE com as vagas reservadas."""
    turma = Turma.objects.select_related('curso', 'graduacao').get(pk=turma_id)
    # Lock nas turmas de curso envolvidas (ordem fixa por id evita deadlock).
    ids = sorted(t.pk for t in turma.turmas_curso_restantes())
    list(Turma.objects.select_for_update().filter(pk__in=ids).order_by('pk'))

    if not turma.disponivel():
        raise ValidationError({'turma': 'Esta turma não está mais disponível para matrícula.'})

    aluno, _ = Aluno.objects.update_or_create(cpf=aluno_dados['cpf'], defaults={
        'nome': aluno_dados['nome'], 'sobrenome': aluno_dados['sobrenome'],
        'email': aluno_dados['email'], 'telefone': aluno_dados['telefone'],
    })
    if Matricula.objects.filter(
        aluno=aluno, turma=turma, status=Matricula.Status.CONFIRMADA
    ).exists():
        raise ValidationError({'cpf': 'Este CPF já está matriculado nesta turma.'})

    # Uma nova tentativa substitui a reserva anterior da mesma pessoa.
    for antiga in Matricula.objects.filter(
        aluno=aluno, turma=turma, status=Matricula.Status.PENDENTE
    ):
        _expirar(antiga)

    cupom = resolver_cupom(codigo_cupom, turma)
    preco = calcular_preco(turma, cupom)
    if metodo == Matricula.Metodo.PIX:
        parcelas = 1
    matricula = Matricula.objects.create(
        aluno=aluno, turma=turma, metodo=metodo, parcelas=parcelas,
        valor_original=preco['valor_original'],
        desconto_promocao=preco['desconto_promocao'],
        desconto_cupom=preco['desconto_cupom'],
        valor_a_vista=preco['valor_a_vista'],
        valor_total=_valor_total(preco['valor_a_vista'], parcelas),
        cupom=cupom, promocao=preco['promocao'],
        reserva_expira_em=timezone.now() + timedelta(minutes=settings.RESERVA_MINUTOS),
        termos_aceitos_em=timezone.now(), ip=ip,
    )
    Vaga.objects.bulk_create(
        [Vaga(matricula=matricula, turma_id=pk) for pk in ids]
    )
    return matricula


def iniciar_matricula(*, turma_id, aluno, metodo, parcelas=1, codigo_cupom='',
                      cartao=None, endereco=None, ip=None):
    """Reserva a vaga e gera o pagamento.

    - PIX: devolve a matrícula PENDENTE com QR Code e copia-e-cola.
    - Cartão: cobra na hora → CONFIRMADA ou RECUSADA (com o motivo).
    - Valor zero (cupom de 100%): confirma direto, sem cobrança.

    Levanta ``PagamentoIndisponivel`` se o Asaas não responder.
    """
    matricula = _reservar(
        turma_id=turma_id, aluno_dados=aluno, metodo=metodo,
        parcelas=parcelas, codigo_cupom=codigo_cupom, ip=ip,
    )
    if matricula.valor_total == ZERO:
        confirmar_matricula(matricula)
        matricula.refresh_from_db()
        return matricula

    client = get_asaas_client()
    try:
        al = matricula.aluno
        if not al.asaas_customer_id:
            al.asaas_customer_id = client.criar_ou_recuperar_cliente(
                nome=al.nome_completo, cpf=al.cpf, email=al.email, telefone=al.telefone,
            )
            al.save(update_fields=['asaas_customer_id'])

        comum = {
            'customer_id': al.asaas_customer_id,
            'descricao': _descricao(matricula.turma),
            'referencia': str(matricula.pk),
        }
        if metodo == Matricula.Metodo.PIX:
            pix = client.cobrar_pix(valor=matricula.valor_total, **comum)
            matricula.asaas_payment_id = pix['payment_id']
            matricula.pix_qrcode = pix['pix_qrcode']
            matricula.pix_copia_cola = pix['pix_copia_cola']
            matricula.save(update_fields=['asaas_payment_id', 'pix_qrcode', 'pix_copia_cola'])
            return matricula

        resultado = client.cobrar_cartao(
            valor_total=matricula.valor_total, parcelas=matricula.parcelas,
            cartao=cartao, ip=ip or '0.0.0.0',
            titular={
                'nome': al.nome_completo, 'email': al.email, 'cpf': al.cpf,
                'telefone': al.telefone, **(endereco or {}),
            },
            **comum,
        )
    except AsaasError as exc:
        if exc.recusado and metodo == Matricula.Metodo.CARTAO:
            Matricula.objects.filter(pk=matricula.pk).update(
                status=Matricula.Status.RECUSADA, observacao=str(exc)
            )
            matricula.refresh_from_db()
            return matricula
        logger.error('Asaas indisponível na matrícula #%s: %s', matricula.pk, exc)
        Matricula.objects.filter(pk=matricula.pk).update(
            status=Matricula.Status.EXPIRADA, observacao=f'Falha no Asaas: {exc}'
        )
        raise PagamentoIndisponivel() from None

    matricula.asaas_payment_id = resultado['payment_id']
    matricula.asaas_installment_id = resultado['installment_id']
    matricula.save(update_fields=['asaas_payment_id', 'asaas_installment_id'])
    if resultado['pago']:
        confirmar_matricula(matricula)
    matricula.refresh_from_db()
    return matricula


# ---------------------------------------------------------------------------
# Confirmação, expiração, consulta
# ---------------------------------------------------------------------------


@transaction.atomic
def confirmar_matricula(matricula):
    """Pagamento garantido → aluno matriculado. Idempotente."""
    m = Matricula.objects.select_for_update().select_related('turma').get(pk=matricula.pk)
    if m.status == Matricula.Status.CONFIRMADA:
        return False
    if m.status not in (Matricula.Status.PENDENTE, Matricula.Status.EXPIRADA):
        # Pago depois de recusado/cancelado: não matricula; a secretaria estorna.
        logger.warning('Pagamento recebido para matrícula #%s em status %s.', m.pk, m.status)
        return False
    if m.status == Matricula.Status.EXPIRADA:
        # PIX pago depois do prazo: o aluno pagou, então honramos a matrícula.
        logger.warning('Matrícula #%s confirmada após expirar a reserva.', m.pk)
    m.status = Matricula.Status.CONFIRMADA
    m.confirmada_em = timezone.now()
    m.save(update_fields=['status', 'confirmada_em'])
    if m.cupom_id:
        Cupom.objects.filter(pk=m.cupom_id).update(usos_atuais=F('usos_atuais') + 1)
    transaction.on_commit(lambda: _emails_confirmacao(m))
    return True


def _expirar(matricula):
    Matricula.objects.filter(pk=matricula.pk, status=Matricula.Status.PENDENTE).update(
        status=Matricula.Status.EXPIRADA
    )
    if matricula.asaas_payment_id:
        # Fora da transação: não segura locks esperando a rede.
        transaction.on_commit(lambda: _cancelar_cobranca(matricula))


def _cancelar_cobranca(matricula):
    try:
        get_asaas_client().cancelar_cobranca(matricula.asaas_payment_id)
    except AsaasError as exc:
        logger.warning('Não foi possível cancelar a cobrança da matrícula #%s: %s',
                       matricula.pk, exc)


def atualizar_status(matricula):
    """Usado pela página que aguarda o PIX: confirma se o Asaas já recebeu
    (caso o webhook não tenha chegado) e expira a reserva vencida."""
    if matricula.status != Matricula.Status.PENDENTE:
        return matricula
    # Consulta o Asaas no máximo a cada 15 s por matrícula.
    chave = f'asaas-consulta-{matricula.pk}'
    if matricula.asaas_payment_id and cache.add(chave, 1, timeout=15):
        try:
            if get_asaas_client().pagamento_confirmado(matricula.asaas_payment_id):
                confirmar_matricula(matricula)
        except AsaasError as exc:
            logger.warning('Consulta ao Asaas falhou (matrícula #%s): %s', matricula.pk, exc)
    matricula.refresh_from_db()
    if matricula.status == Matricula.Status.PENDENTE and not matricula.reserva_ativa():
        _expirar(matricula)
        matricula.refresh_from_db()
    return matricula


# ---------------------------------------------------------------------------
# Webhook do Asaas
# ---------------------------------------------------------------------------

EVENTOS_PAGAMENTO = {'PAYMENT_CONFIRMED', 'PAYMENT_RECEIVED'}


def webhook_autentico(headers):
    """Compara o token do header em tempo constante."""
    import hmac
    token = headers.get('asaas-access-token')
    if not token or not settings.ASAAS_WEBHOOK_TOKEN:
        return False
    return hmac.compare_digest(str(token), str(settings.ASAAS_WEBHOOK_TOKEN))


def processar_webhook(payload):
    evento = (payload or {}).get('event')
    pagamento = (payload or {}).get('payment') or {}
    if evento not in EVENTOS_PAGAMENTO:
        return {'ignored': True}
    # Parcelado: cada parcela gera um evento; todas apontam para a mesma matrícula
    # via externalReference — a primeira confirma, as demais são ignoradas.
    referencia = str(pagamento.get('externalReference') or '')
    matricula = None
    if referencia.isdigit():
        matricula = Matricula.objects.filter(pk=int(referencia)).first()
    if matricula is None and pagamento.get('id'):
        matricula = Matricula.objects.filter(asaas_payment_id=pagamento['id']).first()
    if matricula is None:
        return {'ignored': True, 'reason': 'matricula_nao_encontrada'}
    return {'processed': confirmar_matricula(matricula), 'matricula_id': matricula.pk}


# ---------------------------------------------------------------------------
# Cancelamento (secretaria, pelo Admin)
# ---------------------------------------------------------------------------


@transaction.atomic
def cancelar_e_estornar(matricula, motivo=''):
    """Estorna no Asaas, cancela a matrícula e libera as vagas."""
    m = Matricula.objects.select_for_update().get(pk=matricula.pk)
    if m.status != Matricula.Status.CONFIRMADA:
        raise ValueError('Só matrículas confirmadas podem ser canceladas e estornadas.')
    if m.asaas_payment_id:
        get_asaas_client().estornar(
            payment_id=m.asaas_payment_id, installment_id=m.asaas_installment_id
        )
    m.status = Matricula.Status.CANCELADA
    m.cancelada_em = timezone.now()
    m.observacao = '\n'.join(filter(None, [m.observacao, motivo]))
    m.save(update_fields=['status', 'cancelada_em', 'observacao'])


# ---------------------------------------------------------------------------
# Emails
# ---------------------------------------------------------------------------


def resumo_turma(turma):
    """Cursos da turma com datas, horários e professores (para emails/páginas)."""
    componentes = turma.turmas_curso.select_related('curso').prefetch_related(
        'horarios', 'professores'
    ) if turma.is_graduacao else [turma]
    itens = []
    for t in sorted(componentes, key=lambda t: (t.data_inicio, t.curso.nome)):
        itens.append({
            'curso': t.curso.nome,
            'inicio': t.data_inicio,
            'fim': t.data_fim,
            'horarios': [str(h) for h in t.horarios.all()],
            'professores': [p.nome for p in t.professores.all()],
        })
    return itens


def _contexto(m):
    turma = m.turma
    return {
        'nome': m.aluno.nome_completo,
        'email': m.aluno.email,
        'cpf': m.aluno.cpf_formatado,
        'telefone': m.aluno.telefone,
        'tipo': 'Graduação' if turma.is_graduacao else 'Curso',
        'produto': turma.produto.nome,
        'turma': turma.codigo,
        'inicio': turma.inicio,
        'fim': turma.fim,
        'cursos': resumo_turma(turma),
        'endereco': settings.SEDE_ENDERECO,
        'metodo': m.get_metodo_display(),
        'parcelas': m.parcelas,
        'valor_parcela': m.valor_parcela,
        'valor_total': m.valor_total,
        'admin_url': f"{settings.BACKEND_URL.rstrip('/')}/admin/matriculas/matricula/{m.pk}/change/",
    }


def _emails_confirmacao(m):
    ctx = _contexto(m)
    enviar_notificacao(EmailType.MATRICULA_CONFIRMADA, m.aluno.email, ctx)
    enviar_notificacao(EmailType.MATRICULA_NOVA_REITOR, settings.REITOR_EMAIL, ctx)
