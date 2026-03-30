import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

import { isAppTabId, type AppTabId } from '../config/appTabs'
import api from '../services/api'
import { getToken, removeToken } from '../utils/auth'

export interface AuthenticatedUser {
  id: number
  username: string | null
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  allowed_tabs: AppTabId[]
}

interface AuthContextValue {
  user: AuthenticatedUser | null
  isLoading: boolean
  canAccessTab: (tabId: AppTabId) => boolean
  canManageUsers: boolean
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  setAuthenticatedUser: (user: AuthenticatedUser | null) => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

const normalizeAuthenticatedUser = (user: Omit<AuthenticatedUser, 'allowed_tabs'> & { allowed_tabs?: string[] }): AuthenticatedUser => ({
  ...user,
  allowed_tabs: (user.allowed_tabs ?? []).filter(isAppTabId),
})

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<AuthenticatedUser | null>(null)
  const [isLoading, setIsLoading] = useState(() => Boolean(getToken()))

  const loadCurrentUser = async () => {
    const token = getToken()
    if (!token) {
      setUser(null)
      setIsLoading(false)
      return
    }

    setIsLoading(true)

    try {
      const response = await api.get<AuthenticatedUser>('/users/me')
      setUser(normalizeAuthenticatedUser(response.data))
    } catch {
      removeToken()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadCurrentUser()
  }, [])

  const setAuthenticatedUser = (nextUser: AuthenticatedUser | null) => {
    setUser(nextUser ? normalizeAuthenticatedUser(nextUser) : null)
    setIsLoading(false)
  }

  const refreshUser = async () => {
    await loadCurrentUser()
  }

  const logout = async () => {
    try {
      if (getToken()) {
        await api.post('/users/logout')
      }
    } catch {
      // O cleanup local precisa acontecer mesmo se o backend falhar.
    } finally {
      removeToken()
      setUser(null)
      setIsLoading(false)
    }
  }

  const canAccessTab = (tabId: AppTabId) => {
    if (!user) {
      return false
    }

    if (user.is_superuser) {
      return true
    }

    return user.allowed_tabs.includes(tabId)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        canAccessTab,
        canManageUsers: Boolean(user?.is_superuser),
        logout,
        refreshUser,
        setAuthenticatedUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuthContext = () => {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuthContext deve ser usado dentro de AuthProvider')
  }

  return context
}
