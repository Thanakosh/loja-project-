type DesktopInitialAdmin = {
  email: string
  password: string
  full_name: string
  generated_at: string
}

type DesktopRuntimeInfo = {
  isElectron: boolean
  mode: 'browser' | 'desktop-local'
  apiBaseUrl: string
  dataDir: string
  usingBundledBackend: boolean
  initialAdmin: DesktopInitialAdmin | null
}

type DesktopBridge = {
  isElectron: boolean
  runtime: DesktopRuntimeInfo
  getRuntimeInfo: () => Promise<DesktopRuntimeInfo>
  acknowledgeInitialAdmin: () => Promise<DesktopRuntimeInfo>
}

interface Window {
  desktop?: DesktopBridge
}
