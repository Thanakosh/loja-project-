import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '../api/client'
import type { Venda, VendaPDVCreate, VendaPDVRead, VendasPaginadas, VendasParams } from '../types/vendas'

const getVendaTotal = (total: number | string | null | undefined) => {
  if (typeof total === 'number') {
    return total
  }

  const parsedValue = Number(total)
  return Number.isFinite(parsedValue) ? parsedValue : 0
}

export const useVendas = (params: VendasParams) =>
  useQuery({
    queryKey: ['vendas', params],
    queryFn: async () => {
      const response = await apiClient.get<VendasPaginadas>('/api/v1/vendas/', {
        params,
      })
      return response.data
    },
    placeholderData: (previousData) => previousData,
  })

export const useVenda = (vendaId?: number) =>
  useQuery({
    queryKey: ['vendas', 'detalhe', vendaId],
    queryFn: async () => {
      const response = await apiClient.get<Venda>(`/api/v1/vendas/${vendaId}`)
      return response.data
    },
    enabled: Boolean(vendaId),
  })

export const useVendasTotal = (params: VendasParams, key: string) =>
  useQuery({
    queryKey: ['dashboard', key, params],
    queryFn: async () => {
      const response = await apiClient.get<VendasPaginadas | Venda[]>('/api/v1/vendas/', {
        params,
      })

      const vendas = Array.isArray(response.data) ? response.data : response.data.items ?? []
      return vendas.reduce((accumulator, venda) => accumulator + getVendaTotal(venda.total), 0)
    },
    staleTime: 60_000,
    refetchInterval: 60_000,
  })

export const useRegistrarVenda = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: VendaPDVCreate) => {
      const response = await apiClient.post<VendaPDVRead>('/api/v1/pdv/venda', payload)
      return response.data
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['vendas'] }),
        queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
      ])
    },
  })
}

export const useCancelarVenda = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (vendaId: number) => {
      await apiClient.post(`/api/v1/pdv/venda/${vendaId}/cancelar`)
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['vendas'] }),
        queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
      ])
    },
  })
}
