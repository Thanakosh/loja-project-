import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '../api/client'
import type { Orcamento, OrcamentoListResponse, StatusOrcamento } from '../types/orcamentos'

export interface OrcamentosFilters {
  page?: number
  page_size?: number
  status?: StatusOrcamento
}

export interface ConverterOrcamentoPayload {
  orcamentoId: number
  forma_pagamento: number
  parcelas: number
}

export const useOrcamentos = (filters: OrcamentosFilters) =>
  useQuery({
    queryKey: ['orcamentos', filters],
    queryFn: async () => {
      const response = await apiClient.get<OrcamentoListResponse>('/api/v1/orcamentos/', {
        params: filters,
      })
      return response.data
    },
    placeholderData: (previousData) => previousData,
  })

export const useOrcamentosTotal = (filters: OrcamentosFilters) =>
  useQuery({
    queryKey: ['dashboard', 'orcamentos-total', filters],
    queryFn: async () => {
      const response = await apiClient.get<OrcamentoListResponse>('/api/v1/orcamentos/', {
        params: { ...filters, page_size: 1 },
      })
      return response.data.total ?? 0
    },
    staleTime: 60_000,
    refetchInterval: 60_000,
  })

export const useCreateOrcamento = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: unknown) => {
      const response = await apiClient.post<Orcamento>('/api/v1/orcamentos/', payload)
      return response.data
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['orcamentos'] })
    },
  })
}

export const useCancelarOrcamento = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (orcamentoId: number) => {
      await apiClient.delete(`/api/v1/orcamentos/${orcamentoId}`)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['orcamentos'] })
    },
  })
}

export const useConverterOrcamento = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ orcamentoId, forma_pagamento, parcelas }: ConverterOrcamentoPayload) => {
      await apiClient.post(`/api/v1/orcamentos/${orcamentoId}/converter`, {
        forma_pagamento,
        parcelas,
      })
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['orcamentos'] }),
        queryClient.invalidateQueries({ queryKey: ['vendas'] }),
        queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
      ])
    },
  })
}
