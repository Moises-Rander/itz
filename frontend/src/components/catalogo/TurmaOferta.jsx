import { Link } from 'react-router-dom'
import { CalendarDays, Clock, MapPin, UserRound, GraduationCap } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import Preco from './Preco'
import { periodoLabel } from '@/lib/format'
import { CONTATO } from '@/lib/config'

const horariosLabel = (horarios) =>
  horarios?.length
    ? horarios.map((h) => `${h.dia} ${h.inicio}–${h.fim}`).join(' · ')
    : 'Horários a definir'

// Uma turma disponível: período, horários, professores, vagas, preço e matrícula.
export default function TurmaOferta({ turma }) {
  return (
    <Card>
      <CardContent>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-1 text-sm text-muted-foreground">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <h3 className="text-lg font-semibold text-foreground">Turma {turma.codigo}</h3>
              <Badge variant="outline">
                {turma.vagas_disponiveis} vaga{turma.vagas_disponiveis === 1 ? '' : 's'}
              </Badge>
            </div>
            <p className="flex items-center gap-2">
              <CalendarDays className="h-4 w-4 shrink-0" /> {periodoLabel(turma.inicio, turma.fim)}
            </p>
            <p className="flex items-center gap-2">
              <Clock className="h-4 w-4 shrink-0" /> {horariosLabel(turma.horarios)}
            </p>
            {turma.professores.length > 0 && (
              <p className="flex items-center gap-2">
                <UserRound className="h-4 w-4 shrink-0" /> {turma.professores.map((p) => p.nome).join(', ')}
              </p>
            )}
            <p className="flex items-center gap-2">
              <MapPin className="h-4 w-4 shrink-0" /> Presencial — {CONTATO.endereco}
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
      </CardContent>
    </Card>
  )
}
