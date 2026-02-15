import { apiClient } from './client'
import { saveToken } from '../utils/auth'

interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

interface LoggedUser {
  id: number
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
}

export const login = async (email: string, password: string): Promise<LoggedUser> => {
  const formData = new URLSearchParams()
  formData.append('username', email)
  formData.append('password', password)

  const tokenResponse = await apiClient.post<TokenResponse>('/api/v1/users/token', formData.toString(), {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })

  saveToken(tokenResponse.data.access_token)

  const userResponse = await apiClient.get<LoggedUser>('/api/v1/users/me')
  return userResponse.data
}
