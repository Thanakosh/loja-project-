import { apiClient } from './client'
import type { AppTabId } from '../config/appTabs'
import { saveToken, saveRefreshToken } from '../utils/auth'

interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface LoggedUser {
  id: number
  username: string | null
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  allowed_tabs: AppTabId[]
}

export const login = async (username: string, password: string): Promise<LoggedUser> => {
  const formData = new URLSearchParams()
  formData.append('username', username)
  formData.append('password', password)

  const tokenResponse = await apiClient.post<TokenResponse>('/api/v1/users/token', formData.toString(), {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })

  saveToken(tokenResponse.data.access_token)
  saveRefreshToken(tokenResponse.data.refresh_token)

  const userResponse = await apiClient.get<LoggedUser>('/api/v1/users/me')
  return userResponse.data
}
