import { useMutation, useQuery } from '@tanstack/react-query'
import { simularPreco, finalizarMatricula, statusMatricula } from '@/services/checkout'

export const usePreco = (turma, codigoCupom) =>
  useQuery({
    queryKey: ['preco', turma, codigoCupom],
    queryFn: () => simularPreco({ turma, codigo_cupom: codigoCupom }),
    enabled: !!turma,
    retry: false,
    staleTime: 0,
  })

export const useFinalizarMatricula = () => useMutation({ mutationFn: finalizarMatricula })

// Enquanto o PIX não é pago, consulta a cada 5 s (o backend confirma com o Asaas).
export const useStatusMatricula = (token) =>
  useQuery({
    queryKey: ['matricula', token],
    queryFn: () => statusMatricula(token),
    enabled: !!token,
    retry: 1,
    staleTime: 0,
    refetchInterval: (query) => (query.state.data?.status === 'PENDENTE' ? 5000 : false),
  })
