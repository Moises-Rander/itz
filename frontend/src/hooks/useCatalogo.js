import { useQuery } from '@tanstack/react-query'
import {
  listarCatalogo,
  obterCurso,
  obterFormacao,
  obterTurma,
  listarProfessores,
} from '@/services/catalogo'

export const useCatalogo = (filtros = {}) =>
  useQuery({ queryKey: ['catalogo', filtros], queryFn: () => listarCatalogo(filtros) })

export const useCurso = (slug) =>
  useQuery({ queryKey: ['curso', slug], queryFn: () => obterCurso(slug), enabled: !!slug })

export const useFormacao = (slug) =>
  useQuery({ queryKey: ['formacao', slug], queryFn: () => obterFormacao(slug), enabled: !!slug })

// Vagas e preço mudam: no checkout sempre busca a versão atual.
export const useTurma = (id) =>
  useQuery({ queryKey: ['turma', id], queryFn: () => obterTurma(id), enabled: !!id, staleTime: 0 })

export const useProfessores = (filtros = {}) =>
  useQuery({ queryKey: ['professores', filtros], queryFn: () => listarProfessores(filtros) })
