import axios from 'axios'
import { API_URL } from '@/lib/config'

// Instância central do Axios. A URL base vem de VITE_API_URL.
export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Mensagem de erro amigável (sem expor detalhes técnicos ao usuário).
export function mensagemErro(error, fallback = 'Não foi possível carregar as informações. Tente novamente em instantes.') {
  const status = error?.response?.status
  if (status === 404) return 'Conteúdo não encontrado.'
  if (status >= 500) return 'Nossos servidores estão indisponíveis no momento. Tente novamente mais tarde.'
  return fallback
}

export default api
