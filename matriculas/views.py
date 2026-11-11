from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from cursos.models import Turma

from .models import Matricula
from .serializers import CheckoutSerializer, MatriculaStatusSerializer, SimularPrecoSerializer
from .services import (
    PagamentoIndisponivel,
    atualizar_status,
    calcular_preco,
    iniciar_matricula,
    opcoes_parcelamento,
    processar_webhook,
    resolver_cupom,
    webhook_autentico,
)


def ip_cliente(request):
    """IP do aluno (exigido pelo Asaas). Mesma regra do limitador de tentativas:
    respeita ``NUM_PROXIES``, então um X-Forwarded-For forjado não engana."""
    return ScopedRateThrottle().get_ident(request)


class SimularPrecoView(APIView):
    """Preço final e opções de parcelamento (com cupom, se informado)."""

    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'simular'

    def post(self, request):
        s = SimularPrecoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        turma = Turma.objects.filter(pk=s.validated_data['turma']).first()
        if turma is None or not turma.disponivel():
            raise NotFound('Turma indisponível.')
        cupom = resolver_cupom(s.validated_data['codigo_cupom'], turma)
        p = calcular_preco(turma, cupom)
        return Response({
            'valor_original': p['valor_original'],
            'desconto_promocao': p['desconto_promocao'],
            'promocao': p['promocao'].nome if p['promocao'] else None,
            'desconto_cupom': p['desconto_cupom'],
            'cupom': cupom.codigo if cupom else None,
            'valor_a_vista': p['valor_a_vista'],
            'parcelamento': opcoes_parcelamento(p['valor_a_vista']),
        })


class CheckoutView(APIView):
    """Inicia a matrícula e o pagamento (PIX ou cartão)."""

    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'checkout'  # freia testes de cartão em massa

    def post(self, request):
        s = CheckoutSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        try:
            matricula = iniciar_matricula(
                turma_id=d['turma'], aluno=dict(d['aluno']), metodo=d['metodo'],
                parcelas=d['parcelas'], codigo_cupom=d['codigo_cupom'],
                cartao=d.get('cartao'), endereco=d.get('endereco'), ip=ip_cliente(request),
            )
        except Turma.DoesNotExist:
            raise NotFound('Turma não encontrada.') from None
        except PagamentoIndisponivel:
            return Response(
                {'detail': 'O sistema de pagamento não respondeu. Nenhum valor foi cobrado; '
                           'tente novamente em instantes.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(MatriculaStatusSerializer(matricula).data, status=status.HTTP_201_CREATED)


class MatriculaStatusView(APIView):
    """Consultado pela página enquanto o PIX não é pago."""

    permission_classes = (AllowAny,)

    def get(self, request, token):
        matricula = get_object_or_404(
            Matricula.objects.select_related('turma', 'aluno'), token=token
        )
        return Response(MatriculaStatusSerializer(atualizar_status(matricula)).data)


class AsaasWebhookView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        if not webhook_autentico(request.headers):
            raise PermissionDenied('Webhook não autenticado.')
        return Response(processar_webhook(request.data))
