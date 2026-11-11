import { useQuery } from '@tanstack/react-query'
import {
  listarConteudo,
  listarEquipe,
  listarDepoimentos,
} from '@/services/cms'

export const useConteudo = (secao) =>
  useQuery({
    queryKey: ['conteudo', secao || 'todos'],
    queryFn: () => listarConteudo(secao),
  })

export const useEquipe = () =>
  useQuery({ queryKey: ['equipe'], queryFn: listarEquipe })

export const useDepoimentos = () =>
  useQuery({ queryKey: ['depoimentos'], queryFn: listarDepoimentos })
