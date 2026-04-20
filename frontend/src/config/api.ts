const trimTrailingSlash = (value: string) => value.replace(/\/+$/, '')

const resolveDesktopApiBaseUrl = () => {
  if (typeof window === 'undefined') {
    return ''
  }

  const desktopApiBaseUrl = window.desktop?.runtime.apiBaseUrl?.trim()
  return desktopApiBaseUrl ? trimTrailingSlash(desktopApiBaseUrl) : ''
}

const resolveDefaultApiBaseUrl = () => {
  if (typeof window === 'undefined') {
    return ''
  }

  const desktopApiBaseUrl = resolveDesktopApiBaseUrl()
  if (desktopApiBaseUrl) {
    return desktopApiBaseUrl
  }

  return trimTrailingSlash(window.location.origin)
}

export const API_BASE_URL = trimTrailingSlash(
  import.meta.env.VITE_API_URL?.trim() || resolveDefaultApiBaseUrl(),
)
