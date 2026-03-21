const trimTrailingSlash = (value: string) => value.replace(/\/+$/, '')

const resolveDefaultApiBaseUrl = () => {
  if (typeof window === 'undefined') {
    return ''
  }

  return trimTrailingSlash(window.location.origin)
}

export const API_BASE_URL = trimTrailingSlash(
  import.meta.env.VITE_API_URL?.trim() || resolveDefaultApiBaseUrl(),
)
