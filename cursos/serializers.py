"""Serializers públicos do catálogo (somente leitura)."""
from django.utils import timezone
from rest_framework import serializers

from .models import Curso, Graduacao, Professor, Turma


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
    """Turma disponível, com cronograma, professores e preço."""

    inicio = serializers.DateField(read_only=True)
    fim = serializers.DateField(read_only=True)
    vagas_disponiveis = serializers.SerializerMethodField()
    em_andamento = serializers.SerializerMethodField()
    preco = serializers.SerializerMethodField()
    cronograma = serializers.SerializerMethodField()
    professores = serializers.SerializerMethodField()

    class Meta:
        model = Turma
        fields = (
            'id', 'codigo', 'inicio', 'fim', 'vagas_disponiveis', 'em_andamento',
            'preco', 'cronograma', 'professores',
        )

    def _componentes(self, obj):
        if obj.is_graduacao:
            return sorted(
                obj.turmas_curso.select_related('curso').prefetch_related('horarios', 'professores'),
                key=lambda t: t.data_inicio,
            )
        return [obj]

    def get_vagas_disponiveis(self, obj):
        return obj.vagas_disponiveis()

    def get_em_andamento(self, obj):
        return bool(obj.inicio and obj.inicio < timezone.localdate())

    def get_preco(self, obj):
        return _preco(obj)

    def get_cronograma(self, obj):
        return [
            {
                'curso': t.curso.nome,
                'curso_slug': t.curso.slug,
                'inicio': t.data_inicio,
                'fim': t.data_fim,
                'horarios': [
                    {
                        'dia': h.get_dia_semana_display(),
                        'inicio': h.hora_inicio.strftime('%H:%M'),
                        'fim': h.hora_fim.strftime('%H:%M'),
                    }
                    for h in t.horarios.all()
                ],
                'professores': [p.nome for p in t.professores.all()],
            }
            for t in self._componentes(obj)
        ]

    def get_professores(self, obj):
        vistos = {}
        for t in self._componentes(obj):
            for p in t.professores.all():
                vistos.setdefault(p.pk, p)
        return ProfessorSerializer(vistos.values(), many=True, context=self.context).data


def turmas_disponiveis(produto):
    turmas = produto.turmas.filter(status=Turma.Status.PUBLICADA)
    return sorted((t for t in turmas if t.disponivel()), key=lambda t: t.inicio)


class CatalogoItemSerializer(serializers.Serializer):
    """Card da vitrine — curso avulso ou graduação com turma disponível."""

    def to_representation(self, item):
        produto, turmas = item
        proxima = turmas[0]
        mais_barata = min(turmas, key=lambda t: _preco(t)['valor_a_vista'])
        request = self.context.get('request')
        imagem = produto.imagem.url if produto.imagem else None
        if imagem and request:
            imagem = request.build_absolute_uri(imagem)
        return {
            'tipo': 'graduacao' if isinstance(produto, Graduacao) else 'curso',
            'slug': produto.slug,
            'nome': produto.nome,
            'resumo': produto.resumo,
            'imagem': imagem,
            'carga_horaria': produto.carga_horaria,
            'qtd_cursos': produto.cursos().count() if isinstance(produto, Graduacao) else None,
            'proxima_turma': {'id': proxima.pk, 'codigo': proxima.codigo, 'inicio': proxima.inicio},
            'qtd_turmas': len(turmas),
            'preco': _preco(mais_barata),
        }


class CursoDetalheSerializer(serializers.ModelSerializer):
    turmas = serializers.SerializerMethodField()
    graduacoes = serializers.SerializerMethodField()

    class Meta:
        model = Curso
        fields = (
            'slug', 'nome', 'resumo', 'descricao', 'ementa', 'carga_horaria', 'imagem',
            'turmas', 'graduacoes',
        )

    def get_turmas(self, obj):
        return TurmaSerializer(turmas_disponiveis(obj), many=True, context=self.context).data

    def get_graduacoes(self, obj):
        """Graduações publicadas que incluem este curso (vitrine cruzada)."""
        qs = Graduacao.objects.filter(publicado=True, modulos__itens__curso=obj).distinct()
        return [{'slug': g.slug, 'nome': g.nome, 'resumo': g.resumo} for g in qs]


class GraduacaoDetalheSerializer(serializers.ModelSerializer):
    carga_horaria = serializers.IntegerField(read_only=True)
    modulos = serializers.SerializerMethodField()
    turmas = serializers.SerializerMethodField()

    class Meta:
        model = Graduacao
        fields = (
            'slug', 'nome', 'resumo', 'descricao', 'carga_horaria', 'imagem',
            'modulos', 'turmas',
        )

    def get_modulos(self, obj):
        return [
            {
                'ordem': m.ordem,
                'nome': m.nome,
                'descricao': m.descricao,
                'cursos': [
                    {
                        'slug': i.curso.slug, 'nome': i.curso.nome,
                        'resumo': i.curso.resumo, 'carga_horaria': i.curso.carga_horaria,
                    }
                    for i in m.itens.select_related('curso')
                ],
            }
            for m in obj.modulos.prefetch_related('itens__curso')
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
            'tipo': 'graduacao' if obj.is_graduacao else 'curso',
            'slug': p.slug, 'nome': p.nome, 'carga_horaria': p.carga_horaria,
        }
