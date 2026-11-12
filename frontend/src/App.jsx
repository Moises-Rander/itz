import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from '@/components/ui/sonner'

import Layout from '@/components/layout/Layout'
import Home from '@/pages/Home'
import Catalogo from '@/pages/Catalogo'
import CursoDetalhe from '@/pages/CursoDetalhe'
import FormacaoDetalhe from '@/pages/FormacaoDetalhe'
import Sobre from '@/pages/Sobre'
import Contato from '@/pages/Contato'
import Checkout from '@/pages/Checkout'
import StatusMatricula from '@/pages/StatusMatricula'
import Termos from '@/pages/Termos'
import NotFound from '@/pages/NotFound'
import Seo from '@/components/common/Seo'

// Links antigos (/graduacoes/...) continuam funcionando.
function RedirecionaFormacao() {
  const { slug } = useParams()
  return <Navigate to={`/formacoes/${slug}`} replace />
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 5,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<><Seo /><Home /></>} />
            <Route path="/cursos" element={<><Seo titulo="Cursos e formações" descricao="Conheça os cursos e as formações em teologia do Instituto de Teologia Zait, com turmas em São Luís - MA." /><Catalogo /></>} />
            <Route path="/cursos/:slug" element={<CursoDetalhe />} />
            <Route path="/formacoes/:slug" element={<FormacaoDetalhe />} />
            <Route path="/graduacoes/:slug" element={<RedirecionaFormacao />} />
            <Route path="/sobre" element={<><Seo titulo="Sobre" /><Sobre /></>} />
            <Route path="/contato" element={<><Seo titulo="Contato" descricao="Fale com o Instituto de Teologia Zait: telefone, WhatsApp, e-mail e endereço em São Luís - MA." /><Contato /></>} />
            <Route path="/termos" element={<><Seo titulo="Termos de uso" /><Termos /></>} />
            <Route path="/matricula/status/:token" element={<><Seo titulo="Status da matrícula" noindex /><StatusMatricula /></>} />
            <Route path="/matricula/:turmaId" element={<><Seo titulo="Matrícula" noindex /><Checkout /></>} />
            <Route path="*" element={<><Seo titulo="Página não encontrada" noindex /><NotFound /></>} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster richColors position="top-right" />
    </QueryClientProvider>
  )
}
