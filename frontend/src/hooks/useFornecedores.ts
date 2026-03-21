import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '../api/client'
import type { Fornecedor, FornecedorPayload } from '../types/fornecedores'

export interface FornecedoresFilters {
  search?: string
  limit?: number
  skip?: number
}

export const useFornecedores = (filters: FornecedoresFilters) =>
  useQuery({
    queryKey: ['fornecedores', filters],
    queryFn: async () => {
      const response = await apiClient.get<Fornecedor[]>('/api/v1/fornecedores/', {
        params: filters,
      })
      return response.data
    },
    placeholderData: (previousData) => previousData,
  })

export const useCreateFornecedor = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: FornecedorPayload) => {
      const response = await apiClient.post<Fornecedor>('/api/v1/fornecedores/', payload)
      return response.data
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['fornecedores'] })
    },
  })
}

export const useUpdateFornecedor = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: FornecedorPayload }) => {
      const response = await apiClient.put<Fornecedor>(`/api/v1/fornecedores/${id}`, payload)
      return response.data
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['fornecedores'] })
    },
  })
}
