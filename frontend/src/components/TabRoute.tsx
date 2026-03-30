import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'

import type { AppTabId } from '../config/appTabs'
import { useAuthContext } from '../contexts/AuthContext'

const RouteAccessFallback = () => (
  <div className="flex min-h-[40vh] items-center justify-center px-6 text-sm text-gray-500 dark:text-gray-400">
    Carregando...
  </div>
)

export const TabRoute = ({ tabId, children }: { tabId: AppTabId; children: ReactNode }) => {
  const { canAccessTab, isLoading } = useAuthContext()

  if (isLoading) {
    return <RouteAccessFallback />
  }

  if (!canAccessTab(tabId)) {
    return <Navigate replace to="/dashboard" />
  }

  return <>{children}</>
}
