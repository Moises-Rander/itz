import api from '@/lib/api'

export const listarConteudo = async (secao) => {
  const params = secao ? { secao } : {}
  const { data } = await api.get('/cms/conteudo/', { params })
  return data
}

export const listarEquipe = async () => {
  const { data } = await api.get('/cms/equipe/')
  return data
}

export const listarDepoimentos = async () => {
  const { data } = await api.get('/cms/depoimentos/')
  return data
}
