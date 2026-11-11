import { Link } from 'react-router-dom'
import { ArrowRight, Quote } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import SectionTitle from '@/components/common/SectionTitle'
import ProdutoCard from '@/components/catalogo/ProdutoCard'
import ProfessoresGrid from '@/components/catalogo/ProfessoresGrid'
import LeadForm from '@/components/forms/LeadForm'
import ContactInfo from '@/components/common/ContactInfo'
import { CardsSkeleton, ErrorState, EmptyState } from '@/components/common/StateComponents'
import { useCatalogo, useProfessores } from '@/hooks/useCatalogo'
import { useConteudo, useDepoimentos } from '@/hooks/useCms'
import { HERO, INSTITUICAO } from '@/lib/config'

const container = 'mx-auto max-w-7xl px-4 sm:px-6 lg:px-8'

function Hero() {
  // Conteúdo do hero gerenciável pelo Django Admin (seção HERO); com fallback
  // para a config local (env) quando não houver cadastro.
  const { data } = useConteudo('HERO')
  const bloco = data?.[0]
  const imagem = bloco?.imagem || HERO.imagem
  const titulo = bloco?.titulo || HERO.titulo
  const subtitulo = bloco?.texto || HERO.subtitulo

  return (
    <section className="relative flex min-h-[90vh] items-center">
      {/* Fundo via CSS (falha silenciosamente se a imagem não carregar) sobre cor escura. */}
      <div
        className="absolute inset-0 -z-10 bg-slate-900 bg-cover bg-center"
        style={imagem ? { backgroundImage: `url(${imagem})` } : undefined}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-slate-900/85 to-slate-900/55" />
      </div>
      <div className={container}>
        <div className="max-w-2xl py-24 text-white">
          <h1 className="text-4xl font-bold leading-tight tracking-tight sm:text-5xl lg:text-6xl">
            {titulo}
          </h1>
          <p className="mt-5 text-lg text-white/85">{subtitulo}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link to="/cursos">Conheça nossos cursos</Link>
            </Button>
            <Button asChild size="lg" variant="secondary">
              <Link to="/contato">Fale conosco</Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
}

function CursosDestaque() {
  // O catálogo já vem com as formações primeiro.
  const { data, isLoading, isError, refetch } = useCatalogo()

  return (
    <section className={`${container} py-20`}>
      <SectionTitle
        eyebrow="Nossos cursos"
        title="Cursos em destaque"
        subtitle="Faça uma formação completa ou comece por um curso avulso."
      />
      <div className="mt-10">
        {isLoading && <CardsSkeleton count={6} />}
        {isError && <ErrorState onRetry={refetch} />}
        {data && (data.length === 0 ? (
          <EmptyState message="Em breve, novas turmas por aqui." />
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {data.slice(0, 6).map((item) => (
              <ProdutoCard key={`${item.tipo}-${item.slug}`} item={item} />
            ))}
          </div>
        ))}
      </div>
      <div className="mt-10 text-center">
        <Button asChild variant="outline" size="lg">
          <Link to="/cursos">
            Ver todos os cursos <ArrowRight className="ml-1 h-4 w-4" />
          </Link>
        </Button>
      </div>
    </section>
  )
}

function SobreResumo() {
  const { data, isLoading, isError } = useConteudo('SOBRE')
  const bloco = data?.[0]
  if (isLoading || isError || !bloco) return null

  return (
    <section className="bg-muted/40 py-20">
      <div className={`${container} grid items-center gap-10 lg:grid-cols-2`}>
        <div>
          <SectionTitle eyebrow={`Sobre o ${INSTITUICAO.sigla}`} title={bloco.titulo} />
          <p className="mt-4 whitespace-pre-line text-muted-foreground">{bloco.texto}</p>
          <Button asChild className="mt-6" variant="outline">
            <Link to="/sobre">Saiba mais sobre nós</Link>
          </Button>
        </div>
        {bloco.imagem && (
          <img
            src={bloco.imagem}
            alt={bloco.titulo}
            className="h-80 w-full rounded-2xl object-cover shadow-sm"
          />
        )}
      </div>
    </section>
  )
}

function Professores() {
  const { data } = useProfessores({ home: true })
  if (!data?.length) return null
  return (
    <section className={`${container} py-20`}>
      <SectionTitle center eyebrow="Corpo docente" title="Nossos professores" />
      <div className="mt-10">
        <ProfessoresGrid professores={data} comBio />
      </div>
    </section>
  )
}

function Depoimentos() {
  const { data, isLoading, isError } = useDepoimentos()
  if (isLoading || isError || !data || data.length === 0) return null

  return (
    <section className={`${container} py-20`}>
      <SectionTitle center eyebrow="Depoimentos" title="O que dizem nossos alunos" />
      <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {data.map((d) => (
          <Card key={d.id}>
            <CardContent>
              <Quote className="h-8 w-8 text-primary/30" />
              <p className="mt-3 text-sm text-muted-foreground">{d.texto}</p>
              <div className="mt-5 flex items-center gap-3">
                {d.foto ? (
                  <img src={d.foto} alt={d.nome_aluno} className="h-10 w-10 rounded-full object-cover" />
                ) : (
                  <span className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 font-semibold text-primary">
                    {d.nome_aluno?.[0]}
                  </span>
                )}
                <div>
                  <p className="text-sm font-semibold">{d.nome_aluno}</p>
                  <p className="text-xs text-muted-foreground">{d.nome_curso}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  )
}

function ContatoRapido() {
  return (
    <section className="bg-muted/40 py-20">
      <div className={`${container} grid gap-10 lg:grid-cols-2`}>
        <div>
          <SectionTitle eyebrow="Fale conosco" title="Ficou com alguma dúvida?" subtitle="Envie uma mensagem e nossa equipe entrará em contato." />
          <div className="mt-8">
            <LeadForm />
          </div>
        </div>
        <div className="lg:pl-10">
          <h3 className="text-lg font-semibold">Informações de contato</h3>
          <div className="mt-6">
            <ContactInfo />
          </div>
        </div>
      </div>
    </section>
  )
}

export default function Home() {
  return (
    <>
      <Hero />
      <CursosDestaque />
      <SobreResumo />
      <Professores />
      <Depoimentos />
      <ContatoRapido />
    </>
  )
}
