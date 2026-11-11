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
            <Route path="/" element={<Home />} />
            <Route path="/cursos" element={<Catalogo />} />
            <Route path="/cursos/:slug" element={<CursoDetalhe />} />
            <Route path="/formacoes/:slug" element={<FormacaoDetalhe />} />
            <Route path="/graduacoes/:slug" element={<RedirecionaFormacao />} />
            <Route path="/sobre" element={<Sobre />} />
            <Route path="/contato" element={<Contato />} />
            <Route path="/termos" element={<Termos />} />
            <Route path="/matricula/status/:token" element={<StatusMatricula />} />
            <Route path="/matricula/:turmaId" element={<Checkout />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster richColors position="top-right" />
    </QueryClientProvider>
  )
}
