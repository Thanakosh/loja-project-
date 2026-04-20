const fs = require('node:fs')
const path = require('node:path')
const { spawnSync } = require('node:child_process')

const projectRoot = __dirname
const desktopBuildRoot = path.join(projectRoot, '.desktop-build')
const bundledBackendDir = path.join(desktopBuildRoot, 'backend', 'dist', 'LojaAPI')
const isCI = process.env.CI === 'true'
const localRunId = process.env.BUILD_RUN_ID || `${Date.now()}`

function buildBundledBackend() {
  const scriptPath = path.join(projectRoot, 'scripts', 'build-bundled-backend.cjs')
  const result = spawnSync(process.execPath, [scriptPath], {
    cwd: projectRoot,
    stdio: 'inherit',
    env: {
      ...process.env,
      LOJA_DESKTOP_BUILD_ROOT: desktopBuildRoot,
    },
  })

  if (result.status !== 0) {
    throw new Error(`Falha ao gerar backend desktop local (exit=${result.status ?? 'null'})`)
  }

  if (!fs.existsSync(bundledBackendDir)) {
    throw new Error(`Diretorio do backend desktop nao encontrado: ${bundledBackendDir}`)
  }
}

module.exports = {
  outDir: isCI ? 'out' : path.join('out-local', `run-${localRunId}`),
  packagerConfig: {
    asar: true,
    extraResource: [bundledBackendDir],
  },
  hooks: {
    prePackage: async () => {
      buildBundledBackend()
    },
  },
  makers: [
    {
      name: '@electron-forge/maker-squirrel',
      config: {
        name: 'LojaProject',
        authors: 'Thanakosh',
        description: 'Sistema de Gerenciamento Comercial Inteligente',
      },
    },
    {
      name: '@electron-forge/maker-zip',
    },
  ],
}
