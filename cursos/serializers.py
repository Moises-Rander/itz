"""Serializers públicos do catálogo (somente leitura)."""
from rest_framework import serializers

from .models import Curso, Formacao, Professor, Turma


class ProfessorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professor
        fields = ('id', 'nome', 'titulacao', 'bio', 'foto')


def _preco(turma):
    """Preço com a promoção vigente + a maior opção de parcelamento."""
    from matriculas.services import calcular_preco, opcoes_parcelamento
    p = calcular_preco(turma)
    maior = opcoes_parcelamento(p['valor_a_vista'])[-1]
    return {
        'valor_original': str(p['valor_original']),
        'desconto_promocao': str(p['desconto_promocao']),
        'valor_a_vista': str(p['valor_a_vista']),
        'promocao': p['promocao'].nome if p['promocao'] else None,
        'parcelamento': {
            'parcelas': maior['parcelas'],
            'valor_parcela': str(maior['valor_parcela']),
            'valor_total': str(maior['valor_total']),
            'com_juros': maior['com_juros'],
        },
    }


class TurmaSerializer(serializers.ModelSerializer):
    """Turma disponível, com horários, professores e preço."""

    inicio = serializers.DateField(read_only=True)
    fim = serializers.DateField(read_only=True)
    vagas_disponiveis = serializers.SerializerMethodField()
    preco = serializers.SerializerMethodField()
    horarios = serializers.SerializerMethodField()
    professores = serializers.SerializerMethodField()

    class Meta:
        model = Turma
        fields = (
            'id', 'codigo', 'inicio', 'fim', 'vagas_disponiveis', 'preco', 'horarios',
            'professores',
        )

    def get_vagas_disponiveis(self, obj):
        return obj.vagas_disponiveis()

    def get_preco(self, obj):
        return _preco(obj)

    def get_horarios(self, obj):
        return [
            {
                'dia': h.get_dia_semana_display(),
                'inicio': h.hora_inicio.strftime('%H:%M'),
                'fim': h.hora_fim.strftime('%H:%M'),
            }
            for h in obj.horarios.all()
        ]

    def get_professores(self, obj):
        return ProfessorSerializer(obj.professores.all(), many=True, context=self.context).data


def turmas_disponiveis(produto):
    turmas = produto.turmas.filter(status=Turma.Status.PUBLICADA).prefetch_related(
        'horarios', 'professores'
    )
    return sorted((t for t in turmas if t.disponivel()), key=lambda t: t.inicio)


class CatalogoItemSerializer(serializers.Serializer):
    """Card da vitrine — curso avulso ou formação com turma disponível."""

    def to_representation(self, item):
        produto, turmas = item
        proxima = turmas[0]
        mais_barata = min(turmas, key=lambda t: _preco(t)['valor_a_vista'])
        request = self.context.get('request')
        imagem = produto.imagem.url if produto.imagem else None
        if imagem and request:
            imagem = request.build_absolute_uri(imagem)
        return {
            'tipo': 'formacao' if isinstance(produto, Formacao) else 'curso',
            'slug': produto.slug,
            'nome': produto.nome,
            'resumo': produto.resumo,
            'imagem': imagem,
            'carga_horaria': produto.carga_horaria,
            'qtd_modulos': produto.modulos.count() if isinstance(produto, Formacao) else None,
            'proxima_turma': {'id': proxima.pk, 'codigo': proxima.codigo, 'inicio': proxima.inicio},
            'qtd_turmas': len(turmas),
            'preco': _preco(mais_barata),
        }


class CursoDetalheSerializer(serializers.ModelSerializer):
    aulas = serializers.SerializerMethodField()
    turmas = serializers.SerializerMethodField()

    class Meta:
        model = Curso
        fields = (
            'slug', 'nome', 'resumo', 'descricao', 'carga_horaria', 'imagem', 'aulas', 'turmas',
        )

    def get_aulas(self, obj):
        return [{'ordem': a.ordem, 'nome': a.nome} for a in obj.aulas.all()]

    def get_turmas(self, obj):
        return TurmaSerializer(turmas_disponiveis(obj), many=True, context=self.context).data


class FormacaoDetalheSerializer(serializers.ModelSerializer):
    modulos = serializers.SerializerMethodField()
    turmas = serializers.SerializerMethodField()

    class Meta:
        model = Formacao
        fields = (
            'slug', 'nome', 'resumo', 'descricao', 'carga_horaria', 'imagem',
            'modulos', 'turmas',
        )

    def get_modulos(self, obj):
        return [
            {
                'ordem': m.ordem,
                'nome': m.nome,
                'aulas': [{'ordem': a.ordem, 'nome': a.nome} for a in m.aulas.all()],
            }
            for m in obj.modulos.prefetch_related('aulas')
        ]

    def get_turmas(self, obj):
        return TurmaSerializer(turmas_disponiveis(obj), many=True, context=self.context).data


class TurmaCheckoutSerializer(TurmaSerializer):
    """Turma vista no checkout: inclui o produto ao qual pertence."""

    produto = serializers.SerializerMethodField()

    class Meta(TurmaSerializer.Meta):
        fields = TurmaSerializer.Meta.fields + ('produto',)

    def get_produto(self, obj):
        p = obj.produto
        return {
            'tipo': 'formacao' if obj.is_formacao else 'curso',
            'slug': p.slug, 'nome': p.nome, 'carga_horaria': p.carga_horaria,
        }
