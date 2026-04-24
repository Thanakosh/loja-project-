import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '../api/client'
import type {
  CompartilharOrcamentoWhatsAppPayload,
  WhatsAppAccount,
  WhatsAppConnectPayload,
  WhatsAppMessage,
} from '../types/whatsapp'

export const useWhatsAppStatus = () =>
  useQuery({
    queryKey: ['integracoes', 'whatsapp', 'status'],
    queryFn: async () => {
      const response = await apiClient.get<WhatsAppAccount>('/api/v1/integracoes/whatsapp/status')
      return response.data
    },
    staleTime: 15_000,
  })

export const useConnectWhatsApp = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: WhatsAppConnectPayload = {}) => {
      const response = await apiClient.post<WhatsAppAccount>('/api/v1/integracoes/whatsapp/connect', payload)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['integracoes', 'whatsapp', 'status'], data)
    },
  })
}

export const useDisconnectWhatsApp = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.post<WhatsAppAccount>('/api/v1/integracoes/whatsapp/disconnect')
      return response.data
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['integracoes', 'whatsapp', 'status'], data)
    },
  })
}

export const useCompartilharOrcamentoWhatsApp = () =>
  useMutation({
    mutationFn: async ({
      orcamentoId,
      payload,
    }: {
      orcamentoId: number
      payload: CompartilharOrcamentoWhatsAppPayload
    }) => {
      const response = await apiClient.post<WhatsAppMessage>(
        `/api/v1/orcamentos/${orcamentoId}/compartilhar-whatsapp`,
        payload,
      )
      return response.data
    },
  })
