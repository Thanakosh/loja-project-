import { TOKEN_KEY } from '../types/auth'

export const saveToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token)
}

export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY)
}

export const getToken = (): string | null => localStorage.getItem(TOKEN_KEY)

export const isAuthenticated = (): boolean => Boolean(getToken())
