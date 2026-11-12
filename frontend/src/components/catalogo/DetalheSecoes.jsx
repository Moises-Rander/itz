import { Users } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/common/StateComponents'
import TurmaOferta from '@/components/catalogo/TurmaOferta'
import ProfessoresGrid from '@/components/catalogo/ProfessoresGrid'
import Seo from '@/components/common/Seo'

// Seções compartilhadas pelas páginas de detalhe de Curso e de Formação.
const container = 'mx-auto max-w-6xl px-4 sm:px-6 lg:px-8'

export function Cabecalho({ badge, nome, info, descricao, imagem }) {
  return (
    <section className="border-b bg-muted/40">
      <Seo titulo={nome} descricao={descricao} imagem={imagem} />
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

// Desktop: conteúdo à esquerda; turmas e professores numa coluna à direita.
// Celular: turmas → conteúdo → professores (a matrícula fica logo no topo).
export function LayoutDetalhe({ children, turmas }) {
  return (
    <div className={`${container} grid gap-12 pt-12 lg:grid-cols-3 lg:grid-rows-[auto_1fr] lg:gap-x-10`}>
      <div className="lg:col-start-3 lg:row-start-1">
        <Turmas turmas={turmas} />
      </div>
      <div className="min-w-0 lg:col-span-2 lg:col-start-1 lg:row-span-2 lg:row-start-1">{children}</div>
      <div className="lg:col-start-3 lg:row-start-2">
        <Professores turmas={turmas} />
      </div>
    </div>
  )
}

export function Turmas({ turmas }) {
  return (
    <section>
      <h2 className="mb-5 flex items-center gap-2 text-xl font-bold">
        <Users className="h-5 w-5 text-primary" /> Turmas com matrícula aberta
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
    <section>
      <h2 className="mb-5 text-xl font-bold">Professores</h2>
      <ProfessoresGrid professores={[...unicos.values()]} comBio coluna />
    </section>
  )
}
