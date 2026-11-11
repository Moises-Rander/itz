import { useSearchParams } from 'react-router-dom'
import { Search } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import PageHeader from '@/components/common/PageHeader'
import ProdutoCard from '@/components/catalogo/ProdutoCard'
import { CardsSkeleton, ErrorState, EmptyState } from '@/components/common/StateComponents'
import { useCatalogo } from '@/hooks/useCatalogo'

const ABAS = [
  { value: '', label: 'Todos' },
  { value: 'graduacao', label: 'Graduações' },
  { value: 'curso', label: 'Cursos avulsos' },
]

export default function Catalogo() {
  const [params, setParams] = useSearchParams()
  const tipo = params.get('tipo') || ''
  const q = params.get('q') || ''
  const { data, isLoading, isError, refetch } = useCatalogo({ tipo, q })

  const atualizar = (chave, valor) => {
    const novo = new URLSearchParams(params)
    if (valor) novo.set(chave, valor)
    else novo.delete(chave)
    setParams(novo, { replace: true })
  }

  return (
    <>
      <PageHeader
        title="Cursos e Graduações"
        subtitle="Faça uma graduação completa ou escolha cursos avulsos. Só aparecem aqui as turmas com matrícula aberta."
      />
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap gap-2">
            {ABAS.map((a) => (
              <Button
                key={a.value || 'todos'}
                variant={tipo === a.value ? 'default' : 'outline'}
                size="sm"
                onClick={() => atualizar('tipo', a.value)}
              >
                {a.label}
              </Button>
            ))}
          </div>
          <div className="relative w-full sm:max-w-xs">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={q}
              onChange={(e) => atualizar('q', e.target.value)}
              placeholder="Buscar por nome..."
              className="pl-9"
            />
          </div>
        </div>

        {isLoading && <CardsSkeleton count={6} />}
        {isError && <ErrorState onRetry={refetch} />}
        {data &&
          (data.length === 0 ? (
            <EmptyState message="Nenhuma turma com matrícula aberta no momento. Volte em breve!" />
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {data.map((item) => (
                <ProdutoCard key={`${item.tipo}-${item.slug}`} item={item} />
              ))}
            </div>
          ))}
      </div>
    </>
  )
}
