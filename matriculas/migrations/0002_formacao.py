"""Graduação → Formação nos descontos; matrícula em formação passa a ocupar
uma única vaga, na própria turma (antes ocupava uma em cada turma de curso)."""
import django.db.models.deletion
from django.db import migrations, models


def vaga_na_propria_turma(apps, schema_editor):
    Matricula = apps.get_model('matriculas', 'Matricula')
    Vaga = apps.get_model('matriculas', 'Vaga')
    for m in Matricula.objects.filter(turma__formacao__isnull=False):
        Vaga.objects.filter(matricula=m).delete()
        Vaga.objects.create(matricula=m, turma_id=m.turma_id)


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0002_formacao_aulas'),
        ('matriculas', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(model_name='cupom', old_name='graduacao', new_name='formacao'),
        migrations.AlterField(
            model_name='cupom',
            name='formacao',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='cursos.formacao', verbose_name='formação'),
        ),
        migrations.RenameField(model_name='promocao', old_name='graduacao', new_name='formacao'),
        migrations.AlterField(
            model_name='promocao',
            name='formacao',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='cursos.formacao', verbose_name='formação'),
        ),
        migrations.AlterField(
            model_name='vaga',
            name='turma',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ocupacoes', to='cursos.turma', verbose_name='turma'),
        ),
        migrations.RunPython(vaga_na_propria_turma, migrations.RunPython.noop),
    ]
