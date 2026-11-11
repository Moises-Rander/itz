"""Catálogo: Cursos avulsos, Graduações (Módulos → Cursos), Turmas e Professores.

- Curso: uma disciplina (ex.: Hebraico Básico). Existe por si só e pode ser
  vendido avulso; também pode compor várias Graduações.
- Graduação: N Módulos ordenados; cada Módulo tem N Cursos ordenados.
- Turma: oferta de um Curso OU de uma Graduação (exatamente um dos dois).
  A turma de Graduação é um pacote de turmas de curso ("turmas compartilhadas"):
  quem compra a Graduação estuda junto com quem comprou o curso avulso.
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
    """Campos comuns de Curso e Graduação (o que aparece na vitrine)."""

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
    ementa = models.TextField('ementa', blank=True)
    carga_horaria = models.PositiveIntegerField('carga horária (horas)', default=0)

    class Meta(ProdutoBase.Meta):
        verbose_name = 'curso'
        verbose_name_plural = 'cursos'


class Graduacao(ProdutoBase):
    class Meta(ProdutoBase.Meta):
        verbose_name = 'graduação'
        verbose_name_plural = 'graduações'

    def cursos(self):
        """Cursos da grade, na ordem módulo → curso."""
        return Curso.objects.filter(modulos_curso__modulo__graduacao=self).order_by(
            'modulos_curso__modulo__ordem', 'modulos_curso__ordem'
        )

    @property
    def carga_horaria(self):
        return sum(c.carga_horaria for c in self.cursos())


class Modulo(models.Model):
    graduacao = models.ForeignKey(
        Graduacao, on_delete=models.CASCADE, related_name='modulos', verbose_name='graduação'
    )
    nome = models.CharField('nome', max_length=150)
    descricao = models.TextField('descrição', blank=True)
    ordem = models.PositiveIntegerField('ordem', default=1)

    class Meta:
        verbose_name = 'módulo'
        verbose_name_plural = 'módulos'
        ordering = ['graduacao', 'ordem']
        constraints = [
            models.UniqueConstraint(
                fields=['graduacao', 'ordem'], name='modulo_ordem_unica_por_graduacao'
            ),
        ]

    def __str__(self):
        return f'{self.graduacao} — {self.ordem}. {self.nome}'


class ModuloCurso(models.Model):
    """Curso dentro de um Módulo (com a ordem de exibição)."""

    modulo = models.ForeignKey(
        Modulo, on_delete=models.CASCADE, related_name='itens', verbose_name='módulo'
    )
    curso = models.ForeignKey(
        Curso, on_delete=models.PROTECT, related_name='modulos_curso', verbose_name='curso'
    )
    ordem = models.PositiveIntegerField('ordem', default=1)

    class Meta:
        verbose_name = 'curso do módulo'
        verbose_name_plural = 'cursos do módulo'
        ordering = ['modulo', 'ordem']
        constraints = [
            models.UniqueConstraint(fields=['modulo', 'curso'], name='curso_unico_por_modulo'),
        ]

    def __str__(self):
        return f'{self.modulo} → {self.curso}'

    def clean(self):
        # O mesmo curso não pode aparecer em dois módulos da mesma graduação.
        if self.modulo_id and self.curso_id:
            repetido = ModuloCurso.objects.filter(
                modulo__graduacao_id=self.modulo.graduacao_id, curso_id=self.curso_id
            ).exclude(pk=self.pk)
            if repetido.exists():
                raise ValidationError({'curso': 'Este curso já está em outro módulo desta graduação.'})


class Turma(models.Model):
    """Oferta de um Curso OU de uma Graduação.

    - Turma de curso: tem datas, vagas, horários e professores próprios.
    - Turma de graduação: é composta por turmas de curso (uma por curso da
      grade); datas, horários, professores e vagas vêm delas.
    """

    class Status(models.TextChoices):
        RASCUNHO = 'RASCUNHO', 'Rascunho (não aparece no site)'
        PUBLICADA = 'PUBLICADA', 'Publicada'
        FECHADA = 'FECHADA', 'Fechada manualmente'

    curso = models.ForeignKey(
        Curso, on_delete=models.PROTECT, null=True, blank=True,
        related_name='turmas', verbose_name='curso',
    )
    graduacao = models.ForeignKey(
        Graduacao, on_delete=models.PROTECT, null=True, blank=True,
        related_name='turmas', verbose_name='graduação',
    )
    codigo = models.CharField('código', max_length=40, help_text='Ex.: 2027.1')
    status = models.CharField(
        'status', max_length=12, choices=Status.choices, default=Status.RASCUNHO
    )
    preco = models.DecimalField('preço à vista (R$)', max_digits=10, decimal_places=2)

    # --- Só turma de curso ---
    data_inicio = models.DateField('data de início', null=True, blank=True)
    data_fim = models.DateField('data de fim', null=True, blank=True)
    vagas = models.PositiveIntegerField('vagas', null=True, blank=True)
    professores = models.ManyToManyField(
        Professor, blank=True, related_name='turmas', verbose_name='professores'
    )

    # --- Só turma de graduação ---
    turmas_curso = models.ManyToManyField(
        'self', symmetrical=False, blank=True, related_name='turmas_graduacao',
        limit_choices_to={'curso__isnull': False},
        verbose_name='turmas de curso',
        help_text='Uma turma para cada curso da grade da graduação.',
    )

    class Meta:
        verbose_name = 'turma'
        verbose_name_plural = 'turmas'
        ordering = ['-id']
        constraints = [
            models.CheckConstraint(
                name='turma_curso_xor_graduacao',
                condition=(
                    models.Q(curso__isnull=False, graduacao__isnull=True)
                    | models.Q(curso__isnull=True, graduacao__isnull=False)
                ),
            ),
        ]

    def __str__(self):
        return f'{self.produto} — {self.codigo}'

    # ------------------------------------------------------------------ tipo
    @property
    def is_graduacao(self):
        return self.graduacao_id is not None

    @property
    def produto(self):
        return self.graduacao if self.is_graduacao else self.curso

    # ------------------------------------------------------- datas derivadas
    def _componentes(self):
        """Turmas de curso que formam esta turma (ela mesma, se for de curso)."""
        if not self.is_graduacao:
            return [self]
        return list(self.turmas_curso.all())

    @property
    def inicio(self):
        datas = [t.data_inicio for t in self._componentes() if t.data_inicio]
        return min(datas) if datas else None

    @property
    def fim(self):
        datas = [t.data_fim for t in self._componentes() if t.data_fim]
        return max(datas) if datas else None

    def turmas_curso_restantes(self, hoje=None):
        """Turmas de curso ainda não encerradas — onde a matrícula ocupa vaga."""
        hoje = hoje or timezone.localdate()
        return [t for t in self._componentes() if t.data_fim and t.data_fim >= hoje]

    # ----------------------------------------------------------------- vagas
    def vagas_ocupadas(self, agora=None):
        """Vagas desta turma de curso ocupadas por matrículas confirmadas ou
        reservas de pagamento ainda válidas."""
        from matriculas.models import Vaga
        return Vaga.objects.ocupando(agora).filter(turma=self).count()

    def vagas_disponiveis(self, agora=None):
        agora = agora or timezone.now()
        if not self.is_graduacao:
            return max((self.vagas or 0) - self.vagas_ocupadas(agora), 0)
        restantes = self.turmas_curso_restantes(timezone.localdate(agora))
        if not restantes:
            return 0
        return min(t.vagas_disponiveis(agora) for t in restantes)

    # ------------------------------------------------------- disponibilidade
    def grade_completa(self):
        """Turma de graduação: tem exatamente uma turma de curso por curso da grade."""
        if not self.is_graduacao:
            return True
        cursos_grade = set(self.graduacao.cursos().values_list('id', flat=True))
        cursos_turmas = [t.curso_id for t in self.turmas_curso.all()]
        return bool(cursos_grade) and sorted(cursos_turmas) == sorted(cursos_grade)

    def dentro_do_prazo(self, hoje=None):
        """Curso: até o dia de início. Graduação: até a última turma de curso começar."""
        hoje = hoje or timezone.localdate()
        inicios = [t.data_inicio for t in self._componentes() if t.data_inicio]
        return bool(inicios) and hoje <= max(inicios)

    def disponivel(self, agora=None):
        """Pode ser exibida e vendida no site agora?"""
        agora = agora or timezone.now()
        return (
            self.status == self.Status.PUBLICADA
            and self.produto.publicado
            and self.grade_completa()
            and self.dentro_do_prazo(timezone.localdate(agora))
            and self.vagas_disponiveis(agora) > 0
        )

    # ------------------------------------------------------------- validação
    def clean(self):
        if bool(self.curso_id) == bool(self.graduacao_id):
            raise ValidationError('Vincule a turma a exatamente um: Curso OU Graduação.')
        if self.curso_id:
            erros = {}
            if not self.data_inicio:
                erros['data_inicio'] = 'Obrigatória para turma de curso.'
            if not self.data_fim:
                erros['data_fim'] = 'Obrigatória para turma de curso.'
            if self.vagas is None:
                erros['vagas'] = 'Obrigatório para turma de curso.'
            if erros:
                raise ValidationError(erros)
            if self.data_fim < self.data_inicio:
                raise ValidationError({'data_fim': 'A data de fim não pode ser anterior ao início.'})
        else:
            sobra = [
                campo for campo in ('data_inicio', 'data_fim', 'vagas')
                if getattr(self, campo) is not None
            ]
            if sobra:
                raise ValidationError(
                    'Turma de graduação não tem datas nem vagas próprias: '
                    'elas vêm das turmas de curso que a compõem.'
                )


class HorarioAula(models.Model):
    """Dia e horário em que a turma de curso tem aula (presencial, na sede)."""

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


class TurmaGraduacaoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(graduacao__isnull=False)


class TurmaCurso(Turma):
    objects = TurmaCursoManager()

    class Meta:
        proxy = True
        verbose_name = 'turma de curso'
        verbose_name_plural = 'turmas de curso'


class TurmaGraduacao(Turma):
    objects = TurmaGraduacaoManager()

    class Meta:
        proxy = True
        verbose_name = 'turma de graduação'
        verbose_name_plural = 'turmas de graduação'
