import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'

import { useAuthContext } from '../contexts/AuthContext'

const RouteAccessFallback = () => (
  <div className="flex min-h-[40vh] items-center justify-center px-6 text-sm text-gray-500 dark:text-gray-400">
    Carregando...
  </div>
)

export const AdminRoute = ({ children }: { children: ReactNode }) => {
  const { canManageUsers, isLoading } = useAuthContext()

  if (isLoading) {
    return <RouteAccessFallback />
  }

  if (!canManageUsers) {
    return <Navigate replace to="/dashboard" />
  }

  return <>{children}</>
}
