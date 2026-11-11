import { Users } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/common/StateComponents'
import TurmaOferta from '@/components/catalogo/TurmaOferta'
import ProfessoresGrid from '@/components/catalogo/ProfessoresGrid'

// Seções compartilhadas pelas páginas de detalhe de Curso e de Formação.
const container = 'mx-auto max-w-6xl px-4 sm:px-6 lg:px-8'

export function Cabecalho({ badge, nome, info, descricao, imagem }) {
  return (
    <section className="border-b bg-muted/40">
      <div className={`${container} grid gap-8 py-12 lg:grid-cols-2`}>
        <div>
          <Badge variant="secondary">{badge}</Badge>
          <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">{nome}</h1>
          <div className="mt-4 flex flex-wrap gap-x-5 gap-y-1 text-muted-foreground">{info}</div>
          {descricao && <p className="mt-5 whitespace-pre-line text-muted-foreground">{descricao}</p>}
        </div>
        {imagem && <img src={imagem} alt={nome} className="h-72 w-full rounded-2xl object-cover shadow-sm" />}
      </div>
    </section>
  )
}

export function Turmas({ turmas }) {
  return (
    <section className="mt-12">
      <h2 className="mb-5 flex items-center gap-2 text-2xl font-bold">
        <Users className="h-6 w-6 text-primary" /> Turmas com matrícula aberta
      </h2>
      {turmas.length === 0 ? (
        <EmptyState message="Nenhuma turma aberta no momento. Volte em breve!" />
      ) : (
        <div className="space-y-4">
          {turmas.map((t) => <TurmaOferta key={t.id} turma={t} />)}
        </div>
      )}
    </section>
  )
}

export function Professores({ turmas }) {
  const unicos = new Map()
  turmas.forEach((t) => t.professores.forEach((p) => unicos.set(p.id, p)))
  if (unicos.size === 0) return null
  return (
    <section className="mt-12">
      <h2 className="mb-5 text-2xl font-bold">Professores</h2>
      <ProfessoresGrid professores={[...unicos.values()]} comBio />
    </section>
  )
}
