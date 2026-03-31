import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '../api/client'
import type {
  BaixaContaReceberPayload,
  ContaReceberListResponse,
  ContaReceberResumo,
} from '../types/contasReceber'

export interface ContasReceberFilters {
  page?: number
  page_size?: number
  apenas_em_aberto?: boolean
  vencidas?: boolean
  cliente_id?: string
  cliente_nome?: string
}

export const useContasReceber = (filters: ContasReceberFilters) =>
  useQuery({
    queryKey: ['contas-receber', filters],
    queryFn: async () => {
      const response = await apiClient.get<ContaReceberListResponse>('/api/v1/contas-receber/', {
        params: filters,
      })
      return response.data
    },
    placeholderData: (previousData) => previousData,
  })

export const useContasReceberResumo = () =>
  useQuery({
    queryKey: ['contas-receber-resumo'],
    queryFn: async () => {
      const response = await apiClient.get<ContaReceberResumo>('/api/v1/contas-receber/resumo')
      return response.data
    },
    staleTime: 60_000,
  })

export const useBaixarContaReceber = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: BaixaContaReceberPayload }) => {
      const response = await apiClient.put(`/api/v1/contas-receber/${id}/baixar`, data)
      return response.data
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['contas-receber'] }),
        queryClient.invalidateQueries({ queryKey: ['contas-receber-resumo'] }),
      ])
    },
  })
}
