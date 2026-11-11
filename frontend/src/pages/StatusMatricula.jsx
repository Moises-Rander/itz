import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { CheckCircle2, Clock, Loader2, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Spinner, ErrorState } from '@/components/common/StateComponents'
import CopyButton from '@/components/matricula/CopyButton'
import { useStatusMatricula } from '@/hooks/useCheckout'
import { formatarBRL, periodoLabel, tipoLabel } from '@/lib/format'
import { CONTATO } from '@/lib/config'

const container = 'mx-auto max-w-xl px-4 py-12 sm:px-6'

function useContagem(ate) {
  const [agora, setAgora] = useState(() => Date.now())
  useEffect(() => {
    const id = setInterval(() => setAgora(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])
  const resto = Math.max(0, Math.floor((new Date(ate).getTime() - agora) / 1000))
  return `${String(Math.floor(resto / 60)).padStart(2, '0')}:${String(resto % 60).padStart(2, '0')}`
}

function AguardandoPix({ m }) {
  const restante = useContagem(m.reserva_expira_em)
  return (
    <div className="space-y-5 text-center">
      <h1 className="text-2xl font-bold">Pague com PIX para garantir sua vaga</h1>
      <p className="text-muted-foreground">
        Sua vaga está reservada por <strong className="text-foreground">{restante}</strong>.
        Assim que o pagamento cair, esta página confirma sozinha.
      </p>
      {m.pix.qrcode && (
        <img src={`data:image/png;base64,${m.pix.qrcode}`} alt="QR Code PIX"
          className="mx-auto h-60 w-60 rounded-lg border bg-white p-2" />
      )}
      <div className="text-left">
        <p className="mb-1 text-sm font-medium">PIX copia e cola</p>
        <div className="flex items-center gap-2">
          <code className="flex-1 truncate rounded bg-muted px-3 py-2 text-xs">{m.pix.copia_cola}</code>
          <CopyButton value={m.pix.copia_cola} />
        </div>
      </div>
      <p className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" /> Aguardando pagamento de {formatarBRL(m.valor_total)}
      </p>
    </div>
  )
}

function Confirmada({ m }) {
  return (
    <div className="space-y-4 text-center">
      <CheckCircle2 className="mx-auto h-14 w-14 text-primary" />
      <h1 className="text-2xl font-bold">Matrícula confirmada!</h1>
      <p className="text-muted-foreground">
        Bem-vindo(a), {m.aluno_nome}! Você já faz parte da turma. Enviamos os detalhes para o seu email.
      </p>
      <div className="rounded-lg bg-muted/60 p-4 text-left text-sm">
        <p className="font-semibold">{tipoLabel(m.turma.tipo)}: {m.turma.produto}</p>
        <p>Turma {m.turma.codigo} · {periodoLabel(m.turma.inicio, m.turma.fim)}</p>
        <p>Local: {CONTATO.endereco}</p>
        <p className="mt-2 text-muted-foreground">
          Pagamento: {m.metodo === 'PIX' ? 'PIX' : 'Cartão'}
          {m.parcelas > 1 ? ` em ${m.parcelas}x de ${formatarBRL(m.valor_parcela)}` : ''} — {formatarBRL(m.valor_total)}
        </p>
      </div>
      <Button asChild variant="outline"><Link to="/">Voltar ao início</Link></Button>
    </div>
  )
}

function Falhou({ m }) {
  const recusada = m.status === 'RECUSADA'
  const Icon = recusada ? XCircle : Clock
  return (
    <div className="space-y-4 text-center">
      <Icon className="mx-auto h-14 w-14 text-destructive" />
      <h1 className="text-2xl font-bold">
        {recusada ? 'Pagamento não aprovado' : m.status === 'CANCELADA' ? 'Matrícula cancelada' : 'O prazo para pagamento acabou'}
      </h1>
      <p className="text-muted-foreground">
        {recusada
          ? m.motivo || 'O cartão foi recusado. Tente outro cartão ou pague com PIX.'
          : m.status === 'CANCELADA'
          ? 'Esta matrícula foi cancelada pela secretaria.'
          : 'A reserva da vaga expirou sem o pagamento. Nenhum valor foi cobrado.'}
      </p>
      {m.status !== 'CANCELADA' && (
        <Button asChild><Link to={`/matricula/${m.turma.id}`}>Tentar novamente</Link></Button>
      )}
    </div>
  )
}

export default function StatusMatricula() {
  const { token } = useParams()
  const { data: m, isLoading, isError, refetch } = useStatusMatricula(token)

  if (isLoading) return <div className={container}><Spinner label="Carregando..." /></div>
  if (isError || !m) return <div className={container}><ErrorState onRetry={refetch} /></div>

  return (
    <div className={container}>
      <Card>
        <CardContent className="py-4">
          {m.status === 'PENDENTE' && m.pix ? <AguardandoPix m={m} />
            : m.status === 'PENDENTE' ? <Spinner label="Processando o pagamento..." />
            : m.status === 'CONFIRMADA' ? <Confirmada m={m} />
            : <Falhou m={m} />}
        </CardContent>
      </Card>
    </div>
  )
}
