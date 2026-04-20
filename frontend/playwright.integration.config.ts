import fs from 'node:fs'
import { spawnSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { defineConfig, devices } from '@playwright/test'

const frontendUrl = process.env.PLAYWRIGHT_FRONTEND_URL ?? 'http://127.0.0.1:5173'
const backendUrl = process.env.PLAYWRIGHT_BACKEND_URL ?? 'http://127.0.0.1:8000'
const frontendDir = path.dirname(fileURLToPath(import.meta.url))
const backendDir = path.resolve(frontendDir, '../backend')
const projectVenvPython = path.resolve(frontendDir, '../.venv/Scripts/python.exe')

const canImportFastApi = (commandParts: string[]): boolean => {
  const [command, ...args] = commandParts
  const result = spawnSync(command, [...args, '-c', 'from fastapi import FastAPI'], {
    stdio: 'ignore',
    cwd: backendDir,
    env: process.env,
  })

  return result.status === 0
}

const pythonCandidates = [
  process.env.PLAYWRIGHT_PYTHON ? [process.env.PLAYWRIGHT_PYTHON] : null,
  fs.existsSync(projectVenvPython) ? [projectVenvPython] : null,
  process.platform === 'win32' ? ['py', '-3.13'] : null,
  ['python'],
].filter((candidate): candidate is string[] => candidate !== null)

const backendPythonCommand = pythonCandidates.find(canImportFastApi) ?? pythonCandidates[pythonCandidates.length - 1]
const quotedBackendPython = backendPythonCommand
  .map((part) => (part.includes(' ') ? `"${part}"` : part))
  .join(' ')

export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.integration.spec.ts',
  timeout: 60_000,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: [['html', { outputFolder: 'playwright-report-integration' }], ['list']],
  use: {
    baseURL: frontendUrl,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'on-first-retry',
  },
  webServer: [
    {
      command: `${quotedBackendPython} create_user.py && ${quotedBackendPython} -m uvicorn app.main:app --host 127.0.0.1 --port 8000`,
      cwd: backendDir,
      url: `${backendUrl}/ping`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        DEBUG: 'false',
        ENVIRONMENT: 'development',
        CORS_ORIGINS: '["http://127.0.0.1:5173","http://localhost:5173"]',
      },
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 5173',
      cwd: frontendDir,
      url: frontendUrl,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        VITE_API_URL: backendUrl,
      },
    },
  ],
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
      },
    },
  ],
})
