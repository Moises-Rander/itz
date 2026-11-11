"""Graduação → Formação; Aula vira a menor unidade.

- Curso: N aulas (a ementa antiga vira aulas, uma por linha).
- Formação: N módulos → N aulas (cada curso que estava no módulo vira uma aula
  com o nome do curso); carga horária passa a ser um campo próprio.
- Turma de formação: deixa de ser um pacote de turmas de curso e ganha datas,
  vagas, professores e horários próprios (copiados das turmas que a compunham).
"""
import re

import django.db.models.deletion
from django.db import migrations, models

MARCADOR = re.compile(r'^\s*(?:[-–•*·]|\d+[.)-])\s*')


def converter(apps, schema_editor):
    Curso = apps.get_model('cursos', 'Curso')
    Formacao = apps.get_model('cursos', 'Formacao')
    ModuloCurso = apps.get_model('cursos', 'ModuloCurso')
    Aula = apps.get_model('cursos', 'Aula')
    Turma = apps.get_model('cursos', 'Turma')
    HorarioAula = apps.get_model('cursos', 'HorarioAula')

    # Ementa do curso → aulas (uma por linha não vazia).
    for curso in Curso.objects.exclude(ementa=''):
        linhas = [MARCADOR.sub('', ln).strip() for ln in curso.ementa.splitlines()]
        linhas = [ln[:200] for ln in linhas if ln]
        Aula.objects.bulk_create(
            Aula(curso=curso, nome=nome, ordem=i) for i, nome in enumerate(linhas, 1)
        )

    # Cursos de cada módulo → aulas do módulo; carga horária da formação = soma.
    for formacao in Formacao.objects.all():
        total = 0
        for item in ModuloCurso.objects.filter(modulo__formacao=formacao).select_related('curso'):
            Aula.objects.create(modulo_id=item.modulo_id, nome=item.curso.nome[:200], ordem=item.ordem)
            total += item.curso.carga_horaria
        formacao.carga_horaria = total
        formacao.save(update_fields=['carga_horaria'])

    # Turma de formação: herda datas, vagas, professores e horários das turmas de curso.
    for turma in Turma.objects.filter(formacao__isnull=False):
        partes = list(turma.turmas_curso.all())
        if not partes:
            continue
        inicios = [t.data_inicio for t in partes if t.data_inicio]
        fins = [t.data_fim for t in partes if t.data_fim]
        vagas = [t.vagas for t in partes if t.vagas is not None]
        turma.data_inicio = min(inicios) if inicios else None
        turma.data_fim = max(fins) if fins else None
        turma.vagas = min(vagas) if vagas else None
        turma.save(update_fields=['data_inicio', 'data_fim', 'vagas'])
        turma.professores.set({p.pk for t in partes for p in t.professores.all()})
        vistos = set()
        for h in HorarioAula.objects.filter(turma__in=partes):
            chave = (h.dia_semana, h.hora_inicio, h.hora_fim)
            if chave not in vistos:
                vistos.add(chave)
                HorarioAula.objects.create(
                    turma=turma, dia_semana=h.dia_semana,
                    hora_inicio=h.hora_inicio, hora_fim=h.hora_fim,
                )


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0001_initial'),
        # Os descontos (matriculas 0001) apontam para Graduacao: renomear depois.
        ('matriculas', '0001_initial'),
    ]

    operations = [
        # --- Graduação → Formação
        migrations.RemoveConstraint(model_name='modulo', name='modulo_ordem_unica_por_graduacao'),
        migrations.RemoveConstraint(model_name='turma', name='turma_curso_xor_graduacao'),
        migrations.RenameModel(old_name='Graduacao', new_name='Formacao'),
        migrations.AlterModelOptions(
            name='formacao',
            options={'ordering': ['nome'], 'verbose_name': 'formação', 'verbose_name_plural': 'formações'},
        ),
        migrations.RenameField(model_name='modulo', old_name='graduacao', new_name='formacao'),
        migrations.AlterField(
            model_name='modulo',
            name='formacao',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='modulos', to='cursos.formacao', verbose_name='formação'),
        ),
        migrations.RenameField(model_name='turma', old_name='graduacao', new_name='formacao'),
        migrations.AlterField(
            model_name='turma',
            name='formacao',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='turmas', to='cursos.formacao', verbose_name='formação'),
        ),
        migrations.AlterModelOptions(
            name='modulo',
            options={'ordering': ['formacao', 'ordem'], 'verbose_name': 'módulo', 'verbose_name_plural': 'módulos'},
        ),
        migrations.AddField(
            model_name='formacao',
            name='carga_horaria',
            field=models.PositiveIntegerField(default=0, verbose_name='carga horária (horas)'),
        ),
        migrations.DeleteModel(name='TurmaGraduacao'),
        migrations.CreateModel(
            name='TurmaFormacao',
            fields=[],
            options={
                'verbose_name': 'turma de formação',
                'verbose_name_plural': 'turmas de formação',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('cursos.turma',),
        ),
        # --- Aula
        migrations.CreateModel(
            name='Aula',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200, verbose_name='nome')),
                ('ordem', models.PositiveIntegerField(default=1, verbose_name='ordem')),
                ('curso', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='aulas', to='cursos.curso', verbose_name='curso')),
                ('modulo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='aulas', to='cursos.modulo', verbose_name='módulo')),
            ],
            options={
                'verbose_name': 'aula',
                'verbose_name_plural': 'aulas',
                'ordering': ['ordem', 'id'],
            },
        ),
        # --- Dados
        migrations.RunPython(converter, migrations.RunPython.noop),
        # --- Remove a estrutura antiga
        migrations.RemoveField(model_name='curso', name='ementa'),
        migrations.RemoveField(model_name='modulo', name='descricao'),
        migrations.RemoveField(model_name='turma', name='turmas_curso'),
        migrations.DeleteModel(name='ModuloCurso'),
        # --- Restrições
        migrations.AddConstraint(
            model_name='modulo',
            constraint=models.UniqueConstraint(fields=('formacao', 'ordem'), name='modulo_ordem_unica_por_formacao'),
        ),
        migrations.AddConstraint(
            model_name='turma',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('curso__isnull', False), ('formacao__isnull', True)), models.Q(('curso__isnull', True), ('formacao__isnull', False)), _connector='OR'), name='turma_curso_xor_formacao'),
        ),
        migrations.AddConstraint(
            model_name='aula',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('curso__isnull', False), ('modulo__isnull', True)), models.Q(('curso__isnull', True), ('modulo__isnull', False)), _connector='OR'), name='aula_curso_xor_modulo'),
        ),
    ]
