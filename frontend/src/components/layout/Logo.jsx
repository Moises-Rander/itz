import { Link } from 'react-router-dom'
import { cn } from '@/lib/utils'
import logoDark from '@/assets/itz-logo-dark.svg' // texto branco — para fundos escuros
import logoLight from '@/assets/itz-logo-light.svg' // texto preto — para fundos claros

// `light` = true quando o logo está sobre fundo escuro (ex.: hero transparente),
// exibindo a versão de texto branco; caso contrário, a versão de texto preto.
export default function Logo({ className, light }) {
  return (
    <Link to="/" aria-label="Instituto de Teologia Zait" className="inline-flex items-center">
      <img
        src={light ? logoDark : logoLight}
        alt="Instituto de Teologia Zait"
        className={cn('h-9 w-auto', className)}
      />
    </Link>
  )
}
