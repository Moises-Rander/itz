import { Link } from 'react-router-dom'
import { CalendarDays, Clock, MapPin, UserRound, GraduationCap } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import Preco from './Preco'
import { formatarData, periodoLabel } from '@/lib/format'
import { CONTATO } from '@/lib/config'

function Horarios({ horarios }) {
  if (!horarios?.length) return <span>Horários a definir</span>
  return horarios.map((h) => `${h.dia} ${h.inicio}–${h.fim}`).join(' · ')
}

// Uma turma disponível: período, vagas, preço, cronograma e botão de matrícula.
export default function TurmaOferta({ turma, graduacao }) {
  return (
    <Card>
      <CardContent className="space-y-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-lg font-semibold">Turma {turma.codigo}</h3>
              {turma.em_andamento && <Badge variant="secondary">Em andamento — ainda dá para entrar</Badge>}
              <Badge variant="outline">
                {turma.vagas_disponiveis} vaga{turma.vagas_disponiveis === 1 ? '' : 's'}
              </Badge>
            </div>
            <p className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
              <CalendarDays className="h-4 w-4" /> {periodoLabel(turma.inicio, turma.fim)}
            </p>
            <p className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
              <MapPin className="h-4 w-4" /> Presencial — {CONTATO.endereco}
            </p>
          </div>
          <div className="flex flex-col items-start gap-3 sm:items-end sm:text-right">
            <Preco preco={turma.preco} grande />
            <Button asChild size="lg">
              <Link to={`/matricula/${turma.id}`}>
                <GraduationCap className="mr-2 h-5 w-5" /> Matricular-se
              </Link>
            </Button>
          </div>
        </div>

        <div className="divide-y rounded-lg border">
          {turma.cronograma.map((c) => (
            <div key={c.curso_slug} className="grid gap-1 p-3 text-sm sm:grid-cols-[1fr_auto] sm:gap-4">
              <div>
                {graduacao ? (
                  <Link to={`/cursos/${c.curso_slug}`} className="font-medium hover:text-primary">
                    {c.curso}
                  </Link>
                ) : (
                  <span className="font-medium">Aulas</span>
                )}
                <p className="flex items-center gap-1 text-muted-foreground">
                  <Clock className="h-3.5 w-3.5" /> <Horarios horarios={c.horarios} />
                </p>
                {c.professores.length > 0 && (
                  <p className="flex items-center gap-1 text-muted-foreground">
                    <UserRound className="h-3.5 w-3.5" /> {c.professores.join(', ')}
                  </p>
                )}
              </div>
              {graduacao && (
                <span className="text-muted-foreground sm:text-right">
                  {formatarData(c.inicio, { day: '2-digit', month: 'short' })} – {formatarData(c.fim)}
                </span>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
