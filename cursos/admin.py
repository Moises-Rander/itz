from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Aula,
    Curso,
    Formacao,
    HorarioAula,
    Modulo,
    Professor,
    TurmaCurso,
    TurmaFormacao,
)


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'titulacao', 'exibir_na_home', 'ordem')
    list_editable = ('exibir_na_home', 'ordem')
    list_filter = ('exibir_na_home',)
    search_fields = ('nome', 'titulacao', 'bio')


PRODUTO_FIELDS = ('nome', 'slug', 'resumo', 'descricao', 'carga_horaria', 'imagem', 'publicado')


class AulaInline(admin.TabularInline):
    model = Aula
    extra = 1
    fields = ('ordem', 'nome')


class AulaCursoInline(AulaInline):
    fk_name = 'curso'
    exclude = ('modulo',)


class AulaModuloInline(AulaInline):
    fk_name = 'modulo'
    exclude = ('curso',)


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'carga_horaria', 'qtd_aulas', 'publicado')
    list_filter = ('publicado',)
    list_editable = ('publicado',)
    search_fields = ('nome', 'resumo', 'descricao')
    prepopulated_fields = {'slug': ('nome',)}
    fields = PRODUTO_FIELDS
    inlines = (AulaCursoInline,)

    @admin.display(description='aulas')
    def qtd_aulas(self, obj):
        return obj.aulas.count()


class ModuloInline(admin.TabularInline):
    model = Modulo
    extra = 1
    fields = ('ordem', 'nome', 'aulas_do_modulo')
    readonly_fields = ('aulas_do_modulo',)

    @admin.display(description='aulas')
    def aulas_do_modulo(self, obj):
        if not obj.pk:
            return 'Salve para adicionar aulas.'
        nomes = [a.nome for a in obj.aulas.all()]
        link = reverse('admin:cursos_modulo_change', args=[obj.pk])
        return format_html('{} — <a href="{}">editar aulas</a>', ', '.join(nomes) or 'nenhuma', link)


@admin.register(Formacao)
class FormacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'qtd_modulos', 'carga_horaria', 'publicado')
    list_filter = ('publicado',)
    list_editable = ('publicado',)
    search_fields = ('nome', 'resumo', 'descricao')
    prepopulated_fields = {'slug': ('nome',)}
    fields = PRODUTO_FIELDS
    inlines = (ModuloInline,)

    @admin.display(description='módulos')
    def qtd_modulos(self, obj):
        return obj.modulos.count()


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ('formacao', 'ordem', 'nome')
    list_filter = ('formacao',)
    search_fields = ('nome', 'formacao__nome')
    fields = ('formacao', 'ordem', 'nome')
    inlines = (AulaModuloInline,)

    def get_model_perms(self, request):
        # Editado a partir da Formação; não aparece solto no menu.
        return {}


# ---------------------------------------------------------------- Turmas


class HorarioAulaInline(admin.TabularInline):
    model = HorarioAula
    extra = 1


class TurmaAdminBase(admin.ModelAdmin):
    """Telas de turma de curso e de formação: mesmos campos, muda o produto."""

    produto = None  # 'curso' ou 'formacao'
    list_filter = ('status',)
    filter_horizontal = ('professores',)
    inlines = (HorarioAulaInline,)

    def get_list_display(self, request):
        return (
            self.produto, 'codigo', 'status', 'data_inicio', 'data_fim', 'preco',
            'vagas', 'vagas_col', 'no_site',
        )

    def get_list_filter(self, request):
        return ('status', self.produto)

    def get_search_fields(self, request):
        return ('codigo', f'{self.produto}__nome')

    def get_autocomplete_fields(self, request):
        return (self.produto,)

    def get_fields(self, request, obj=None):
        return (
            self.produto, 'codigo', 'status', 'preco', ('data_inicio', 'data_fim'),
            'vagas', 'professores',
        )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        for campo in (self.produto, 'data_inicio', 'data_fim', 'vagas'):
            form.base_fields[campo].required = True
        return form

    @admin.display(description='vagas livres')
    def vagas_col(self, obj):
        return obj.vagas_disponiveis()

    @admin.display(description='no site?', boolean=True)
    def no_site(self, obj):
        return obj.disponivel()


@admin.register(TurmaCurso)
class TurmaCursoAdmin(TurmaAdminBase):
    produto = 'curso'


@admin.register(TurmaFormacao)
class TurmaFormacaoAdmin(TurmaAdminBase):
    produto = 'formacao'
