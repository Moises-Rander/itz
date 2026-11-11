import re

from django.conf import settings
from rest_framework import serializers

from .models import Matricula


def so_digitos(valor):
    return re.sub(r'\D', '', valor or '')


def cpf_valido(cpf):
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in (9, 10):
        soma = sum(int(cpf[j]) * (i + 1 - j) for j in range(i))
        if (soma * 10 % 11) % 10 != int(cpf[i]):
            return False
    return True


class AlunoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=80)
    sobrenome = serializers.CharField(max_length=120)
    cpf = serializers.CharField(max_length=14)
    email = serializers.EmailField()
    telefone = serializers.CharField(max_length=20)

    def validate_cpf(self, valor):
        cpf = so_digitos(valor)
        if not cpf_valido(cpf):
            raise serializers.ValidationError('CPF inválido.')
        return cpf

    def validate_telefone(self, valor):
        tel = so_digitos(valor)
        if len(tel) not in (10, 11):
            raise serializers.ValidationError('Informe o telefone com DDD.')
        return tel


class CartaoSerializer(serializers.Serializer):
    """Dados do cartão — usados só em memória para cobrar; nunca gravados."""

    nome = serializers.CharField(max_length=100)
    numero = serializers.CharField(max_length=23)
    mes = serializers.CharField(max_length=2)
    ano = serializers.CharField(max_length=4)
    cvv = serializers.CharField(max_length=4)

    def validate_numero(self, valor):
        numero = so_digitos(valor)
        if not 13 <= len(numero) <= 19:
            raise serializers.ValidationError('Número de cartão inválido.')
        return numero

    def validate(self, dados):
        mes, ano = so_digitos(dados['mes']), so_digitos(dados['ano'])
        if len(ano) == 2:
            ano = f'20{ano}'
        if not (mes.isdigit() and 1 <= int(mes) <= 12) or len(ano) != 4:
            raise serializers.ValidationError({'mes': 'Validade inválida.'})
        cvv = so_digitos(dados['cvv'])
        if len(cvv) not in (3, 4):
            raise serializers.ValidationError({'cvv': 'Código de segurança inválido.'})
        return {**dados, 'mes': mes.zfill(2), 'ano': ano, 'cvv': cvv}


class EnderecoSerializer(serializers.Serializer):
    """Exigido pelo Asaas para o titular do cartão."""

    cep = serializers.CharField(max_length=9)
    numero_endereco = serializers.CharField(max_length=10)

    def validate_cep(self, valor):
        cep = so_digitos(valor)
        if len(cep) != 8:
            raise serializers.ValidationError('CEP inválido.')
        return cep


class SimularPrecoSerializer(serializers.Serializer):
    turma = serializers.IntegerField()
    codigo_cupom = serializers.CharField(required=False, allow_blank=True, default='')


class CheckoutSerializer(serializers.Serializer):
    turma = serializers.IntegerField()
    aluno = AlunoSerializer()
    metodo = serializers.ChoiceField(choices=Matricula.Metodo.choices)
    parcelas = serializers.IntegerField(min_value=1, default=1)
    codigo_cupom = serializers.CharField(required=False, allow_blank=True, default='')
    cartao = CartaoSerializer(required=False)
    endereco = EnderecoSerializer(required=False)
    aceite_termos = serializers.BooleanField()

    def validate_parcelas(self, valor):
        if valor > settings.MAX_PARCELAS:
            raise serializers.ValidationError(f'Máximo de {settings.MAX_PARCELAS} parcelas.')
        return valor

    def validate_aceite_termos(self, valor):
        if not valor:
            raise serializers.ValidationError('É preciso aceitar os termos para se matricular.')
        return valor

    def validate(self, dados):
        if dados['metodo'] == Matricula.Metodo.CARTAO:
            erros = {}
            if not dados.get('cartao'):
                erros['cartao'] = 'Informe os dados do cartão.'
            if not dados.get('endereco'):
                erros['endereco'] = 'Informe o CEP e o número do endereço do titular.'
            if erros:
                raise serializers.ValidationError(erros)
        else:
            dados['parcelas'] = 1
            dados.pop('cartao', None)
            dados.pop('endereco', None)
        return dados


class MatriculaStatusSerializer(serializers.ModelSerializer):
    """O que a página do checkout precisa para acompanhar o pagamento."""

    turma = serializers.SerializerMethodField()
    aluno_nome = serializers.CharField(source='aluno.nome', read_only=True)
    valor_parcela = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    pix = serializers.SerializerMethodField()
    motivo = serializers.SerializerMethodField()

    class Meta:
        model = Matricula
        fields = (
            'token', 'status', 'metodo', 'parcelas', 'valor_parcela', 'valor_total',
            'reserva_expira_em', 'turma', 'aluno_nome', 'pix', 'motivo',
        )

    def get_turma(self, obj):
        t = obj.turma
        return {
            'id': t.pk, 'codigo': t.codigo, 'produto': t.produto.nome,
            'tipo': 'formacao' if t.is_formacao else 'curso',
            'inicio': t.inicio, 'fim': t.fim,
        }

    def get_pix(self, obj):
        if obj.metodo != Matricula.Metodo.PIX or obj.status != Matricula.Status.PENDENTE:
            return None
        return {'qrcode': obj.pix_qrcode, 'copia_cola': obj.pix_copia_cola}

    def get_motivo(self, obj):
        # Motivo de recusa do cartão (mensagem do emissor) — útil ao aluno.
        return obj.observacao if obj.status == Matricula.Status.RECUSADA else None
