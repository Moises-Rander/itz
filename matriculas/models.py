"""Matrícula: aluno (sem login), pagamento via Asaas e ocupação de vagas.

Fluxo: PENDENTE (reserva de vaga ativa) → CONFIRMADA quando o pagamento cai.
Sem pagamento dentro do prazo a reserva expira sozinha: a ``Vaga`` deixa de
contar como ocupada assim que ``reserva_expira_em`` passa — não depende de
tarefa agendada (o servidor pode estar dormindo).
"""
import secrets
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class TipoDesconto(models.TextChoices):
    PERCENTUAL = 'PERCENTUAL', 'Percentual (%)'
    FIXO = 'FIXO', 'Valor fixo (R$)'


def _aplicar_desconto(valor_base, tipo, valor_desconto):
    """Valor do desconto (R$) sobre valor_base, sem nunca ultrapassá-lo."""
    valor_base = Decimal(valor_base)
    valor_desconto = Decimal(valor_desconto)
    if tipo == TipoDesconto.PERCENTUAL:
        desconto = valor_base * valor_desconto / Decimal('100')
    else:
        desconto = valor_desconto
    return min(desconto, valor_base).quantize(Decimal('0.01'))


class AlvoDesconto(models.Model):
    """Restrição opcional de um desconto a uma turma, curso ou formação."""

    turma = models.ForeignKey(
        'cursos.Turma', on_delete=models.CASCADE, null=True, blank=True,
        related_name='+', verbose_name='turma',
    )
    curso = models.ForeignKey(
        'cursos.Curso', on_delete=models.CASCADE, null=True, blank=True,
        related_name='+', verbose_name='curso',
    )
    formacao = models.ForeignKey(
        'cursos.Formacao', on_delete=models.CASCADE, null=True, blank=True,
        related_name='+', verbose_name='formação',
    )

    class Meta:
        abstract = True

    def _alvos(self):
        return [a for a in (self.turma_id, self.curso_id, self.formacao_id) if a]

    def aplica_a(self, turma):
        if self.turma_id:
            return self.turma_id == turma.pk
        if self.curso_id:
            return self.curso_id == turma.curso_id
        if self.formacao_id:
            return self.formacao_id == turma.formacao_id
        return True  # sem restrição: vale para tudo

    def clean(self):
        if len(self._alvos()) > 1:
            raise ValidationError('Restrinja a no máximo um: turma, curso ou formação.')
        if getattr(self, 'data_inicio', None) and getattr(self, 'data_fim', None):
            if self.data_fim < self.data_inicio:
                raise ValidationError({'data_fim': 'A data de fim não pode ser anterior ao início.'})


class Cupom(AlvoDesconto):
    codigo = models.CharField('código', max_length=40, unique=True)
    tipo_desconto = models.CharField('tipo de desconto', max_length=12, choices=TipoDesconto.choices)
    valor_desconto = models.DecimalField('valor do desconto', max_digits=10, decimal_places=2)
    data_inicio = models.DateField('início da validade')
    data_fim = models.DateField('fim da validade')
    max_usos = models.PositiveIntegerField('máximo de usos', default=1)
    usos_atuais = models.PositiveIntegerField(
        'usos', default=0, help_text='Contado quando a matrícula é confirmada.'
    )
    is_ativo = models.BooleanField('ativo', default=True)

    class Meta:
        verbose_name = 'cupom'
        verbose_name_plural = 'cupons'
        ordering = ['codigo']

    def __str__(self):
        return self.codigo

    def esta_valido(self, turma, em=None):
        hoje = em or timezone.localdate()
        return (
            self.is_ativo
            and self.usos_atuais < self.max_usos
            and self.data_inicio <= hoje <= self.data_fim
            and self.aplica_a(turma)
        )

    def calcular_desconto(self, valor_base):
        return _aplicar_desconto(valor_base, self.tipo_desconto, self.valor_desconto)


class Promocao(AlvoDesconto):
    """Desconto automático enquanto vigente. A mais específica vence
    (turma > curso/formação > geral)."""

    nome = models.CharField('nome', max_length=120, blank=True, help_text='Ex.: Black Friday')
    tipo_desconto = models.CharField('tipo de desconto', max_length=12, choices=TipoDesconto.choices)
    valor = models.DecimalField('valor do desconto', max_digits=10, decimal_places=2)
    data_inicio = models.DateField('início')
    data_fim = models.DateField('fim')
    is_ativa = models.BooleanField('ativa', default=True)

    class Meta:
        verbose_name = 'promoção'
        verbose_name_plural = 'promoções'
        ordering = ['-data_inicio']

    def __str__(self):
        return self.nome or f'Promoção {self.get_tipo_desconto_display()} #{self.pk}'

    def calcular_desconto(self, valor_base):
        return _aplicar_desconto(valor_base, self.tipo_desconto, self.valor)

    @property
    def especificidade(self):
        if self.turma_id:
            return 2
        return 1 if (self.curso_id or self.formacao_id) else 0


class TaxaParcelamento(models.Model):
    """Acréscimo repassado ao aluno ao parcelar no cartão.

    Ex.: 12 parcelas com acréscimo de 15% → total = valor à vista × 1,15.
    Número de parcelas sem linha cadastrada = sem acréscimo.
    """

    parcelas = models.PositiveSmallIntegerField('parcelas', unique=True)
    acrescimo_percentual = models.DecimalField(
        'acréscimo sobre o total (%)', max_digits=5, decimal_places=2
    )

    class Meta:
        verbose_name = 'taxa de parcelamento'
        verbose_name_plural = 'taxas de parcelamento'
        ordering = ['parcelas']

    def __str__(self):
        return f'{self.parcelas}x: +{self.acrescimo_percentual}%'

    def clean(self):
        from django.conf import settings
        if self.parcelas is not None and not (2 <= self.parcelas <= settings.MAX_PARCELAS):
            raise ValidationError(
                {'parcelas': f'Use de 2 a {settings.MAX_PARCELAS} parcelas.'}
            )


class Aluno(models.Model):
    """Pessoa que se matriculou. Sem login; identificada pelo CPF."""

    nome = models.CharField('nome', max_length=80)
    sobrenome = models.CharField('sobrenome', max_length=120)
    cpf = models.CharField('CPF', max_length=11, unique=True, help_text='Somente dígitos.')
    email = models.EmailField('email')
    telefone = models.CharField('telefone', max_length=20)
    asaas_customer_id = models.CharField('cliente no Asaas', max_length=60, blank=True)
    criado_em = models.DateTimeField('cadastrado em', auto_now_add=True)

    class Meta:
        verbose_name = 'aluno'
        verbose_name_plural = 'alunos'
        ordering = ['nome', 'sobrenome']

    def __str__(self):
        return f'{self.nome_completo} ({self.cpf_formatado})'

    @property
    def nome_completo(self):
        return f'{self.nome} {self.sobrenome}'.strip()

    @property
    def cpf_formatado(self):
        c = self.cpf
        return f'{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}' if len(c) == 11 else c


def _novo_token():
    return secrets.token_urlsafe(24)


class Matricula(models.Model):
    class Status(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Aguardando pagamento'
        CONFIRMADA = 'CONFIRMADA', 'Confirmada'
        EXPIRADA = 'EXPIRADA', 'Expirada (não paga)'
        RECUSADA = 'RECUSADA', 'Pagamento recusado'
        CANCELADA = 'CANCELADA', 'Cancelada (estornada)'

    class Metodo(models.TextChoices):
        PIX = 'PIX', 'PIX'
        CARTAO = 'CARTAO', 'Cartão de crédito'

    aluno = models.ForeignKey(
        Aluno, on_delete=models.PROTECT, related_name='matriculas', verbose_name='aluno'
    )
    turma = models.ForeignKey(
        'cursos.Turma', on_delete=models.PROTECT, related_name='matriculas', verbose_name='turma'
    )
    status = models.CharField(
        'status', max_length=12, choices=Status.choices, default=Status.PENDENTE
    )
    metodo = models.CharField('forma de pagamento', max_length=8, choices=Metodo.choices)
    parcelas = models.PositiveSmallIntegerField('parcelas', default=1)

    # Valores (congelados no momento da compra)
    valor_original = models.DecimalField('preço da turma', max_digits=10, decimal_places=2)
    desconto_promocao = models.DecimalField(
        'desconto da promoção', max_digits=10, decimal_places=2, default=Decimal('0.00')
    )
    desconto_cupom = models.DecimalField(
        'desconto do cupom', max_digits=10, decimal_places=2, default=Decimal('0.00')
    )
    valor_a_vista = models.DecimalField('valor à vista', max_digits=10, decimal_places=2)
    valor_total = models.DecimalField(
        'valor cobrado', max_digits=10, decimal_places=2,
        help_text='Inclui o acréscimo do parcelamento, quando houver.',
    )
    cupom = models.ForeignKey(
        Cupom, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='matriculas', verbose_name='cupom',
    )
    promocao = models.ForeignKey(
        Promocao, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='matriculas', verbose_name='promoção',
    )

    # Pagamento (Asaas)
    asaas_payment_id = models.CharField('cobrança no Asaas', max_length=60, blank=True, db_index=True)
    asaas_installment_id = models.CharField('parcelamento no Asaas', max_length=60, blank=True)
    pix_copia_cola = models.TextField('PIX copia e cola', blank=True)
    pix_qrcode = models.TextField('QR Code PIX (base64)', blank=True)
    reserva_expira_em = models.DateTimeField('reserva da vaga até', null=True, blank=True)

    # Acompanhamento público (a página consulta o status por este token)
    token = models.CharField(max_length=40, unique=True, default=_novo_token, editable=False)

    termos_aceitos_em = models.DateTimeField('termos aceitos em')
    ip = models.GenericIPAddressField('IP', null=True, blank=True)
    observacao = models.TextField(
        'observação', blank=True, help_text='Motivo de recusa/cancelamento, anotações internas.'
    )
    criada_em = models.DateTimeField('criada em', auto_now_add=True)
    confirmada_em = models.DateTimeField('confirmada em', null=True, blank=True)
    cancelada_em = models.DateTimeField('cancelada em', null=True, blank=True)

    class Meta:
        verbose_name = 'matrícula'
        verbose_name_plural = 'matrículas'
        ordering = ['-criada_em']
        constraints = [
            models.UniqueConstraint(
                fields=['aluno', 'turma'], condition=models.Q(status='CONFIRMADA'),
                name='matricula_confirmada_unica_por_aluno_turma',
            ),
        ]

    def __str__(self):
        return f'{self.aluno.nome_completo} → {self.turma} [{self.get_status_display()}]'

    def reserva_ativa(self, agora=None):
        agora = agora or timezone.now()
        return (
            self.status == self.Status.PENDENTE
            and self.reserva_expira_em is not None
            and self.reserva_expira_em > agora
        )

    @property
    def valor_parcela(self):
        return (self.valor_total / self.parcelas).quantize(Decimal('0.01'))


class VagaQuerySet(models.QuerySet):
    def ocupando(self, agora=None):
        """Vagas de matrículas confirmadas ou com reserva de pagamento válida."""
        agora = agora or timezone.now()
        return self.filter(
            models.Q(matricula__status=Matricula.Status.CONFIRMADA)
            | models.Q(
                matricula__status=Matricula.Status.PENDENTE,
                matricula__reserva_expira_em__gt=agora,
            )
        )


class Vaga(models.Model):
    """Lugar ocupado por uma matrícula na sua turma."""

    matricula = models.ForeignKey(
        Matricula, on_delete=models.CASCADE, related_name='vagas', verbose_name='matrícula'
    )
    turma = models.ForeignKey(
        'cursos.Turma', on_delete=models.PROTECT, related_name='ocupacoes',
        verbose_name='turma',
    )

    objects = VagaQuerySet.as_manager()

    class Meta:
        verbose_name = 'vaga'
        verbose_name_plural = 'vagas'
        constraints = [
            models.UniqueConstraint(fields=['matricula', 'turma'], name='vaga_unica_por_matricula_turma'),
        ]

    def __str__(self):
        return f'{self.turma} — {self.matricula.aluno.nome_completo}'
