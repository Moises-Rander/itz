import { Link } from 'react-router-dom'
import { Clock, ArrowRight, GraduationCap, CalendarDays, Layers } from 'lucide-react'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import Preco from './Preco'
import { tipoLabel, cargaHorariaLabel, formatarData } from '@/lib/format'

const linkProduto = (item) =>
  item.tipo === 'graduacao' ? `/graduacoes/${item.slug}` : `/cursos/${item.slug}`

// Card da vitrine: curso avulso ou graduação com turma disponível.
export default function ProdutoCard({ item }) {
  const destino = linkProduto(item)
  return (
    <Card className="flex flex-col overflow-hidden pt-0 transition-shadow hover:shadow-md">
      <Link to={destino} className="relative block h-44 w-full overflow-hidden bg-muted">
        {item.imagem ? (
          <img src={item.imagem} alt={item.nome} className="h-full w-full object-cover" loading="lazy" />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-muted-foreground">
            <GraduationCap className="h-10 w-10" />
          </div>
        )}
        <Badge className="absolute left-3 top-3" variant={item.tipo === 'graduacao' ? 'default' : 'secondary'}>
          {tipoLabel(item.tipo)}
        </Badge>
      </Link>

      <CardContent className="flex-1">
        <h3 className="line-clamp-2 text-lg font-semibold">
          <Link to={destino} className="hover:text-primary">{item.nome}</Link>
        </h3>
        {item.resumo && <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{item.resumo}</p>}
        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
          <span className="flex items-center gap-1">
            <Clock className="h-4 w-4" /> {cargaHorariaLabel(item.carga_horaria)}
          </span>
          {item.qtd_cursos && (
            <span className="flex items-center gap-1">
              <Layers className="h-4 w-4" /> {item.qtd_cursos} cursos
            </span>
          )}
          <span className="flex items-center gap-1">
            <CalendarDays className="h-4 w-4" /> Início {formatarData(item.proxima_turma.inicio)}
          </span>
        </div>
        <Preco preco={item.preco} className="mt-4" />
      </CardContent>

      <CardFooter>
        <Button asChild variant="outline" className="w-full">
          <Link to={destino}>
            Ver detalhes <ArrowRight className="ml-1 h-4 w-4" />
          </Link>
        </Button>
      </CardFooter>
    </Card>
  )
}
