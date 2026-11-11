import { Link, useParams } from 'react-router-dom'
import { Clock, BookOpen, Layers, ArrowRight } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Spinner, ErrorState } from '@/components/common/StateComponents'
import { Cabecalho, Turmas, Professores } from '@/components/catalogo/DetalheSecoes'
import { useCurso } from '@/hooks/useCatalogo'
import { cargaHorariaLabel } from '@/lib/format'

const container = 'mx-auto max-w-6xl px-4 sm:px-6 lg:px-8'

export default function CursoDetalhe() {
  const { slug } = useParams()
  const { data: curso, isLoading, isError, refetch } = useCurso(slug)

  if (isLoading) return <div className={`${container} py-16`}><Spinner label="Carregando curso..." /></div>
  if (isError || !curso) return <div className={`${container} py-16`}><ErrorState onRetry={refetch} /></div>

  return (
    <div className="pb-16">
      <Cabecalho
        badge="Curso"
        nome={curso.nome}
        descricao={curso.descricao}
        imagem={curso.imagem}
        info={<span className="flex items-center gap-2"><Clock className="h-4 w-4" /> {cargaHorariaLabel(curso.carga_horaria)}</span>}
      />
      <div className={`${container} pt-12`}>
        {curso.ementa && (
          <section>
            <h2 className="mb-4 flex items-center gap-2 text-2xl font-bold">
              <BookOpen className="h-6 w-6 text-primary" /> Ementa
            </h2>
            <p className="whitespace-pre-line text-muted-foreground">{curso.ementa}</p>
          </section>
        )}

        <Turmas turmas={curso.turmas} />
        <Professores turmas={curso.turmas} />

        {curso.graduacoes.length > 0 && (
          <section className="mt-12">
            <h2 className="mb-2 flex items-center gap-2 text-2xl font-bold">
              <Layers className="h-6 w-6 text-primary" /> Este curso faz parte de
            </h2>
            <p className="mb-5 text-muted-foreground">
              Na graduação você faz este e outros cursos, com valor menor que a soma dos avulsos.
            </p>
            <div className="grid gap-4 sm:grid-cols-2">
              {curso.graduacoes.map((g) => (
                <Card key={g.slug}>
                  <CardContent>
                    <Link to={`/graduacoes/${g.slug}`} className="flex items-center justify-between gap-3 font-semibold hover:text-primary">
                      {g.nome} <ArrowRight className="h-4 w-4 shrink-0" />
                    </Link>
                    {g.resumo && <p className="mt-1 text-sm text-muted-foreground">{g.resumo}</p>}
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
