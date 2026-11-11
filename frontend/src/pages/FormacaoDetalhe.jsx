import { Link, useParams } from 'react-router-dom'
import { Clock, Layers, BookOpen } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Spinner, ErrorState } from '@/components/common/StateComponents'
import { Cabecalho, Turmas, Professores } from '@/components/catalogo/DetalheSecoes'
import { useGraduacao } from '@/hooks/useCatalogo'
import { cargaHorariaLabel } from '@/lib/format'

const container = 'mx-auto max-w-6xl px-4 sm:px-6 lg:px-8'

function Grade({ modulos }) {
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
                  <div className="flex-1">
                    <p className="font-semibold">{m.nome}</p>
                    {m.descricao && <p className="mt-1 text-sm text-muted-foreground">{m.descricao}</p>}
                    <ul className="mt-3 divide-y rounded-lg border">
                      {m.cursos.map((c) => (
                        <li key={c.slug} className="flex items-center justify-between gap-3 p-3 text-sm">
                          <Link to={`/cursos/${c.slug}`} className="flex items-center gap-2 font-medium hover:text-primary">
                            <BookOpen className="h-4 w-4 text-primary" /> {c.nome}
                          </Link>
                          <span className="shrink-0 text-muted-foreground">{cargaHorariaLabel(c.carga_horaria)}</span>
                        </li>
                      ))}
                    </ul>
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

export default function GraduacaoDetalhe() {
  const { slug } = useParams()
  const { data: grad, isLoading, isError, refetch } = useGraduacao(slug)

  if (isLoading) return <div className={`${container} py-16`}><Spinner label="Carregando graduação..." /></div>
  if (isError || !grad) return <div className={`${container} py-16`}><ErrorState onRetry={refetch} /></div>

  const qtdCursos = grad.modulos.reduce((n, m) => n + m.cursos.length, 0)

  return (
    <div className="pb-16">
      <Cabecalho
        badge="Graduação"
        nome={grad.nome}
        descricao={grad.descricao}
        imagem={grad.imagem}
        info={
          <>
            <span className="flex items-center gap-2"><Clock className="h-4 w-4" /> {cargaHorariaLabel(grad.carga_horaria)}</span>
            <span className="flex items-center gap-2"><Layers className="h-4 w-4" /> {grad.modulos.length} módulos · {qtdCursos} cursos</span>
          </>
        }
      />
      <div className={`${container} pt-12`}>
        <Grade modulos={grad.modulos} />
        <Turmas turmas={grad.turmas} graduacao />
        <Professores turmas={grad.turmas} />
      </div>
    </div>
  )
}
