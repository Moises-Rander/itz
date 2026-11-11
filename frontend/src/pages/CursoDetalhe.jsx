import { useParams } from 'react-router-dom'
import { Clock, BookOpen, PlayCircle } from 'lucide-react'
import { Spinner, ErrorState } from '@/components/common/StateComponents'
import { Cabecalho, Turmas, Professores } from '@/components/catalogo/DetalheSecoes'
import ListaAulas from '@/components/catalogo/ListaAulas'
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
        info={
          <>
            <span className="flex items-center gap-2"><Clock className="h-4 w-4" /> {cargaHorariaLabel(curso.carga_horaria)}</span>
            {curso.aulas.length > 0 && (
              <span className="flex items-center gap-2"><PlayCircle className="h-4 w-4" /> {curso.aulas.length} aulas</span>
            )}
          </>
        }
      />
      <div className={`${container} pt-12`}>
        {curso.aulas.length > 0 && (
          <section>
            <h2 className="mb-5 flex items-center gap-2 text-2xl font-bold">
              <BookOpen className="h-6 w-6 text-primary" /> Aulas
            </h2>
            <ListaAulas aulas={curso.aulas} />
          </section>
        )}

        <Turmas turmas={curso.turmas} />
        <Professores turmas={curso.turmas} />
      </div>
    </div>
  )
}
