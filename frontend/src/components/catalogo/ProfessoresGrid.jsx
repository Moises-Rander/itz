import { UserRound } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'

export default function ProfessoresGrid({ professores, comBio }) {
  if (!professores?.length) return null
  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {professores.map((p) => (
        <Card key={p.id}>
          <CardContent className="flex gap-4">
            {p.foto ? (
              <img src={p.foto} alt={p.nome} className="h-16 w-16 shrink-0 rounded-full object-cover" />
            ) : (
              <span className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                <UserRound className="h-7 w-7" />
              </span>
            )}
            <div>
              <p className="font-semibold">{p.nome}</p>
              {p.titulacao && <p className="text-sm text-muted-foreground">{p.titulacao}</p>}
              {comBio && p.bio && <p className="mt-2 line-clamp-4 text-sm text-muted-foreground">{p.bio}</p>}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
