from django.conf import settings
from django.contrib import admin, messages
from django.utils.html import format_html

from .asaas import AsaasError
from .models import Aluno, Cupom, Matricula, Promocao, TaxaParcelamento, Vaga
from .services import cancelar_e_estornar, confirmar_matricula


class SomenteLeituraInline(admin.TabularInline):
    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class MatriculaDoAlunoInline(SomenteLeituraInline):
    model = Matricula
    fields = ('turma', 'status', 'metodo', 'valor_total', 'criada_em')
    readonly_fields = fields


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'cpf_formatado', 'email', 'telefone', 'criado_em')
    search_fields = ('nome', 'sobrenome', 'cpf', 'email', 'telefone')
    readonly_fields = ('asaas_customer_id', 'criado_em')
    inlines = (MatriculaDoAlunoInline,)

    @admin.display(description='nome', ordering='nome')
    def nome_completo(self, obj):
        return obj.nome_completo

    @admin.display(description='CPF', ordering='cpf')
    def cpf_formatado(self, obj):
        return obj.cpf_formatado


class VagaInline(SomenteLeituraInline):
    model = Vaga
    fields = ('turma',)
    readonly_fields = fields
    verbose_name_plural = 'vagas ocupadas'


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'aluno', 'turma', 'status_col', 'metodo', 'parcelas', 'valor_total', 'criada_em',
    )
    list_display_links = ('id', 'aluno')
    list_filter = ('status', 'metodo', 'turma__curso', 'turma__formacao')
    search_fields = (
        'aluno__nome', 'aluno__sobrenome', 'aluno__cpf', 'aluno__email', 'asaas_payment_id',
    )
    date_hierarchy = 'criada_em'
    inlines = (VagaInline,)
    actions = ('cancelar_estornar',)
    fieldsets = (
        (None, {'fields': ('aluno', 'turma', 'status', 'observacao')}),
        ('Valores', {'fields': (
            'valor_original', 'promocao', 'desconto_promocao', 'cupom', 'desconto_cupom',
            'valor_a_vista', 'metodo', 'parcelas', 'valor_total',
        )}),
        ('Pagamento (Asaas)', {'fields': (
            'asaas_payment_id', 'asaas_installment_id', 'reserva_expira_em',
        )}),
        ('Registro', {'fields': (
            'termos_aceitos_em', 'ip', 'criada_em', 'confirmada_em', 'cancelada_em',
        )}),
    )

    def get_readonly_fields(self, request, obj=None):
        # Tudo vem do checkout/Asaas; só a observação é editável à mão.
        return [f.name for f in Matricula._meta.fields if f.name != 'observacao']

    def has_add_permission(self, request):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if settings.ASAAS_FAKE:
            actions['simular_pagamento'] = self.get_action('simular_pagamento')
        return actions

    @admin.display(description='status', ordering='status')
    def status_col(self, obj):
        cores = {
            Matricula.Status.CONFIRMADA: '#15803d', Matricula.Status.PENDENTE: '#b45309',
            Matricula.Status.CANCELADA: '#b91c1c', Matricula.Status.RECUSADA: '#b91c1c',
        }
        rotulo = obj.get_status_display()
        if obj.status == Matricula.Status.PENDENTE and not obj.reserva_ativa():
            rotulo = 'Expirada (não paga)'
        return format_html('<b style="color:{}">{}</b>', cores.get(obj.status, '#666'), rotulo)

    @admin.action(description='Cancelar e estornar (libera as vagas)')
    def cancelar_estornar(self, request, queryset):
        feitas = 0
        for m in queryset:
            try:
                cancelar_e_estornar(m, motivo=f'Cancelada por {request.user.email}.')
                feitas += 1
            except (ValueError, AsaasError) as exc:
                self.message_user(request, f'#{m.pk}: {exc}', level=messages.WARNING)
        if feitas:
            self.message_user(request, f'{feitas} matrícula(s) cancelada(s) e estornada(s).')

    @admin.action(description='[Modo simulado] Marcar pagamento como recebido')
    def simular_pagamento(self, request, queryset):
        feitas = sum(1 for m in queryset if confirmar_matricula(m))
        self.message_user(request, f'{feitas} matrícula(s) confirmada(s) (simulação).')


@admin.register(Cupom)
class CupomAdmin(admin.ModelAdmin):
    list_display = (
        'codigo', 'tipo_desconto', 'valor_desconto', 'restrito_a', 'data_inicio', 'data_fim',
        'usos_atuais', 'max_usos', 'is_ativo',
    )
    list_filter = ('tipo_desconto', 'is_ativo')
    search_fields = ('codigo',)
    readonly_fields = ('usos_atuais',)
    autocomplete_fields = ('curso', 'formacao')
    fieldsets = (
        (None, {'fields': (
            'codigo', 'tipo_desconto', 'valor_desconto', ('data_inicio', 'data_fim'),
            'max_usos', 'usos_atuais', 'is_ativo',
        )}),
        ('Restringir a (opcional — preencha no máximo um)', {
            'fields': ('turma', 'curso', 'formacao'),
        }),
    )

    @admin.display(description='vale para')
    def restrito_a(self, obj):
        return obj.turma or obj.curso or obj.formacao or 'Tudo'


@admin.register(Promocao)
class PromocaoAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 'tipo_desconto', 'valor', 'restrito_a', 'data_inicio', 'data_fim', 'is_ativa',
    )
    list_filter = ('tipo_desconto', 'is_ativa')
    autocomplete_fields = ('curso', 'formacao')
    fieldsets = (
        (None, {'fields': (
            'nome', 'tipo_desconto', 'valor', ('data_inicio', 'data_fim'), 'is_ativa',
        )}),
        ('Restringir a (opcional — preencha no máximo um)', {
            'fields': ('turma', 'curso', 'formacao'),
        }),
    )

    @admin.display(description='vale para')
    def restrito_a(self, obj):
        return obj.turma or obj.curso or obj.formacao or 'Tudo'


@admin.register(TaxaParcelamento)
class TaxaParcelamentoAdmin(admin.ModelAdmin):
    list_display = ('parcelas', 'acrescimo_percentual')
    list_editable = ('acrescimo_percentual',)
