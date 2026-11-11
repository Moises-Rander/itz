from django.contrib import admin

from .models import ConteudoInstitucional, Depoimento, MembroEquipe


@admin.register(ConteudoInstitucional)
class ConteudoInstitucionalAdmin(admin.ModelAdmin):
    list_display = ('secao', 'titulo', 'ordem', 'is_ativo')
    list_filter = ('secao', 'is_ativo')
    search_fields = ('titulo', 'texto')
    list_editable = ('ordem', 'is_ativo')


@admin.register(MembroEquipe)
class MembroEquipeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cargo', 'ordem', 'is_ativo')
    list_filter = ('is_ativo',)
    search_fields = ('nome', 'cargo', 'bio')
    list_editable = ('ordem', 'is_ativo')


@admin.register(Depoimento)
class DepoimentoAdmin(admin.ModelAdmin):
    list_display = ('nome_aluno', 'nome_curso', 'ordem', 'is_publicado')
    list_filter = ('is_publicado',)
    search_fields = ('nome_aluno', 'nome_curso', 'texto')
    list_editable = ('ordem', 'is_publicado')
