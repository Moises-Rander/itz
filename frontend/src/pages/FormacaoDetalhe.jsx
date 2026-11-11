import { useParams } from 'react-router-dom'
import { Clock, Layers, PlayCircle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Spinner, ErrorState } from '@/components/common/StateComponents'
import { Cabecalho, Turmas, Professores } from '@/components/catalogo/DetalheSecoes'
import ListaAulas from '@/components/catalogo/ListaAulas'
import { useFormacao } from '@/hooks/useCatalogo'
import { cargaHorariaLabel } from '@/lib/format'

const container = 'mx-auto max-w-6xl px-4 sm:px-6 lg:px-8'

function Grade({ modulos }) {
  if (!modulos.length) return null
  return (
    <section>
      <h2 className="mb-5 flex items-center gap-2 text-2xl font-bold">
        <Layers className="h-6 w-6 text-primary" /> Grade curricular
      </h2>
      <ol className="space-y-4">
        {modulos.map((m) => (
          <li key={m.ordem}>
            <Card>
              <CardContent>
                <div className="flex gap-4">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground">
                    {m.ordem}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold">{m.nome}</p>
                    <div className="mt-3">
                      <ListaAulas aulas={m.aulas} />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
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
      <div className={`${container} pt-12`}>
        <Grade modulos={formacao.modulos} />
        <Turmas turmas={formacao.turmas} />
        <Professores turmas={formacao.turmas} />
      </div>
    </div>
  )
}
