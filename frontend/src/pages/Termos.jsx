import PageHeader from '@/components/common/PageHeader'
import { CONTATO, INSTITUICAO } from '@/lib/config'

// TEXTO-BASE: revisar com a assessoria jurídica da instituição antes de publicar.
export default function Termos() {
  return (
    <>
      <PageHeader title="Termos de matrícula" subtitle="Matrícula, pagamento, cancelamento e privacidade." />
      <div className="mx-auto max-w-3xl space-y-6 px-4 py-10 text-muted-foreground sm:px-6 lg:px-8 [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-foreground">
        <section>
          <h2>1. Matrícula</h2>
          <p>
            A matrícula em um curso ou graduação da {INSTITUICAO.nome} é confirmada quando o
            pagamento é aprovado. Ao gerar um PIX, a vaga fica reservada por tempo limitado; sem o
            pagamento nesse prazo, a reserva é liberada sem nenhuma cobrança.
          </p>
        </section>
        <section>
          <h2>2. Aulas</h2>
          <p>
            As aulas são presenciais, na sede ({CONTATO.endereco}), nas datas e horários informados
            na página da turma. Na graduação, quem entra com a turma em andamento participa dos
            cursos que ainda não terminaram.
          </p>
        </section>
        <section>
          <h2>3. Pagamento</h2>
          <p>
            Os pagamentos são processados pelo Asaas. No cartão de crédito, o parcelamento pode ter
            acréscimo, sempre exibido antes da confirmação. Não armazenamos dados de cartão.
          </p>
        </section>
        <section>
          <h2>4. Cancelamento e reembolso</h2>
          <p>
            Você pode desistir em até 7 (sete) dias após a confirmação da matrícula, com reembolso
            integral (direito de arrependimento — art. 49 do Código de Defesa do Consumidor). Para
            cancelar, fale com a secretaria: {CONTATO.email} ou {CONTATO.telefone}.
          </p>
        </section>
        <section>
          <h2>5. Privacidade (LGPD)</h2>
          <p>
            Coletamos nome, CPF, email e telefone para realizar a matrícula, emitir a cobrança e
            entrar em contato sobre o curso. Os dados são compartilhados apenas com o processador de
            pagamento e não são usados para outras finalidades. Você pode solicitar acesso,
            correção ou exclusão pelos contatos acima.
          </p>
        </section>
      </div>
    </>
  )
}
