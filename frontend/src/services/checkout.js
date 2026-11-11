import api from '@/lib/api'

export const simularPreco = async ({ turma, codigo_cupom }) =>
  (await api.post('/checkout/preco/', { turma, codigo_cupom })).data

// Atenção: o payload pode conter dados de cartão — nunca registrar em log/storage.
export const finalizarMatricula = async (payload) => (await api.post('/checkout/', payload)).data

export const statusMatricula = async (token) => (await api.get(`/matriculas/${token}/`)).data
