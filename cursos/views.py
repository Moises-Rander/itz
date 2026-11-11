from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Curso, Graduacao, Professor, Turma
from .serializers import (
    CatalogoItemSerializer,
    CursoDetalheSerializer,
    GraduacaoDetalheSerializer,
    ProfessorSerializer,
    TurmaCheckoutSerializer,
    turmas_disponiveis,
)


class CatalogoView(APIView):
    """Vitrine: cursos avulsos e graduações com ao menos uma turma disponível.

    ``?tipo=curso`` ou ``?tipo=graduacao`` filtra; ``?q=`` busca pelo nome.
    """

    permission_classes = (AllowAny,)

    def get(self, request):
        tipo = request.query_params.get('tipo')
        busca = (request.query_params.get('q') or '').strip()
        modelos = {'curso': [Curso], 'graduacao': [Graduacao]}.get(tipo, [Graduacao, Curso])
        itens = []
        for modelo in modelos:
            qs = modelo.objects.filter(publicado=True)
            if busca:
                qs = qs.filter(nome__icontains=busca)
            for produto in qs:
                turmas = turmas_disponiveis(produto)
                if turmas:
                    itens.append((produto, turmas))
        return Response(CatalogoItemSerializer(itens, many=True, context={'request': request}).data)


class CursoDetalheView(RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = CursoDetalheSerializer
    lookup_field = 'slug'
    queryset = Curso.objects.filter(publicado=True)


class GraduacaoDetalheView(RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = GraduacaoDetalheSerializer
    lookup_field = 'slug'
    queryset = Graduacao.objects.filter(publicado=True)


class TurmaCheckoutView(APIView):
    """Turma para a página de checkout — 404 se não estiver disponível."""

    permission_classes = (AllowAny,)

    def get(self, request, pk):
        turma = get_object_or_404(Turma.objects.select_related('curso', 'graduacao'), pk=pk)
        if not turma.disponivel():
            raise Http404('Turma indisponível.')
        return Response(TurmaCheckoutSerializer(turma, context={'request': request}).data)


class ProfessorListView(ListAPIView):
    """Professores; ``?home=1`` traz só os destacados na home."""

    permission_classes = (AllowAny,)
    serializer_class = ProfessorSerializer

    def get_queryset(self):
        qs = Professor.objects.all()
        if self.request.query_params.get('home'):
            qs = qs.filter(exibir_na_home=True)
        return qs
