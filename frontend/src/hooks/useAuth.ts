import axios from 'axios'
import { useCallback, useState } from 'react'

import { login } from '../api/auth'

export const useLogin = () => {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loginUser = useCallback(async (email: string, password: string) => {
    setIsLoading(true)
    setError(null)

    try {
      return await login(email, password)
    } catch (requestError) {
      if (axios.isAxiosError(requestError) && requestError.response?.status === 401) {
        setError('Email ou senha inválidos.')
      } else {
        setError('Não foi possível realizar o login. Tente novamente.')
      }

      throw requestError
    } finally {
      setIsLoading(false)
    }
  }, [])

  return {
    login: loginUser,
    isLoading,
    error,
  }
}
