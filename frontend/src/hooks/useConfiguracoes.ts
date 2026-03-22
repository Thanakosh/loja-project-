import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '../api/client'
import type { ConfiguracaoLoja, ConfiguracaoLojaPayload } from '../types/configuracoes'

export const useConfiguracaoLoja = () =>
  useQuery({
    queryKey: ['configuracoes', 'loja'],
    queryFn: async () => {
      const response = await apiClient.get<ConfiguracaoLoja>('/api/v1/configuracoes/loja')
      return response.data
    },
    staleTime: 60_000,
  })

export const useAtualizarConfiguracaoLoja = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: ConfiguracaoLojaPayload) => {
      const response = await apiClient.put<ConfiguracaoLoja>('/api/v1/configuracoes/loja', payload)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['configuracoes', 'loja'], data)
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}
