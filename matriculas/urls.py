from django.urls import path

from .views import AsaasWebhookView, CheckoutView, MatriculaStatusView, SimularPrecoView

app_name = 'matriculas'

urlpatterns = [
    path('checkout/preco/', SimularPrecoView.as_view(), name='preco'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('matriculas/<str:token>/', MatriculaStatusView.as_view(), name='status'),
    path('webhooks/asaas/', AsaasWebhookView.as_view(), name='webhook-asaas'),
]
