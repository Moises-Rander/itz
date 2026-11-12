import { useParams } from 'react-router-dom'
import { ChevronDown, Clock, Layers, PlayCircle } from 'lucide-react'
import { Spinner, ErrorState } from '@/components/common/StateComponents'
import { Cabecalho, LayoutDetalhe } from '@/components/catalogo/DetalheSecoes'
import ListaAulas from '@/components/catalogo/ListaAulas'
import { useFormacao } from '@/hooks/useCatalogo'
import { cargaHorariaLabel } from '@/lib/format'

const container = 'mx-auto max-w-6xl px-4 sm:px-6 lg:px-8'

// Módulos recolhidos por padrão: clicar abre a lista de aulas.
function Grade({ modulos }) {
  return (
    <section>
      <h2 className="mb-5 flex items-center gap-2 text-2xl font-bold">
        <Layers className="h-6 w-6 text-primary" /> Grade curricular
      </h2>
      {!modulos.length && <p className="text-sm text-muted-foreground">Grade a definir.</p>}
      <ol className="divide-y overflow-hidden empty:hidden rounded-xl border bg-card">
        {modulos.map((m) => (
          <li key={m.ordem}>
            <details className="group">
              <summary className="flex cursor-pointer list-none items-center gap-3 px-4 py-3 transition-colors hover:bg-muted/50 [&::-webkit-details-marker]:hidden">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                  {m.ordem}
                </span>
                <span className="min-w-0 flex-1 font-medium">{m.nome}</span>
                <span className="hidden shrink-0 text-sm text-muted-foreground sm:inline">
                  {m.aulas.length} aula{m.aulas.length === 1 ? '' : 's'}
                </span>
                <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-open:rotate-180" />
              </summary>
              <div className="px-4 pb-4 sm:pl-14">
                <ListaAulas aulas={m.aulas} />
              </div>
            </details>
          </li>
        ))}
      </ol>
    </section>
  )
}

export default function FormacaoDetalhe() {
  const { slug } = useParams()
  const { data: formacao, isLoading, isError, refetch } = useFormacao(slug)

  if (isLoading) return <div className={`${container} py-16`}><Spinner label="Carregando formação..." /></div>
  if (isError || !formacao) return <div className={`${container} py-16`}><ErrorState onRetry={refetch} /></div>

  const qtdAulas = formacao.modulos.reduce((n, m) => n + m.aulas.length, 0)

  return (
    <div className="pb-16">
      <Cabecalho
        badge="Formação"
        nome={formacao.nome}
        descricao={formacao.descricao}
        imagem={formacao.imagem}
        info={
          <>
            <span className="flex items-center gap-2"><Clock className="h-4 w-4" /> {cargaHorariaLabel(formacao.carga_horaria)}</span>
            <span className="flex items-center gap-2"><Layers className="h-4 w-4" /> {formacao.modulos.length} módulos</span>
            {qtdAulas > 0 && (
              <span className="flex items-center gap-2"><PlayCircle className="h-4 w-4" /> {qtdAulas} aulas</span>
            )}
          </>
        }
      />
      <LayoutDetalhe turmas={formacao.turmas}>
        <Grade modulos={formacao.modulos} />
      </LayoutDetalhe>
    </div>
  )
}
