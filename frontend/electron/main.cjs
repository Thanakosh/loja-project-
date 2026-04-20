const { app, BrowserWindow, dialog, ipcMain } = require('electron')
const fs = require('node:fs')
const http = require('node:http')
const path = require('node:path')
const { spawn } = require('node:child_process')

const isDev = !app.isPackaged
const shouldUseBundledBackend = app.isPackaged || process.env.LOJA_DESKTOP_USE_BUNDLED_BACKEND === '1'
const defaultApiPort = Number(process.env.LOJA_DESKTOP_API_PORT || 8000)
const defaultApiBaseUrl = trimTrailingSlash(
  process.env.LOJA_DESKTOP_API_URL || `http://127.0.0.1:${defaultApiPort}`,
)

let backendProcess = null

function trimTrailingSlash(value) {
  return String(value || '').replace(/\/+$/, '')
}

function toSqliteUrl(filePath) {
  return `sqlite:///${path.resolve(filePath).replace(/\\/g, '/')}`
}

function getDesktopDataDir() {
  return path.join(app.getPath('userData'), 'data')
}

function getFirstRunFilePath() {
  return path.join(getDesktopDataDir(), 'desktop-first-run.json')
}

function readInitialAdmin() {
  const firstRunFilePath = getFirstRunFilePath()

  if (!fs.existsSync(firstRunFilePath)) {
    return null
  }

  try {
    return JSON.parse(fs.readFileSync(firstRunFilePath, 'utf8'))
  } catch (error) {
    console.warn('Nao foi possivel ler desktop-first-run.json:', error)
    return null
  }
}

function getBundledBackendDir() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'LojaAPI')
  }

  return path.resolve(__dirname, '..', '.desktop-build', 'backend', 'dist', 'LojaAPI')
}

function getBundledBackendExecutablePath() {
  const executableName = process.platform === 'win32' ? 'LojaAPI.exe' : 'LojaAPI'
  return path.join(getBundledBackendDir(), executableName)
}

function getRuntimeInfo() {
  return {
    isElectron: true,
    mode: shouldUseBundledBackend ? 'desktop-local' : 'browser',
    apiBaseUrl: defaultApiBaseUrl,
    dataDir: shouldUseBundledBackend ? getDesktopDataDir() : '',
    usingBundledBackend: shouldUseBundledBackend,
    initialAdmin: readInitialAdmin(),
  }
}

function waitForBackendReady(baseUrl, timeoutMs = 20000) {
  return new Promise((resolve, reject) => {
    const startedAt = Date.now()

    const tryPing = () => {
      const request = http.get(`${baseUrl}/ping`, (response) => {
        response.resume()

        if (response.statusCode && response.statusCode < 500) {
          resolve()
          return
        }

        retry()
      })

      request.on('error', retry)
      request.setTimeout(1500, () => {
        request.destroy()
        retry()
      })
    }

    const retry = () => {
      if (Date.now() - startedAt >= timeoutMs) {
        reject(new Error(`Backend desktop nao respondeu em ${timeoutMs}ms`))
        return
      }

      setTimeout(tryPing, 500)
    }

    tryPing()
  })
}

async function startBundledBackend() {
  if (!shouldUseBundledBackend) {
    return
  }

  if (backendProcess) {
    return
  }

  const backendDir = getBundledBackendDir()
  const backendExecutablePath = getBundledBackendExecutablePath()
  const dataDir = getDesktopDataDir()
  const databasePath = path.join(dataDir, 'loja.db')

  if (!fs.existsSync(backendExecutablePath)) {
    throw new Error(`Executavel do backend desktop nao encontrado: ${backendExecutablePath}`)
  }

  fs.mkdirSync(dataDir, { recursive: true })

  backendProcess = spawn(backendExecutablePath, [], {
    cwd: backendDir,
    windowsHide: true,
    stdio: 'ignore',
    env: {
      ...process.env,
      LOJA_DESKTOP_MODE: '1',
      LOJA_RUNTIME_BASE_DIR: app.getPath('userData'),
      LOJA_RESOURCE_BASE_DIR: backendDir,
      LOJA_APP_DATA_DIR: dataDir,
      DATABASE_URL: process.env.DATABASE_URL || toSqliteUrl(databasePath),
      JWT_SECRET: process.env.JWT_SECRET || 'desktop-local-secret-token-2026',
      ENVIRONMENT: process.env.ENVIRONMENT || 'development',
      DEBUG: 'false',
      CORS_ORIGINS: process.env.CORS_ORIGINS || '["*"]',
    },
  })

  backendProcess.once('exit', () => {
    backendProcess = null
  })

  await waitForBackendReady(defaultApiBaseUrl)
}

function stopBundledBackend() {
  if (!backendProcess) {
    return
  }

  try {
    backendProcess.kill()
  } catch (error) {
    console.warn('Nao foi possivel encerrar o backend desktop:', error)
  } finally {
    backendProcess = null
  }
}

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 720,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
  })

  if (isDev) {
    const configuredDevServerUrl = process.env.ELECTRON_START_URL
    const isLocalDevServer =
      configuredDevServerUrl && /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?(\/|$)/i.test(configuredDevServerUrl)
    if (configuredDevServerUrl && !isLocalDevServer) {
      console.warn('Ignoring ELECTRON_START_URL because it is not a localhost URL.')
    }
    const devServerUrl = isLocalDevServer ? configuredDevServerUrl : 'http://localhost:5173'
    mainWindow.loadURL(devServerUrl)
    mainWindow.webContents.openDevTools({ mode: 'detach' })
  } else {
    mainWindow.loadFile(path.join(app.getAppPath(), 'dist', 'index.html'))
  }
}

ipcMain.on('desktop:get-runtime-info-sync', (event) => {
  event.returnValue = getRuntimeInfo()
})

ipcMain.handle('desktop:get-runtime-info', async () => getRuntimeInfo())

ipcMain.handle('desktop:acknowledge-initial-admin', async () => {
  const firstRunFilePath = getFirstRunFilePath()

  if (fs.existsSync(firstRunFilePath)) {
    fs.rmSync(firstRunFilePath, { force: true })
  }

  return getRuntimeInfo()
})

app.whenReady().then(async () => {
  try {
    await startBundledBackend()
  } catch (error) {
    dialog.showErrorBox(
      'Falha ao iniciar backend desktop',
      error instanceof Error ? error.message : 'Erro desconhecido ao iniciar backend local.',
    )
    app.quit()
    return
  }

  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('before-quit', () => {
  stopBundledBackend()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
