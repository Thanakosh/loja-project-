import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '../api/client'
import type { CaixaAberturaPayload, CaixaDiario, CaixaFechamentoPayload } from '../types/caixa'

export const useCaixaAtual = () =>
  useQuery({
    queryKey: ['caixa-atual'],
    queryFn: async () => {
      try {
        const response = await apiClient.get<CaixaDiario>('/api/v1/caixa/atual')
        return response.data
      } catch {
        return null
      }
    },
    retry: false,
  })

export const useHistoricoCaixa = (limit = 20) =>
  useQuery({
    queryKey: ['caixa-historico', limit],
    queryFn: async () => {
      const response = await apiClient.get<CaixaDiario[]>('/api/v1/caixa/historico', {
        params: { limit },
      })
      return response.data
    },
  })

export const useAbrirCaixa = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: CaixaAberturaPayload) => {
      const response = await apiClient.post<CaixaDiario>('/api/v1/caixa/abrir', payload)
      return response.data
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['caixa-atual'] }),
        queryClient.invalidateQueries({ queryKey: ['caixa-historico'] }),
      ])
    },
  })
}

export const useFecharCaixa = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ caixaId, payload }: { caixaId: number; payload: CaixaFechamentoPayload }) => {
      const response = await apiClient.post<CaixaDiario>(`/api/v1/caixa/${caixaId}/fechar`, payload)
      return response.data
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['caixa-atual'] }),
        queryClient.invalidateQueries({ queryKey: ['caixa-historico'] }),
      ])
    },
  })
}
