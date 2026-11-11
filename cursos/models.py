"""Catálogo: Cursos, Formações, Aulas, Turmas e Professores.

- Aula: a menor unidade (só o nome). Pertence a um Curso OU a um Módulo.
- Curso: N aulas ordenadas. Vendido avulso.
- Formação: N Módulos ordenados; cada Módulo tem N aulas ordenadas.
- Turma: oferta de um Curso OU de uma Formação (exatamente um dos dois), com
  datas, vagas, horários e professores próprios.
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


def _slug_unico(instancia, origem):
    base = slugify(origem)[:200] or 'item'
    slug, n = base, 2
    modelo = type(instancia)
    while modelo.objects.filter(slug=slug).exclude(pk=instancia.pk).exists():
        slug = f'{base}-{n}'
        n += 1
    return slug


class Professor(models.Model):
    """Professor exibido no site (sem conta de acesso)."""

    nome = models.CharField('nome', max_length=150)
    titulacao = models.CharField('titulação', max_length=150, blank=True)
    bio = models.TextField('bio', blank=True)
    foto = models.ImageField('foto', upload_to='professores/', null=True, blank=True)
    exibir_na_home = models.BooleanField('exibir na home', default=False)
    ordem = models.PositiveIntegerField('ordem', default=0)

    class Meta:
        verbose_name = 'professor'
        verbose_name_plural = 'professores'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome


class ProdutoBase(models.Model):
    """Campos comuns de Curso e Formação (o que aparece na vitrine)."""

    nome = models.CharField('nome', max_length=150)
    slug = models.SlugField(
        'endereço na URL', max_length=220, unique=True, blank=True,
        help_text='Gerado a partir do nome se ficar em branco.',
    )
    resumo = models.CharField(
        'resumo', max_length=300, blank=True, help_text='Texto curto exibido no card.'
    )
    descricao = models.TextField('descrição', blank=True)
    imagem = models.ImageField('imagem', upload_to='catalogo/', null=True, blank=True)
    carga_horaria = models.PositiveIntegerField('carga horária (horas)', default=0)
    publicado = models.BooleanField(
        'publicado', default=True,
        help_text='Desmarque para esconder do site mesmo com turmas abertas.',
    )

    class Meta:
        abstract = True
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _slug_unico(self, self.nome)
        super().save(*args, **kwargs)


class Curso(ProdutoBase):
    class Meta(ProdutoBase.Meta):
        verbose_name = 'curso'
        verbose_name_plural = 'cursos'


class Formacao(ProdutoBase):
    class Meta(ProdutoBase.Meta):
        verbose_name = 'formação'
        verbose_name_plural = 'formações'

    def qtd_aulas(self):
        return Aula.objects.filter(modulo__formacao=self).count()


class Modulo(models.Model):
    formacao = models.ForeignKey(
        Formacao, on_delete=models.CASCADE, related_name='modulos', verbose_name='formação'
    )
    nome = models.CharField('nome', max_length=150)
    ordem = models.PositiveIntegerField('ordem', default=1)

    class Meta:
        verbose_name = 'módulo'
        verbose_name_plural = 'módulos'
        ordering = ['formacao', 'ordem']
        constraints = [
            models.UniqueConstraint(
                fields=['formacao', 'ordem'], name='modulo_ordem_unica_por_formacao'
            ),
        ]

    def __str__(self):
        return f'{self.formacao} — {self.ordem}. {self.nome}'


class Aula(models.Model):
    """Aula de um Curso OU de um Módulo de formação."""

    curso = models.ForeignKey(
        Curso, on_delete=models.CASCADE, null=True, blank=True,
        related_name='aulas', verbose_name='curso',
    )
    modulo = models.ForeignKey(
        Modulo, on_delete=models.CASCADE, null=True, blank=True,
        related_name='aulas', verbose_name='módulo',
    )
    nome = models.CharField('nome', max_length=200)
    ordem = models.PositiveIntegerField('ordem', default=1)

    class Meta:
        verbose_name = 'aula'
        verbose_name_plural = 'aulas'
        ordering = ['ordem', 'id']
        constraints = [
            models.CheckConstraint(
                name='aula_curso_xor_modulo',
                condition=(
                    models.Q(curso__isnull=False, modulo__isnull=True)
                    | models.Q(curso__isnull=True, modulo__isnull=False)
                ),
            ),
        ]

    def __str__(self):
        return self.nome


class Turma(models.Model):
    """Oferta de um Curso OU de uma Formação, com datas, vagas, horários e
    professores próprios."""

    class Status(models.TextChoices):
        RASCUNHO = 'RASCUNHO', 'Rascunho (não aparece no site)'
        PUBLICADA = 'PUBLICADA', 'Publicada'
        FECHADA = 'FECHADA', 'Fechada manualmente'

    curso = models.ForeignKey(
        Curso, on_delete=models.PROTECT, null=True, blank=True,
        related_name='turmas', verbose_name='curso',
    )
    formacao = models.ForeignKey(
        Formacao, on_delete=models.PROTECT, null=True, blank=True,
        related_name='turmas', verbose_name='formação',
    )
    codigo = models.CharField('código', max_length=40, help_text='Ex.: 2027.1')
    status = models.CharField(
        'status', max_length=12, choices=Status.choices, default=Status.RASCUNHO
    )
    preco = models.DecimalField('preço à vista (R$)', max_digits=10, decimal_places=2)
    data_inicio = models.DateField('data de início', null=True, blank=True)
    data_fim = models.DateField('data de fim', null=True, blank=True)
    vagas = models.PositiveIntegerField('vagas', null=True, blank=True)
    professores = models.ManyToManyField(
        Professor, blank=True, related_name='turmas', verbose_name='professores'
    )

    class Meta:
        verbose_name = 'turma'
        verbose_name_plural = 'turmas'
        ordering = ['-id']
        constraints = [
            models.CheckConstraint(
                name='turma_curso_xor_formacao',
                condition=(
                    models.Q(curso__isnull=False, formacao__isnull=True)
                    | models.Q(curso__isnull=True, formacao__isnull=False)
                ),
            ),
        ]

    def __str__(self):
        return f'{self.produto} — {self.codigo}'

    # ------------------------------------------------------------------ tipo
    @property
    def is_formacao(self):
        return self.formacao_id is not None

    @property
    def produto(self):
        return self.formacao if self.is_formacao else self.curso

    @property
    def inicio(self):
        return self.data_inicio

    @property
    def fim(self):
        return self.data_fim

    # ----------------------------------------------------------------- vagas
    def vagas_ocupadas(self, agora=None):
        """Vagas ocupadas por matrículas confirmadas ou reservas de pagamento
        ainda válidas."""
        from matriculas.models import Vaga
        return Vaga.objects.ocupando(agora).filter(turma=self).count()

    def vagas_disponiveis(self, agora=None):
        return max((self.vagas or 0) - self.vagas_ocupadas(agora), 0)

    # ------------------------------------------------------- disponibilidade
    def dentro_do_prazo(self, hoje=None):
        """Matrícula aberta até o dia de início."""
        hoje = hoje or timezone.localdate()
        return bool(self.data_inicio) and hoje <= self.data_inicio

    def disponivel(self, agora=None):
        """Pode ser exibida e vendida no site agora?"""
        agora = agora or timezone.now()
        return (
            self.status == self.Status.PUBLICADA
            and self.produto.publicado
            and self.dentro_do_prazo(timezone.localdate(agora))
            and self.vagas_disponiveis(agora) > 0
        )

    # ------------------------------------------------------------- validação
    def clean(self):
        if bool(self.curso_id) == bool(self.formacao_id):
            raise ValidationError('Vincule a turma a exatamente um: Curso OU Formação.')
        erros = {}
        if not self.data_inicio:
            erros['data_inicio'] = 'Obrigatória.'
        if not self.data_fim:
            erros['data_fim'] = 'Obrigatória.'
        if self.vagas is None:
            erros['vagas'] = 'Obrigatório.'
        if erros:
            raise ValidationError(erros)
        if self.data_fim < self.data_inicio:
            raise ValidationError({'data_fim': 'A data de fim não pode ser anterior ao início.'})


class HorarioAula(models.Model):
    """Dia e horário em que a turma tem aula (presencial, na sede)."""

    class DiaSemana(models.IntegerChoices):  # inteiro para ordenar seg → dom
        SEG = 1, 'Segunda-feira'
        TER = 2, 'Terça-feira'
        QUA = 3, 'Quarta-feira'
        QUI = 4, 'Quinta-feira'
        SEX = 5, 'Sexta-feira'
        SAB = 6, 'Sábado'
        DOM = 7, 'Domingo'

    turma = models.ForeignKey(
        Turma, on_delete=models.CASCADE, related_name='horarios', verbose_name='turma'
    )
    dia_semana = models.PositiveSmallIntegerField('dia da semana', choices=DiaSemana.choices)
    hora_inicio = models.TimeField('início')
    hora_fim = models.TimeField('fim')

    class Meta:
        verbose_name = 'horário de aula'
        verbose_name_plural = 'horários de aula'
        ordering = ['turma', 'dia_semana', 'hora_inicio']

    def __str__(self):
        return f'{self.get_dia_semana_display()} {self.hora_inicio:%H:%M}–{self.hora_fim:%H:%M}'

    def clean(self):
        if self.hora_inicio and self.hora_fim and self.hora_fim <= self.hora_inicio:
            raise ValidationError({'hora_fim': 'O fim deve ser depois do início.'})


# Proxies: duas telas no Admin, cada uma só com os campos do seu tipo.
class TurmaCursoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(curso__isnull=False)


class TurmaFormacaoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(formacao__isnull=False)


class TurmaCurso(Turma):
    objects = TurmaCursoManager()

    class Meta:
        proxy = True
        verbose_name = 'turma de curso'
        verbose_name_plural = 'turmas de curso'


class TurmaFormacao(Turma):
    objects = TurmaFormacaoManager()

    class Meta:
        proxy = True
        verbose_name = 'turma de formação'
        verbose_name_plural = 'turmas de formação'
