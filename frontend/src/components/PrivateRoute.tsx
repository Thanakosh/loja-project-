import { Navigate, Outlet } from 'react-router-dom'

import { useAuthContext } from '../contexts/AuthContext'
import { getToken } from '../utils/auth'

export const PrivateRoute = () => {
  const { isLoading, user } = useAuthContext()

  if (!getToken()) {
    return <Navigate replace to="/login" />
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900 px-6 text-sm text-gray-300">
        Carregando sessao...
      </div>
    )
  }

  if (!user) {
    return <Navigate replace to="/login" />
  }

  return <Outlet />
}
