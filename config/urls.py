"""URL configuration for the ITZ project."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

admin.site.site_header = 'Instituto de Teologia Zait'
admin.site.site_title = 'ITZ Admin'
admin.site.index_title = 'Administração'

urlpatterns = [
    # A raiz do backend leva ao painel (ex.: admin.itzait.com.br -> /admin/).
    path('', RedirectView.as_view(url='/admin/', permanent=False)),
    path('admin/', admin.site.urls),
    path('api/', include('cursos.urls')),
    path('api/', include('matriculas.urls')),
    path('api/', include('cms.urls')),
]

# Servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
