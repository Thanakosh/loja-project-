import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '../api/client'
import type { Cliente, ClientePayload } from '../types/clientes'

export interface ClientesFilters {
  search?: string
  limit?: number
  skip?: number
}

export const useClientes = (filters: ClientesFilters) =>
  useQuery({
    queryKey: ['clientes', filters],
    queryFn: async () => {
      const response = await apiClient.get<Cliente[]>('/api/v1/clientes/', {
        params: filters,
      })
      return response.data
    },
    placeholderData: (previousData) => previousData,
  })

export const useCreateCliente = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: ClientePayload) => {
      const response = await apiClient.post<Cliente>('/api/v1/clientes/', payload)
      return response.data
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['clientes'] })
    },
  })
}

export const useUpdateCliente = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: ClientePayload }) => {
      const response = await apiClient.put<Cliente>(`/api/v1/clientes/${id}`, payload)
      return response.data
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['clientes'] })
    },
  })
}
