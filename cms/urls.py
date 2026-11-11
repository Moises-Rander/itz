from django.urls import path

from .views import (
    ConteudoInstitucionalListView,
    DepoimentoListView,
    MembroEquipeListView,
)

app_name = 'cms'

urlpatterns = [
    path('cms/conteudo/', ConteudoInstitucionalListView.as_view(), name='conteudo'),
    path('cms/equipe/', MembroEquipeListView.as_view(), name='equipe'),
    path('cms/depoimentos/', DepoimentoListView.as_view(), name='depoimentos'),
]
