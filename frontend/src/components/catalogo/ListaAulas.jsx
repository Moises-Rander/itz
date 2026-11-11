import { PlayCircle } from 'lucide-react'

// Aulas em ordem (de um curso ou de um módulo de formação).
export default function ListaAulas({ aulas }) {
  if (!aulas.length) return <p className="text-sm text-muted-foreground">Aulas a definir.</p>
  return (
    <ol className="divide-y rounded-lg border">
      {aulas.map((a, i) => (
        <li key={`${a.ordem}-${i}`} className="flex items-center gap-3 p-3 text-sm">
          <PlayCircle className="h-4 w-4 shrink-0 text-primary" />
          <span className="w-6 shrink-0 text-muted-foreground">{i + 1}.</span>
          <span className="font-medium">{a.nome}</span>
        </li>
      ))}
    </ol>
  )
}
