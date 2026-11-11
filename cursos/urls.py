from django.urls import path

from .views import (
    CatalogoView,
    CursoDetalheView,
    GraduacaoDetalheView,
    ProfessorListView,
    TurmaCheckoutView,
)

app_name = 'cursos'

urlpatterns = [
    path('catalogo/', CatalogoView.as_view(), name='catalogo'),
    path('cursos/<slug:slug>/', CursoDetalheView.as_view(), name='curso'),
    path('graduacoes/<slug:slug>/', GraduacaoDetalheView.as_view(), name='graduacao'),
    path('turmas/<int:pk>/', TurmaCheckoutView.as_view(), name='turma'),
    path('professores/', ProfessorListView.as_view(), name='professores'),
]
