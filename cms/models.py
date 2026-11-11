from django.db import models


class ConteudoInstitucional(models.Model):
    """Bloco editável da página institucional."""

    class Secao(models.TextChoices):
        HERO = 'HERO', 'Hero (banner inicial)'
        SOBRE = 'SOBRE', 'Sobre'
        MISSAO = 'MISSAO', 'Missão'
        VISAO = 'VISAO', 'Visão'
        VALORES = 'VALORES', 'Valores'

    secao = models.CharField('seção', max_length=10, choices=Secao.choices)
    titulo = models.CharField('título', max_length=200)
    texto = models.TextField('texto')
    imagem = models.ImageField('imagem', upload_to='institucional/', null=True, blank=True)
    ordem = models.PositiveIntegerField('ordem', default=0)
    is_ativo = models.BooleanField('ativo', default=True)

    class Meta:
        verbose_name = 'conteúdo institucional'
        verbose_name_plural = 'conteúdos institucionais'
        ordering = ['secao', 'ordem']

    def __str__(self):
        return f'{self.get_secao_display()} — {self.titulo}'


class MembroEquipe(models.Model):
    """Membro da equipe institucional (reitoria, secretaria, diretoria) exibido no site."""

    nome = models.CharField('nome', max_length=150)
    cargo = models.CharField('cargo', max_length=120)
    bio = models.TextField('bio', blank=True)
    foto = models.ImageField('foto', upload_to='equipe/', null=True, blank=True)
    ordem = models.PositiveIntegerField('ordem', default=0)
    is_ativo = models.BooleanField('ativo', default=True)

    class Meta:
        verbose_name = 'membro da equipe'
        verbose_name_plural = 'membros da equipe'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return f'{self.nome} — {self.cargo}'


class Depoimento(models.Model):
    """Depoimento de aluno exibido no site, cadastrado manualmente pelo admin."""

    nome_aluno = models.CharField('nome do aluno', max_length=150)
    foto = models.ImageField('foto', upload_to='depoimentos/', null=True, blank=True)
    nome_curso = models.CharField('nome do curso', max_length=150, blank=True)
    texto = models.TextField('depoimento')
    is_publicado = models.BooleanField('publicado', default=False)
    ordem = models.PositiveIntegerField('ordem de exibição', default=0)

    class Meta:
        verbose_name = 'depoimento'
        verbose_name_plural = 'depoimentos'
        ordering = ['ordem', 'nome_aluno']

    def __str__(self):
        return f'{self.nome_aluno} — {self.nome_curso}'
