import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '../api/client'
import type {
  CategoriaTreeNode,
  DuplicateCheckResponse,
  Produto,
  ProdutoFormPayload,
  ProdutoListResponse,
  ProdutoMutationResult,
} from '../types/produtos'

export interface ProdutosFilters {
  page?: number
  page_size?: number
  incluir_inativos?: boolean
  search?: string
  categoria_id?: number
}

export const useProdutos = (filters: ProdutosFilters) =>
  useQuery({
    queryKey: ['produtos', filters],
    queryFn: async () => {
      const response = await apiClient.get<ProdutoListResponse>('/api/v1/produtos/', {
        params: filters,
      })
      return response.data
    },
    placeholderData: (previousData) => previousData,
  })

export const useProduto = (produtoId?: number) =>
  useQuery({
    queryKey: ['produtos', 'detalhe', produtoId],
    queryFn: async () => {
      const response = await apiClient.get<Produto>(`/api/v1/produtos/${produtoId}`)
      return response.data
    },
    enabled: Boolean(produtoId),
  })

export const useProdutosTotal = () =>
  useQuery({
    queryKey: ['dashboard', 'produtos-total'],
    queryFn: async () => {
      const response = await apiClient.get<ProdutoListResponse>('/api/v1/produtos/', {
        params: { page: 1, page_size: 1 },
      })
      return response.data.total ?? 0
    },
    staleTime: 60_000,
    refetchInterval: 60_000,
  })

export const useCategoriasArvore = () =>
  useQuery({
    queryKey: ['categorias-arvore'],
    queryFn: async () => {
      const response = await apiClient.get<CategoriaTreeNode[]>('/api/v1/categorias/arvore')
      return response.data
    },
    staleTime: 300_000,
  })

export const useCheckProdutoDuplicate = () =>
  useMutation({
    mutationFn: async (descricao: string) => {
      const response = await apiClient.post<DuplicateCheckResponse>('/api/v1/ai/check-duplicate', {
        descricao,
        limite: 3,
      })
      return response.data
    },
  })

export const useCreateProduto = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: ProdutoFormPayload) => {
      const response = await apiClient.post<Produto>('/api/v1/produtos/', payload)
      return {
        data: response.data,
        acao: response.headers['x-produto-acao'] ?? 'criado',
      } satisfies ProdutoMutationResult
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['produtos'] })
    },
  })
}

export const useUpdateProduto = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: ProdutoFormPayload }) => {
      const response = await apiClient.put<Produto>(`/api/v1/produtos/${id}`, payload)
      return response.data
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['produtos'] })
    },
  })
}

export const useDeactivateProduto = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/api/v1/produtos/${id}`)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['produtos'] })
    },
  })
}

export const useReactivateProduto = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.post(`/api/v1/produtos/${id}/reativar`)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['produtos'] })
    },
  })
}

export const useDeleteProdutoPermanente = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: number) => {
      const response = await apiClient.delete<{ message?: string }>(`/api/v1/produtos/${id}/permanente`)
      return response.data
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['produtos'] })
    },
  })
}
