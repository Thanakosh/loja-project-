const fs = require('node:fs')
const path = require('node:path')
const { spawnSync } = require('node:child_process')

const projectRoot = path.resolve(__dirname, '..', '..')
const backendRoot = path.join(projectRoot, 'backend')
const specFile = path.join(backendRoot, 'backend_server.spec')
const alembicIniSource = path.join(projectRoot, 'alembic.ini')
const migrationsSource = path.join(projectRoot, 'migrations')
const projectVenvPython = path.join(projectRoot, '.venv', 'Scripts', 'python.exe')
const externalBuildRoot = process.env.LOJA_DESKTOP_BUILD_ROOT
  ? path.resolve(process.env.LOJA_DESKTOP_BUILD_ROOT)
  : null
const distRoot = externalBuildRoot
  ? path.join(externalBuildRoot, 'backend', 'dist')
  : path.join(backendRoot, 'dist')
const buildRoot = externalBuildRoot
  ? path.join(externalBuildRoot, 'backend', 'build')
  : path.join(backendRoot, 'build')
const distDir = path.join(distRoot, 'LojaAPI')
const buildDir = path.join(buildRoot, 'LojaAPI')
const tempDir = externalBuildRoot ? path.join(externalBuildRoot, 'tmp') : null
const pyInstallerConfigDir = externalBuildRoot
  ? path.join(externalBuildRoot, 'pyinstaller-cache')
  : null
const tempDatabasePath = externalBuildRoot
  ? path.join(externalBuildRoot, 'backend', 'pyinstaller-build.db')
  : path.join(backendRoot, 'pyinstaller-build.db')

function normalizePath(targetPath) {
  return path.resolve(targetPath).toLowerCase()
}

function isInsideAllowedRoot(targetPath, allowedRoot) {
  const normalizedTarget = normalizePath(targetPath)
  const normalizedRoot = normalizePath(allowedRoot)

  return (
    normalizedTarget === normalizedRoot ||
    normalizedTarget.startsWith(`${normalizedRoot}${path.sep}`)
  )
}

function toSqliteUrl(filePath) {
  return `sqlite:///${path.resolve(filePath).replace(/\\/g, '/')}`
}

function hasPyInstaller(candidate) {
  if (!candidate) {
    return false
  }

  const result = spawnSync(candidate, ['-m', 'PyInstaller', '--version'], {
    stdio: 'ignore',
    env: process.env,
  })

  return result.status === 0
}

const pythonCandidates = [
  process.env.PYTHON_FOR_DESKTOP_BUILD,
  fs.existsSync(projectVenvPython) ? projectVenvPython : null,
  'python',
].filter(Boolean)

const pythonExecutable = pythonCandidates.find(hasPyInstaller)

if (!pythonExecutable) {
  throw new Error(
    'Nenhum interpretador Python com PyInstaller disponivel foi encontrado. Instale backend/requirements-desktop.txt antes do build.',
  )
}

function safeRemove(targetPath) {
  const allowedRoots = [backendRoot, externalBuildRoot].filter(Boolean)

  if (!allowedRoots.some((root) => isInsideAllowedRoot(targetPath, root))) {
    throw new Error(`Recusa em remover caminho fora do backend: ${targetPath}`)
  }

  if (fs.existsSync(targetPath)) {
    fs.rmSync(targetPath, { recursive: true, force: true })
  }
}

function copyPath(sourcePath, destinationPath) {
  if (!fs.existsSync(sourcePath)) {
    throw new Error(`Recurso obrigatorio nao encontrado: ${sourcePath}`)
  }

  const stats = fs.statSync(sourcePath)
  fs.mkdirSync(path.dirname(destinationPath), { recursive: true })
  safeRemove(destinationPath)

  if (stats.isDirectory()) {
    fs.cpSync(sourcePath, destinationPath, { recursive: true })
    return
  }

  fs.copyFileSync(sourcePath, destinationPath)
}

safeRemove(distDir)
safeRemove(buildDir)
fs.mkdirSync(distRoot, { recursive: true })
fs.mkdirSync(buildRoot, { recursive: true })

if (tempDir) {
  fs.mkdirSync(tempDir, { recursive: true })
}

if (pyInstallerConfigDir) {
  fs.mkdirSync(pyInstallerConfigDir, { recursive: true })
}

fs.mkdirSync(path.dirname(tempDatabasePath), { recursive: true })

const result = spawnSync(
  pythonExecutable,
  [
    '-m',
    'PyInstaller',
    '--noconfirm',
    '--clean',
    '--distpath',
    distRoot,
    '--workpath',
    buildRoot,
    specFile,
  ],
  {
    cwd: backendRoot,
    stdio: 'inherit',
    env: {
      ...process.env,
      DATABASE_URL: process.env.DATABASE_URL || toSqliteUrl(tempDatabasePath),
      JWT_SECRET: process.env.JWT_SECRET || 'pyinstaller-build-secret-token-2026',
      ENVIRONMENT: process.env.ENVIRONMENT || 'development',
      DEBUG: process.env.DEBUG || 'false',
      CORS_ORIGINS: process.env.CORS_ORIGINS || '["*"]',
      ...(tempDir
        ? {
            TMP: tempDir,
            TEMP: tempDir,
            TMPDIR: tempDir,
          }
        : {}),
      ...(pyInstallerConfigDir
        ? {
            PYINSTALLER_CONFIG_DIR: pyInstallerConfigDir,
          }
        : {}),
    },
  },
)

if (result.status !== 0) {
  throw new Error(`Falha ao empacotar backend local com PyInstaller (exit=${result.status ?? 'null'})`)
}

const executableName = process.platform === 'win32' ? 'LojaAPI.exe' : 'LojaAPI'
const executablePath = path.join(distDir, executableName)

if (!fs.existsSync(executablePath)) {
  throw new Error(`Executavel do backend nao encontrado apos build: ${executablePath}`)
}

copyPath(alembicIniSource, path.join(distDir, 'alembic.ini'))
copyPath(migrationsSource, path.join(distDir, 'migrations'))

console.log(`Backend desktop empacotado em ${executablePath}`)
