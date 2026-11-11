from datetime import date, timedelta
from decimal import Decimal

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from cursos.admin import TurmaGraduacaoForm
from cursos.models import Curso, Graduacao, HorarioAula, Modulo, ModuloCurso, Professor, Turma
from matriculas.models import Aluno, Cupom, Matricula, Promocao, TaxaParcelamento, Vaga
from matriculas.services import (
    calcular_preco,
    cancelar_e_estornar,
    opcoes_parcelamento,
    processar_webhook,
    webhook_autentico,
)

HOJE = date.today()
CPF = '39053344705'
CPF2 = '11144477735'


def aluno_payload(cpf=CPF):
    return {'nome': 'Maria', 'sobrenome': 'Souza', 'cpf': cpf,
            'email': 'maria@x.com', 'telefone': '(98) 99999-0000'}


class Base(TestCase):
    """Catálogo: Hebraico e Grego (cursos), Graduação Teologia I com os dois."""

    def setUp(self):
        self.api = APIClient()
        self.prof = Professor.objects.create(nome='Prof. Ana', titulacao='Mestre')
        self.hebraico = Curso.objects.create(nome='Hebraico Básico', carga_horaria=40)
        self.grego = Curso.objects.create(nome='Grego Básico', carga_horaria=30)
        self.grad = Graduacao.objects.create(nome='Teologia I')
        m1 = Modulo.objects.create(graduacao=self.grad, nome='Línguas', ordem=1)
        ModuloCurso.objects.create(modulo=m1, curso=self.hebraico, ordem=1)
        ModuloCurso.objects.create(modulo=m1, curso=self.grego, ordem=2)

        self.t_heb = self._turma_curso(self.hebraico, HOJE + timedelta(days=10), vagas=2)
        self.t_gre = self._turma_curso(self.grego, HOJE + timedelta(days=60), vagas=5)
        self.t_grad = Turma.objects.create(
            graduacao=self.grad, codigo='2027.1', preco=Decimal('500'),
            status=Turma.Status.PUBLICADA,
        )
        self.t_grad.turmas_curso.set([self.t_heb, self.t_gre])

    def _turma_curso(self, curso, inicio, vagas, preco='200'):
        t = Turma.objects.create(
            curso=curso, codigo='2027.1', preco=Decimal(preco), status=Turma.Status.PUBLICADA,
            data_inicio=inicio, data_fim=inicio + timedelta(days=30), vagas=vagas,
        )
        t.professores.add(self.prof)
        HorarioAula.objects.create(turma=t, dia_semana=1, hora_inicio='19:00', hora_fim='22:00')
        return t

    def _matricula(self, turma, cpf=CPF, status=Matricula.Status.CONFIRMADA, expira=None):
        aluno, _ = Aluno.objects.get_or_create(cpf=cpf, defaults={
            'nome': 'A', 'sobrenome': 'B', 'email': 'a@x.com', 'telefone': '98999990000'})
        m = Matricula.objects.create(
            aluno=aluno, turma=turma, status=status, metodo='PIX',
            valor_original=turma.preco, valor_a_vista=turma.preco, valor_total=turma.preco,
            termos_aceitos_em=timezone.now(),
            reserva_expira_em=expira or timezone.now() + timedelta(minutes=30),
        )
        for t in turma.turmas_curso_restantes():
            Vaga.objects.create(matricula=m, turma=t)
        return m

    def _checkout(self, turma, **extra):
        dados = {'turma': turma.pk, 'aluno': aluno_payload(extra.pop('cpf', CPF)),
                 'metodo': 'PIX', 'aceite_termos': True, **extra}
        with self.captureOnCommitCallbacks(execute=True):
            return self.api.post('/api/checkout/', dados, format='json')


class DisponibilidadeTests(Base):
    def test_turma_publicada_com_vaga_aparece(self):
        self.assertTrue(self.t_heb.disponivel())
        self.assertTrue(self.t_grad.disponivel())

    def test_rascunho_e_fechada_nao_aparecem(self):
        for st in (Turma.Status.RASCUNHO, Turma.Status.FECHADA):
            self.t_heb.status = st
            self.assertFalse(self.t_heb.disponivel())

    def test_curso_sai_do_ar_apos_inicio(self):
        self.t_heb.data_inicio = HOJE - timedelta(days=1)
        self.assertFalse(self.t_heb.disponivel())

    def test_graduacao_aceita_entrada_ate_ultima_turma_comecar(self):
        Turma.objects.filter(pk=self.t_heb.pk).update(
            data_inicio=HOJE - timedelta(days=40), data_fim=HOJE - timedelta(days=5))
        self.assertTrue(self.t_grad.disponivel())  # Grego ainda não começou
        # e só ocupa vaga no Grego (Hebraico já terminou)
        self.assertEqual([t.pk for t in self.t_grad.turmas_curso_restantes()], [self.t_gre.pk])

    def test_graduacao_com_grade_incompleta_nao_aparece(self):
        self.t_grad.turmas_curso.set([self.t_heb])
        self.assertFalse(self.t_grad.disponivel())

    def test_produto_despublicado_esconde_turmas(self):
        self.grad.publicado = False
        self.grad.save()
        self.assertFalse(self.t_grad.disponivel())


class VagasTests(Base):
    def test_graduacao_ocupa_vaga_nas_turmas_de_curso(self):
        self._matricula(self.t_grad)
        self.assertEqual(self.t_heb.vagas_disponiveis(), 1)
        self.assertEqual(self.t_gre.vagas_disponiveis(), 4)
        self.assertEqual(self.t_grad.vagas_disponiveis(), 1)  # o menor entre as turmas

    def test_avulso_lotando_curso_fecha_a_graduacao(self):
        self._matricula(self.t_heb, cpf=CPF)
        self._matricula(self.t_heb, cpf=CPF2)
        self.assertFalse(self.t_heb.disponivel())
        self.assertFalse(self.t_grad.disponivel())

    def test_reserva_pendente_ocupa_ate_expirar(self):
        m = self._matricula(self.t_heb, status=Matricula.Status.PENDENTE)
        self.assertEqual(self.t_heb.vagas_disponiveis(), 1)
        Matricula.objects.filter(pk=m.pk).update(reserva_expira_em=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.t_heb.vagas_disponiveis(), 2)  # liberou sem tarefa agendada


class PrecoTests(Base):
    def test_promocao_mais_especifica_e_cupom(self):
        ontem, depois = HOJE - timedelta(days=1), HOJE + timedelta(days=5)
        Promocao.objects.create(tipo_desconto='PERCENTUAL', valor=10, data_inicio=ontem, data_fim=depois)
        Promocao.objects.create(tipo_desconto='FIXO', valor=50, data_inicio=ontem, data_fim=depois,
                                turma=self.t_heb)
        cupom = Cupom.objects.create(codigo='DEZ', tipo_desconto='FIXO', valor_desconto=10,
                                     data_inicio=ontem, data_fim=depois, max_usos=5)
        p = calcular_preco(self.t_heb, cupom)
        self.assertEqual(p['desconto_promocao'], Decimal('50.00'))  # a da turma vence a geral
        self.assertEqual(p['valor_a_vista'], Decimal('140.00'))

    def test_cupom_restrito_a_outro_produto_e_rejeitado(self):
        Cupom.objects.create(codigo='GRAD', tipo_desconto='FIXO', valor_desconto=10,
                             data_inicio=HOJE, data_fim=HOJE, max_usos=5, graduacao=self.grad)
        r = self.api.post('/api/checkout/preco/', {'turma': self.t_heb.pk, 'codigo_cupom': 'GRAD'})
        self.assertEqual(r.status_code, 400)
        r = self.api.post('/api/checkout/preco/', {'turma': self.t_grad.pk, 'codigo_cupom': 'grad'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Decimal(r.json()['valor_a_vista']), Decimal('490.00'))

    def test_juros_do_parcelamento_repassados(self):
        TaxaParcelamento.objects.create(parcelas=12, acrescimo_percentual=Decimal('15'))
        opcoes = opcoes_parcelamento(Decimal('1000'))
        self.assertEqual(len(opcoes), 12)
        self.assertEqual(opcoes[0]['valor_total'], Decimal('1000.00'))
        self.assertEqual(opcoes[1]['valor_total'], Decimal('1000.00'))  # 2x sem taxa cadastrada
        self.assertEqual(opcoes[11]['valor_total'], Decimal('1150.00'))
        self.assertEqual(opcoes[11]['valor_parcela'], Decimal('95.83'))


@override_settings(ASAAS_FAKE=True, REITOR_EMAIL='reitor@x.com', ASAAS_WEBHOOK_TOKEN='segredo')
class CheckoutTests(Base):
    def test_pix_reserva_e_webhook_confirma_e_envia_emails(self):
        r = self._checkout(self.t_grad)
        self.assertEqual(r.status_code, 201, r.content)
        corpo = r.json()
        self.assertEqual(corpo['status'], 'PENDENTE')
        self.assertTrue(corpo['pix']['copia_cola'])
        self.assertEqual(self.t_heb.vagas_disponiveis(), 1)  # reservada
        self.assertEqual(len(mail.outbox), 0)  # nada antes de pagar

        m = Matricula.objects.get(token=corpo['token'])
        evento = {'event': 'PAYMENT_RECEIVED',
                  'payment': {'id': m.asaas_payment_id, 'externalReference': str(m.pk)}}
        with self.captureOnCommitCallbacks(execute=True):
            self.assertTrue(processar_webhook(evento)['processed'])
            self.assertFalse(processar_webhook(evento)['processed'])  # idempotente
        m.refresh_from_db()
        self.assertEqual(m.status, 'CONFIRMADA')
        destinos = sorted(e.to[0] for e in mail.outbox)
        self.assertEqual(destinos, ['maria@x.com', 'reitor@x.com'])
        reitor = next(e for e in mail.outbox if e.to == ['reitor@x.com']).body
        for dado in ('Maria Souza', '390.533.447-05', 'Hebraico Básico', 'Grego Básico', 'Prof. Ana'):
            self.assertIn(dado, reitor)

    def test_cartao_parcelado_confirma_na_hora(self):
        TaxaParcelamento.objects.create(parcelas=12, acrescimo_percentual=Decimal('20'))
        r = self._checkout(
            self.t_heb, metodo='CARTAO', parcelas=12,
            cartao={'nome': 'MARIA SOUZA', 'numero': '4111 1111 1111 1111', 'mes': '12', 'ano': '30', 'cvv': '123'},
            endereco={'cep': '65070-616', 'numero_endereco': '235'},
        )
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()['status'], 'CONFIRMADA')
        self.assertEqual(Decimal(r.json()['valor_total']), Decimal('240.00'))
        self.assertEqual(len(mail.outbox), 2)

    def test_cartao_recusado_libera_a_vaga(self):
        r = self._checkout(
            self.t_heb, metodo='CARTAO',
            cartao={'nome': 'X', 'numero': '4000000000000002', 'mes': '12', 'ano': '2030', 'cvv': '123'},
            endereco={'cep': '65070616', 'numero_endereco': '1'},
        )
        self.assertEqual(r.json()['status'], 'RECUSADA')
        self.assertTrue(r.json()['motivo'])
        self.assertEqual(self.t_heb.vagas_disponiveis(), 2)

    def test_cartao_exige_endereco_e_termos(self):
        r = self._checkout(self.t_heb, aceite_termos=False)
        self.assertEqual(r.status_code, 400)
        self.assertIn('aceite_termos', r.json())
        r = self._checkout(self.t_heb, metodo='CARTAO')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(set(r.json()), {'cartao', 'endereco'})
        self.assertEqual(Matricula.objects.count(), 0)

    def test_cpf_invalido(self):
        r = self._checkout(self.t_heb, cpf='12345678900')
        self.assertEqual(r.status_code, 400)

    def test_nova_tentativa_substitui_reserva_anterior(self):
        self._checkout(self.t_heb)
        self._checkout(self.t_heb)
        self.assertEqual(Matricula.objects.filter(status='PENDENTE').count(), 1)
        self.assertEqual(self.t_heb.vagas_disponiveis(), 1)

    def test_nao_matricula_duas_vezes(self):
        self._matricula(self.t_heb)
        r = self._checkout(self.t_heb)
        self.assertEqual(r.status_code, 400)

    def test_status_expira_reserva_vencida(self):
        token = self._checkout(self.t_heb).json()['token']
        Matricula.objects.filter(token=token).update(reserva_expira_em=timezone.now() - timedelta(minutes=1))
        r = self.api.get(f'/api/matriculas/{token}/')
        self.assertEqual(r.json()['status'], 'EXPIRADA')
        self.assertIsNone(r.json()['pix'])

    def test_cancelar_e_estornar_libera_vagas(self):
        m = self._matricula(self.t_grad)
        cancelar_e_estornar(m, 'pedido do aluno')
        m.refresh_from_db()
        self.assertEqual(m.status, 'CANCELADA')
        self.assertEqual(self.t_heb.vagas_disponiveis(), 2)

    def test_webhook_token(self):
        self.assertTrue(webhook_autentico({'asaas-access-token': 'segredo'}))
        self.assertFalse(webhook_autentico({'asaas-access-token': 'x'}))
        self.assertEqual(self.api.post('/api/webhooks/asaas/', {}, format='json').status_code, 403)


class CatalogoApiTests(Base):
    def test_catalogo_lista_so_o_que_tem_turma_disponivel(self):
        Curso.objects.create(nome='Sem Turma', carga_horaria=10)
        itens = self.api.get('/api/catalogo/').json()
        self.assertEqual({i['nome'] for i in itens}, {'Teologia I', 'Hebraico Básico', 'Grego Básico'})
        grad = next(i for i in itens if i['tipo'] == 'graduacao')
        self.assertEqual(grad['carga_horaria'], 70)
        self.assertEqual(self.api.get('/api/catalogo/?tipo=curso').json()[0]['tipo'], 'curso')

    def test_detalhe_do_curso_mostra_graduacoes_que_o_incluem(self):
        r = self.api.get(f'/api/cursos/{self.hebraico.slug}/').json()
        self.assertEqual(r['graduacoes'][0]['slug'], self.grad.slug)
        turma = r['turmas'][0]
        self.assertEqual(turma['cronograma'][0]['horarios'][0]['dia'], 'Segunda-feira')
        self.assertEqual(turma['professores'][0]['nome'], 'Prof. Ana')

    def test_detalhe_da_graduacao_traz_grade_e_cronograma(self):
        r = self.api.get(f'/api/graduacoes/{self.grad.slug}/').json()
        self.assertEqual([c['nome'] for c in r['modulos'][0]['cursos']], ['Hebraico Básico', 'Grego Básico'])
        self.assertEqual(len(r['turmas'][0]['cronograma']), 2)

    def test_turma_indisponivel_404_no_checkout(self):
        self.t_heb.status = Turma.Status.FECHADA
        self.t_heb.save()
        self.assertEqual(self.api.get(f'/api/turmas/{self.t_heb.pk}/').status_code, 404)


class AdminFormTests(Base):
    def _form(self, turmas, status='PUBLICADA'):
        return TurmaGraduacaoForm(data={
            'graduacao': self.grad.pk, 'codigo': '2027.2', 'status': status,
            'preco': '400', 'turmas_curso': [t.pk for t in turmas],
        })

    def test_publicar_exige_grade_completa(self):
        self.assertFalse(self._form([self.t_heb]).is_valid())
        self.assertTrue(self._form([self.t_heb], status='RASCUNHO').is_valid())
        self.assertTrue(self._form([self.t_heb, self.t_gre]).is_valid())

    def test_rejeita_turma_de_curso_fora_da_grade_ou_repetida(self):
        outro = self._turma_curso(Curso.objects.create(nome='Outro'), HOJE, vagas=1)
        self.assertFalse(self._form([self.t_heb, self.t_gre, outro]).is_valid())
        heb2 = self._turma_curso(self.hebraico, HOJE + timedelta(days=90), vagas=1)
        self.assertFalse(self._form([self.t_heb, heb2, self.t_gre]).is_valid())


class AdminTelasTests(Base):
    """Toda tela do Admin (lista, inclusão, edição) abre sem erro."""

    def test_todas_as_telas_abrem(self):
        from django.contrib import admin
        from django.urls import reverse

        from accounts.models import User

        self.client.force_login(User.objects.create_superuser(email='adm@x.com', password='x'))
        self._matricula(self.t_grad)
        falhas = []
        for model in admin.site._registry:
            info = (model._meta.app_label, model._meta.model_name)
            urls = [reverse('admin:%s_%s_changelist' % info)]
            if model is not Matricula:
                urls.append(reverse('admin:%s_%s_add' % info))
            obj = model._default_manager.first()
            if obj:
                urls.append(reverse('admin:%s_%s_change' % info, args=[obj.pk]))
            falhas += [(u, s) for u in urls if (s := self.client.get(u).status_code) != 200]
        self.assertEqual(falhas, [])
