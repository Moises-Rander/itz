import { Link } from 'react-router-dom'
import { CalendarDays, Clock, MapPin, UserRound, GraduationCap } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import Preco from './Preco'
import { periodoLabel } from '@/lib/format'
import { CONTATO } from '@/lib/config'

const DIAS = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
const curto = (dia) => dia.replace('-feira', '')

// Junta os dias com o mesmo horário: "Segunda a Sexta", "Terça e Quinta", "Sábado".
function diasLabel(dias) {
  const idx = dias.map((d) => DIAS.indexOf(d))
  const seguidos = idx.every((n, i) => i === 0 || n === idx[i - 1] + 1) && !idx.includes(-1)
  if (dias.length >= 3 && seguidos) return `${curto(dias[0])} a ${curto(dias.at(-1))}`
  if (dias.length === 1) return dias[0]
  return `${dias.slice(0, -1).map(curto).join(', ')} e ${curto(dias.at(-1))}`
}

function agruparHorarios(horarios) {
  const grupos = new Map()
  horarios.forEach((h) => {
    const faixa = `${h.inicio}–${h.fim}`
    grupos.set(faixa, [...(grupos.get(faixa) || []), h.dia])
  })
  return [...grupos].map(([faixa, dias]) => ({ dias: diasLabel(dias), faixa }))
}

function Info({ icon: Icon, children }) {
  return (
    <div className="flex items-start gap-3">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
      <div className="min-w-0 space-y-0.5">{children}</div>
    </div>
  )
}

// Uma turma disponível (card vertical, feito para a coluna lateral).
export default function TurmaOferta({ turma }) {
  const horarios = agruparHorarios(turma.horarios || [])
  return (
    <Card>
      <CardContent>
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <h3 className="text-lg font-semibold">Turma {turma.codigo}</h3>
          <Badge variant="outline">
            {turma.vagas_disponiveis} vaga{turma.vagas_disponiveis === 1 ? '' : 's'}
          </Badge>
        </div>

        <div className="space-y-3 text-sm">
          <Info icon={CalendarDays}>
            <p className="font-medium">{periodoLabel(turma.inicio, turma.fim)}</p>
          </Info>
          <Info icon={Clock}>
            {horarios.length ? (
              horarios.map((h) => (
                <p key={h.faixa}>
                  <span className="font-medium">{h.dias}</span>
                  <span className="text-muted-foreground"> · {h.faixa}</span>
                </p>
              ))
            ) : (
              <p className="text-muted-foreground">Horários a definir</p>
            )}
          </Info>
          {turma.professores.length > 0 && (
            <Info icon={UserRound}>
              <p className="font-medium">{turma.professores.map((p) => p.nome).join(', ')}</p>
            </Info>
          )}
          <Info icon={MapPin}>
            <p className="font-medium">Presencial</p>
            <p className="text-xs text-muted-foreground">{CONTATO.endereco}</p>
          </Info>
        </div>

        <div className="mt-5 flex flex-col gap-3 border-t pt-4">
          <Preco preco={turma.preco} grande />
          <Button asChild size="lg" className="w-full">
            <Link to={`/matricula/${turma.id}`}>
              <GraduationCap className="mr-2 h-5 w-5" /> Matricular-se
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
