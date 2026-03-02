import { _electron as electron, test, expect, Page, ElectronApplication } from '@playwright/test';
import dotenv from 'dotenv';
dotenv.config({ path: '.env.test' });

let electronApp: ElectronApplication;
let page: Page;

const ELECTRON_EXE = 'C:\\Users\\usuario\\AppData\\Local\\LojaProject\\app-0.0.0\\frontend.exe';
const TEST_USER = process.env.TEST_USER!;
const TEST_PASSWORD = process.env.TEST_PASSWORD!;

test.beforeAll(async () => {
  electronApp = await electron.launch({ executablePath: ELECTRON_EXE });
  page = await electronApp.firstWindow();
  await page.waitForLoadState('domcontentloaded');

  await page.locator('input[type="email"], input[name="username"]').fill(TEST_USER);
  await page.locator('input[type="password"]').fill(TEST_PASSWORD);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(/dashboard/, { timeout: 10000 });
});

test.afterAll(async () => {
  await electronApp.close();
});

test('deve exibir o dashboard', async () => {
  await expect(page).toHaveURL(/dashboard/);
});

test('deve navegar para Clientes', async () => {
  await page.locator('text=/clientes/i').click();
  await expect(page).toHaveURL(/clientes/);
});

test('deve navegar para Produtos', async () => {
  await page.locator('text=/produtos/i').click();
  await expect(page).toHaveURL(/produtos/);
});

test('deve navegar para Estoque', async () => {
  await page.locator('text=/estoque/i').click();
  await expect(page).toHaveURL(/estoque/);
});

test('deve navegar para PDV', async () => {
  await page.locator('text=/pdv/i').click();
  await expect(page).toHaveURL(/pdv/);
});

test('deve navegar para Vendas', async () => {
  await page.locator('text=/vendas/i').click();
  await expect(page).toHaveURL(/vendas/);
});
