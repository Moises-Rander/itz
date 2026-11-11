import { formatarBRL } from '@/lib/format'
import { cn } from '@/lib/utils'

// Destaque no parcelado ("12x de R$ X") com o valor à vista abaixo, como nas
// grandes plataformas de cursos. Mostra o preço cheio riscado se houver promoção.
export default function Preco({ preco, className, grande }) {
  if (!preco) return null
  const { parcelamento } = preco
  const temPromo = Number(preco.desconto_promocao) > 0
  return (
    <div className={cn('leading-tight', className)}>
      {temPromo && (
        <p className="text-xs text-muted-foreground">
          <span className="line-through">{formatarBRL(preco.valor_original)}</span>
          {preco.promocao && <span className="ml-1 font-medium text-primary">{preco.promocao}</span>}
        </p>
      )}
      {parcelamento && parcelamento.parcelas > 1 ? (
        <>
          <p className={cn('font-bold', grande ? 'text-2xl' : 'text-lg')}>
            {parcelamento.parcelas}x de {formatarBRL(parcelamento.valor_parcela)}
          </p>
          <p className="text-xs text-muted-foreground">
            ou {formatarBRL(preco.valor_a_vista)} à vista
          </p>
        </>
      ) : (
        <p className={cn('font-bold', grande ? 'text-2xl' : 'text-lg')}>
          {formatarBRL(preco.valor_a_vista)}
        </p>
      )}
    </div>
  )
}
