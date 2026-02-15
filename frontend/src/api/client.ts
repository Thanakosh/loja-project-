import axios, { AxiosError } from 'axios'

import { getToken } from '../utils/auth'

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

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && window.location.pathname !== '/login') {
      window.location.href = '/login'
    }

    return Promise.reject(error)
  },
)
