from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import ConteudoInstitucional, Depoimento, MembroEquipe
from .serializers import (
    ConteudoInstitucionalSerializer,
    DepoimentoSerializer,
    MembroEquipeSerializer,
)


class ConteudoInstitucionalListView(ListAPIView):
    """Conteúdo institucional ativo, com filtro opcional por seção."""

    permission_classes = (AllowAny,)
    serializer_class = ConteudoInstitucionalSerializer

    def get_queryset(self):
        qs = ConteudoInstitucional.objects.filter(is_ativo=True)
        secao = self.request.query_params.get('secao')
        if secao:
            qs = qs.filter(secao=secao.upper())
        return qs.order_by('secao', 'ordem')


class MembroEquipeListView(ListAPIView):
    """Membros da equipe ativos, ordenados por ``ordem``."""

    permission_classes = (AllowAny,)
    serializer_class = MembroEquipeSerializer
    queryset = MembroEquipe.objects.filter(is_ativo=True).order_by('ordem', 'nome')


class DepoimentoListView(ListAPIView):
    """Depoimentos publicados, ordenados por ``ordem``."""

    permission_classes = (AllowAny,)
    serializer_class = DepoimentoSerializer
    queryset = Depoimento.objects.filter(is_publicado=True).order_by('ordem', 'nome_aluno')
