import { TOKEN_KEY } from '../types/auth'

export const getToken = (): string | null => localStorage.getItem(TOKEN_KEY)

export const isAuthenticated = (): boolean => Boolean(getToken())
