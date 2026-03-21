import { useQuery } from '@tanstack/react-query'

import { apiClient } from '../api/client'
import type { FiscalRiskDashboardResponse } from '../types/dashboard'

export const useFiscalRiskDashboard = () =>
  useQuery({
    queryKey: ['dashboard', 'fiscal-risk'],
    queryFn: async () => {
      const response = await apiClient.get<FiscalRiskDashboardResponse>('/api/v1/fiscal-ai/risk-dashboard')
      return response.data
    },
    staleTime: 60_000,
    refetchInterval: 60_000,
  })
