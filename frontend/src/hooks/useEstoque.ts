import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '../api/client'
import type {
  EstoqueAlerta,
  EstoqueListResponse,
  MovimentacaoEstoque,
  TransacaoEstoquePayload,
} from '../types/estoque'

export interface EstoqueFilters {
  page?: number
  page_size?: number
  search?: string
  apenas_baixo?: boolean
}

export const useEstoqueCompleto = (filters: EstoqueFilters) =>
  useQuery({
    queryKey: ['estoque', filters],
    queryFn: async () => {
      const response = await apiClient.get<EstoqueListResponse>('/api/v2/estoque/', {
        params: filters,
      })
      return response.data
    },
    placeholderData: (previousData) => previousData,
  })

export const useEstoqueProduto = (produtoId?: number) =>
  useQuery({
    queryKey: ['estoque', 'produto', produtoId],
    queryFn: async () => {
      const response = await apiClient.get<MovimentacaoEstoque[]>(`/api/v2/estoque/historico/${produtoId}`)
      return response.data
    },
    enabled: Boolean(produtoId),
  })

export const useEstoqueAlertas = () =>
  useQuery({
    queryKey: ['dashboard', 'estoque-alertas'],
    queryFn: async () => {
      const response = await apiClient.get<EstoqueAlerta[]>('/api/v2/estoque/alertas')
      return Array.isArray(response.data) ? response.data : []
    },
    staleTime: 60_000,
    refetchInterval: 60_000,
  })

export const useRegistrarTransacao = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: TransacaoEstoquePayload) => {
      const response = await apiClient.post('/api/v2/estoque/transacao', payload)
      return response.data
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['estoque'] }),
        queryClient.invalidateQueries({ queryKey: ['dashboard', 'estoque-alertas'] }),
      ])
    },
  })
}
