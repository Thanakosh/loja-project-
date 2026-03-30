import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { defineConfig, devices } from '@playwright/test'

const frontendUrl = process.env.PLAYWRIGHT_FRONTEND_URL ?? 'http://127.0.0.1:5173'
const backendUrl = process.env.PLAYWRIGHT_BACKEND_URL ?? 'http://127.0.0.1:8000'
const frontendDir = path.dirname(fileURLToPath(import.meta.url))
const backendDir = path.resolve(frontendDir, '../backend')

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
      command: 'python -m uvicorn app.main:app --host 127.0.0.1 --port 8000',
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
