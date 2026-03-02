import axios, { AxiosError } from 'axios'

import { getToken, getRefreshToken, saveToken, saveRefreshToken, removeToken } from '../utils/auth'

export const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
})

apiClient.interceptors.request.use((config) => {
  const token = getToken()

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

let isRefreshing = false
let failedQueue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = []

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token!)
    }
  })
  failedQueue = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as typeof error.config & { _retry?: boolean }
    const requestUrl = originalRequest?.url ?? ''
    const isAuthEndpoint = requestUrl.includes('/api/v1/users/token') || requestUrl.includes('/api/v1/users/refresh')

    if (isAuthEndpoint) {
      return Promise.reject(error)
    }

    if (error.response?.status === 401 && !originalRequest?._retry) {
      const refreshToken = getRefreshToken()

      // Sem refresh token → redireciona para login
      if (!refreshToken) {
        removeToken()
        if (window.location.pathname !== '/login') window.location.href = '/login'
        return Promise.reject(error)
      }

      if (isRefreshing) {
        // Enfileira requisições enquanto o refresh está em andamento
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token: string) => {
              originalRequest!.headers!.Authorization = `Bearer ${token}`
              resolve(apiClient(originalRequest!))
            },
            reject,
          })
        })
      }

      originalRequest!._retry = true
      isRefreshing = true

      try {
        const res = await axios.post('http://localhost:8000/api/v1/users/refresh', {
          refresh_token: refreshToken,
        })

        const newAccessToken: string = res.data.access_token
        const newRefreshToken: string = res.data.refresh_token

        saveToken(newAccessToken)
        saveRefreshToken(newRefreshToken)

        apiClient.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`
        originalRequest!.headers!.Authorization = `Bearer ${newAccessToken}`

        processQueue(null, newAccessToken)
        return apiClient(originalRequest!)
      } catch (refreshError) {
        processQueue(refreshError, null)
        removeToken()
        if (window.location.pathname !== '/login') window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)
