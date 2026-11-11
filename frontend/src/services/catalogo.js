import api from '@/lib/api'

export const listarCatalogo = async ({ tipo, q } = {}) => {
  const params = {}
  if (tipo) params.tipo = tipo
  if (q) params.q = q
  const { data } = await api.get('/catalogo/', { params })
  return data
}

export const obterCurso = async (slug) => (await api.get(`/cursos/${slug}/`)).data

export const obterFormacao = async (slug) => (await api.get(`/formacoes/${slug}/`)).data

export const obterTurma = async (id) => (await api.get(`/turmas/${id}/`)).data

export const listarProfessores = async ({ home } = {}) =>
  (await api.get('/professores/', { params: home ? { home: 1 } : {} })).data
