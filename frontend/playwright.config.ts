import { defineConfig, devices } from '@playwright/test';
import path from 'path';

export default defineConfig({
  testDir: './tests',
  timeout: 30000,
  retries: 1,
  reporter: [['html', { outputFolder: 'playwright-report' }], ['list']],

  use: {
    // Captura screenshot e vídeo em caso de falha
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'on-first-retry',
  },

  projects: [
    // Testes rodando no Electron (app empacotado)
    {
      name: 'electron',
      use: {
        ...devices['Desktop Chrome'],
      },
    },
    // Testes rodando no browser (dev server Vite) — mais rápido para desenvolvimento
    {
      name: 'browser',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: 'http://localhost:5173',
      },
    },
  ],
});
