"""Cliente da integração com o Asaas (API v3).

- ``AsaasClient``: chama a API real via HTTP.
- ``FakeAsaasClient``: simula respostas sem rede (desenvolvimento e testes),
  ativo quando ``settings.ASAAS_FAKE`` é True ou não há API key.

SEGURANÇA: dados de cartão passam por aqui apenas em memória, a caminho do
Asaas. Nunca grave, registre em log ou inclua em mensagens de erro o conteúdo
de ``cartao``.
"""
import hashlib
import uuid
from datetime import date

import requests
from django.conf import settings


class AsaasError(Exception):
    """Falha de comunicação ou erro de negócio devolvido pelo Asaas."""

    def __init__(self, mensagem, *, recusado=False):
        super().__init__(mensagem)
        self.recusado = recusado  # True = cartão recusado (erro do pagador)


# Status do Asaas que significam "dinheiro garantido".
STATUS_PAGO = {'CONFIRMED', 'RECEIVED', 'RECEIVED_IN_CASH'}


class AsaasClient:
    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key or settings.ASAAS_API_KEY
        self.base_url = (base_url or settings.ASAAS_BASE_URL).rstrip('/')

    def _req(self, metodo, path, *, json=None, params=None):
        try:
            resp = requests.request(
                metodo, f'{self.base_url}{path}', json=json, params=params,
                headers={'access_token': self.api_key, 'Content-Type': 'application/json'},
                timeout=30,
            )
        except requests.RequestException as exc:
            # Só o tipo do erro: a exceção pode carregar o corpo da requisição.
            raise AsaasError(f'Falha de conexão com o Asaas ({type(exc).__name__}).') from None
        if resp.status_code == 400:
            erros = (resp.json() or {}).get('errors') or []
            descricao = '; '.join(e.get('description', '') for e in erros) or 'Requisição recusada.'
            raise AsaasError(descricao, recusado=True)
        if not resp.ok:
            raise AsaasError(f'Asaas respondeu HTTP {resp.status_code}.')
        return resp.json() if resp.content else {}

    # ----------------------------------------------------------- clientes
    def criar_ou_recuperar_cliente(self, *, nome, cpf, email, telefone):
        existentes = self._req('GET', '/customers', params={'cpfCnpj': cpf}).get('data') or []
        if existentes:
            return existentes[0]['id']
        criado = self._req('POST', '/customers', json={
            'name': nome, 'cpfCnpj': cpf, 'email': email, 'mobilePhone': telefone,
            # Os emails ao aluno saem do nosso sistema; evita mensagens duplicadas.
            'notificationDisabled': True,
        })
        return criado['id']

    # ---------------------------------------------------------- cobranças
    def cobrar_pix(self, *, customer_id, valor, descricao, referencia):
        cobranca = self._req('POST', '/payments', json={
            'customer': customer_id, 'billingType': 'PIX', 'value': float(valor),
            'dueDate': date.today().isoformat(),
            'description': descricao, 'externalReference': referencia,
        })
        qr = self._req('GET', f"/payments/{cobranca['id']}/pixQrCode")
        return {
            'payment_id': cobranca['id'],
            'pix_qrcode': qr.get('encodedImage', ''),
            'pix_copia_cola': qr.get('payload', ''),
        }

    def cobrar_cartao(self, *, customer_id, valor_total, parcelas, descricao, referencia,
                      cartao, titular, ip):
        """Cobra no cartão. Retorna {'payment_id', 'pago'}; levanta AsaasError
        com ``recusado=True`` se o cartão for negado."""
        payload = {
            'customer': customer_id, 'billingType': 'CREDIT_CARD',
            'dueDate': date.today().isoformat(),
            'description': descricao, 'externalReference': referencia,
            'creditCard': {
                'holderName': cartao['nome'], 'number': cartao['numero'],
                'expiryMonth': cartao['mes'], 'expiryYear': cartao['ano'],
                'ccv': cartao['cvv'],
            },
            'creditCardHolderInfo': {
                'name': titular['nome'], 'email': titular['email'],
                'cpfCnpj': titular['cpf'], 'postalCode': titular['cep'],
                'addressNumber': titular['numero_endereco'], 'phone': titular['telefone'],
            },
            'remoteIp': ip,
        }
        if parcelas > 1:
            payload['installmentCount'] = parcelas
            payload['totalValue'] = float(valor_total)
        else:
            payload['value'] = float(valor_total)
        cobranca = self._req('POST', '/payments', json=payload)
        return {
            'payment_id': cobranca['id'],
            'installment_id': cobranca.get('installment') or '',
            'pago': cobranca.get('status') in STATUS_PAGO,
        }

    def pagamento_confirmado(self, payment_id):
        return self._req('GET', f'/payments/{payment_id}').get('status') in STATUS_PAGO

    def cancelar_cobranca(self, payment_id):
        """Remove uma cobrança ainda não paga (ex.: PIX expirado)."""
        self._req('DELETE', f'/payments/{payment_id}')

    def estornar(self, *, payment_id, installment_id=''):
        if installment_id:
            self._req('POST', f'/installments/{installment_id}/refund')
        else:
            self._req('POST', f'/payments/{payment_id}/refund')


class FakeAsaasClient:
    """Simulação sem rede. Cartão terminado em 0002 é recusado; os demais são aprovados.
    O PIX nunca é pago sozinho — confirme pelo Admin (ação disponível só no modo simulado)."""

    def criar_ou_recuperar_cliente(self, *, nome, cpf, email, telefone):
        return f'cus_fake_{hashlib.sha1(cpf.encode()).hexdigest()[:12]}'

    def cobrar_pix(self, *, customer_id, valor, descricao, referencia):
        payment_id = f'pay_fake_{uuid.uuid4().hex[:16]}'
        return {
            'payment_id': payment_id,
            # PNG 1x1 transparente — só para a tela ter o que exibir.
            'pix_qrcode': (
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
            ),
            'pix_copia_cola': f'00020126580014br.gov.bcb.pix-FAKE-{payment_id}',
        }

    def cobrar_cartao(self, *, customer_id, valor_total, parcelas, descricao, referencia,
                      cartao, titular, ip):
        if cartao['numero'].endswith('0002'):
            raise AsaasError('Transação não autorizada pelo emissor do cartão.', recusado=True)
        return {
            'payment_id': f'pay_fake_{uuid.uuid4().hex[:16]}',
            'installment_id': f'ins_fake_{uuid.uuid4().hex[:12]}' if parcelas > 1 else '',
            'pago': True,
        }

    def pagamento_confirmado(self, payment_id):
        return False

    def cancelar_cobranca(self, payment_id):
        return None

    def estornar(self, *, payment_id, installment_id=''):
        return None


def get_asaas_client():
    if getattr(settings, 'ASAAS_FAKE', False) or not settings.ASAAS_API_KEY:
        return FakeAsaasClient()
    return AsaasClient()
