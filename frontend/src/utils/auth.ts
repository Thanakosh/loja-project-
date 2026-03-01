import { TOKEN_KEY } from '../types/auth'

const REFRESH_TOKEN_KEY = 'refresh_token'

export const saveToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token)
}

export const saveRefreshToken = (token: string): void => {
  localStorage.setItem(REFRESH_TOKEN_KEY, token)
}

export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export const getToken = (): string | null => localStorage.getItem(TOKEN_KEY)

export const getRefreshToken = (): string | null => localStorage.getItem(REFRESH_TOKEN_KEY)

export const isAuthenticated = (): boolean => Boolean(getToken())
