from django.urls import path

from .views import (
    CatalogoView,
    CursoDetalheView,
    FormacaoDetalheView,
    ProfessorListView,
    TurmaCheckoutView,
)

app_name = 'cursos'

urlpatterns = [
    path('catalogo/', CatalogoView.as_view(), name='catalogo'),
    path('cursos/<slug:slug>/', CursoDetalheView.as_view(), name='curso'),
    path('formacoes/<slug:slug>/', FormacaoDetalheView.as_view(), name='formacao'),
    path('turmas/<int:pk>/', TurmaCheckoutView.as_view(), name='turma'),
    path('professores/', ProfessorListView.as_view(), name='professores'),
]
