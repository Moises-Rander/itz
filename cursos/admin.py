from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from .models import (
    Curso,
    Graduacao,
    HorarioAula,
    Modulo,
    ModuloCurso,
    Professor,
    Turma,
    TurmaCurso,
    TurmaGraduacao,
)


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'titulacao', 'exibir_na_home', 'ordem')
    list_editable = ('exibir_na_home', 'ordem')
    list_filter = ('exibir_na_home',)
    search_fields = ('nome', 'titulacao', 'bio')


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'carga_horaria', 'publicado', 'graduacoes')
    list_filter = ('publicado',)
    list_editable = ('publicado',)
    search_fields = ('nome', 'resumo', 'descricao')
    prepopulated_fields = {'slug': ('nome',)}
    fields = ('nome', 'slug', 'resumo', 'descricao', 'ementa', 'carga_horaria', 'imagem', 'publicado')

    @admin.display(description='faz parte de')
    def graduacoes(self, obj):
        nomes = Graduacao.objects.filter(
            modulos__itens__curso=obj
        ).distinct().values_list('nome', flat=True)
        return ', '.join(nomes) or '— (só avulso)'


class ModuloInline(admin.TabularInline):
    model = Modulo
    extra = 1
    fields = ('ordem', 'nome', 'descricao', 'cursos_do_modulo')
    readonly_fields = ('cursos_do_modulo',)
    show_change_link = True

    @admin.display(description='cursos')
    def cursos_do_modulo(self, obj):
        if not obj.pk:
            return 'Salve para adicionar cursos.'
        nomes = [i.curso.nome for i in obj.itens.select_related('curso')]
        link = reverse('admin:cursos_modulo_change', args=[obj.pk])
        return format_html('{} — <a href="{}">editar cursos</a>', ', '.join(nomes) or 'nenhum', link)


@admin.register(Graduacao)
class GraduacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'qtd_modulos', 'carga_horaria', 'publicado')
    list_filter = ('publicado',)
    list_editable = ('publicado',)
    search_fields = ('nome', 'resumo', 'descricao')
    prepopulated_fields = {'slug': ('nome',)}
    fields = ('nome', 'slug', 'resumo', 'descricao', 'imagem', 'publicado', 'carga_horaria')
    readonly_fields = ('carga_horaria',)
    inlines = (ModuloInline,)

    @admin.display(description='módulos')
    def qtd_modulos(self, obj):
        return obj.modulos.count()

    @admin.display(description='carga horária total (h)')
    def carga_horaria(self, obj):
        return obj.carga_horaria if obj.pk else '—'


class ModuloCursoInline(admin.TabularInline):
    model = ModuloCurso
    extra = 1
    fields = ('ordem', 'curso')
    autocomplete_fields = ('curso',)


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ('graduacao', 'ordem', 'nome')
    list_filter = ('graduacao',)
    search_fields = ('nome', 'graduacao__nome')
    inlines = (ModuloCursoInline,)

    def get_model_perms(self, request):
        # Editado a partir da Graduação; não aparece solto no menu.
        return {}


# ---------------------------------------------------------------- Turmas


class SituacaoMixin:
    """Colunas de situação (calculadas) comuns às duas telas de turma."""

    @admin.display(description='início')
    def inicio_col(self, obj):
        return obj.inicio

    @admin.display(description='fim')
    def fim_col(self, obj):
        return obj.fim

    @admin.display(description='vagas livres')
    def vagas_col(self, obj):
        return obj.vagas_disponiveis()

    @admin.display(description='no site?', boolean=True)
    def no_site(self, obj):
        return obj.disponivel()


class HorarioAulaInline(admin.TabularInline):
    model = HorarioAula
    extra = 1


@admin.register(TurmaCurso)
class TurmaCursoAdmin(SituacaoMixin, admin.ModelAdmin):
    list_display = (
        'curso', 'codigo', 'status', 'data_inicio', 'data_fim', 'preco',
        'vagas', 'vagas_col', 'no_site',
    )
    list_filter = ('status', 'curso')
    search_fields = ('codigo', 'curso__nome')
    autocomplete_fields = ('curso',)
    filter_horizontal = ('professores',)
    fields = (
        'curso', 'codigo', 'status', 'preco', ('data_inicio', 'data_fim'), 'vagas',
        'professores', 'faz_parte_de',
    )
    readonly_fields = ('faz_parte_de',)
    inlines = (HorarioAulaInline,)

    @admin.display(description='usada nas turmas de graduação')
    def faz_parte_de(self, obj):
        if not obj.pk:
            return '—'
        return ', '.join(str(t) for t in obj.turmas_graduacao.all()) or '—'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['curso'].required = True
        for campo in ('data_inicio', 'data_fim', 'vagas'):
            form.base_fields[campo].required = True
        return form


class TurmaGraduacaoForm(forms.ModelForm):
    class Meta:
        model = TurmaGraduacao
        fields = ('graduacao', 'codigo', 'status', 'preco', 'turmas_curso')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['graduacao'].required = True
        self.fields['turmas_curso'].queryset = (
            Turma.objects.filter(curso__isnull=False).select_related('curso')
            .order_by('curso__nome', '-data_inicio')
        )

    def clean(self):
        dados = super().clean()
        graduacao = dados.get('graduacao')
        turmas = list(dados.get('turmas_curso') or [])
        if not graduacao:
            return dados
        grade = {c.pk: c for c in graduacao.cursos()}
        if not grade:
            raise forms.ValidationError('Esta graduação ainda não tem cursos na grade.')
        por_curso = {}
        for t in turmas:
            if t.curso_id not in grade:
                raise forms.ValidationError(
                    f'A turma "{t}" é de um curso que não está na grade de {graduacao}.'
                )
            if t.curso_id in por_curso:
                raise forms.ValidationError(
                    f'Escolha só uma turma de "{t.curso.nome}" (há duas selecionadas).'
                )
            por_curso[t.curso_id] = t
        faltando = [c.nome for pk, c in grade.items() if pk not in por_curso]
        if faltando and dados.get('status') == Turma.Status.PUBLICADA:
            raise forms.ValidationError(
                'Para publicar, inclua uma turma de cada curso da grade. Faltando: '
                + ', '.join(faltando)
            )
        return dados


@admin.register(TurmaGraduacao)
class TurmaGraduacaoAdmin(SituacaoMixin, admin.ModelAdmin):
    form = TurmaGraduacaoForm
    list_display = ('graduacao', 'codigo', 'status', 'inicio_col', 'fim_col', 'preco', 'vagas_col', 'no_site')
    list_filter = ('status', 'graduacao')
    search_fields = ('codigo', 'graduacao__nome')
    autocomplete_fields = ('graduacao',)
    filter_horizontal = ('turmas_curso',)
    readonly_fields = ('cronograma',)

    def get_fields(self, request, obj=None):
        campos = ['graduacao', 'codigo', 'status', 'preco', 'turmas_curso']
        return campos + ['cronograma'] if obj else campos

    @admin.display(description='cronograma (das turmas de curso)')
    def cronograma(self, obj):
        linhas = sorted(
            obj.turmas_curso.select_related('curso').prefetch_related('horarios', 'professores'),
            key=lambda t: t.data_inicio,
        )
        return format_html(
            '<table><tr><th>Curso</th><th>Período</th><th>Horários</th>'
            '<th>Professores</th><th>Vagas livres</th></tr>{}</table>',
            format_html_join('', '<tr><td>{}</td><td>{:%d/%m/%Y} – {:%d/%m/%Y}</td><td>{}</td><td>{}</td><td>{}</td></tr>', (
                (t.curso.nome, t.data_inicio, t.data_fim,
                 ', '.join(map(str, t.horarios.all())) or '—',
                 ', '.join(p.nome for p in t.professores.all()) or '—',
                 t.vagas_disponiveis())
                for t in linhas
            )),
        )
