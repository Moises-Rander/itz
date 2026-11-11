from rest_framework import serializers

from .models import ConteudoInstitucional, Depoimento, MembroEquipe


class ConteudoInstitucionalSerializer(serializers.ModelSerializer):
    secao_display = serializers.CharField(source='get_secao_display', read_only=True)

    class Meta:
        model = ConteudoInstitucional
        fields = ('id', 'secao', 'secao_display', 'titulo', 'texto', 'imagem', 'ordem')


class MembroEquipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembroEquipe
        fields = ('id', 'nome', 'cargo', 'bio', 'foto', 'ordem')


class DepoimentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depoimento
        fields = ('id', 'nome_aluno', 'foto', 'nome_curso', 'texto', 'ordem')
