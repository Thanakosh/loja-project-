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
});

test.afterAll(async () => {
  await electronApp.close();
});

test('deve exibir a tela de login', async () => {
  await expect(page).toHaveURL(/login/);
  await expect(page.locator('input[type="email"], input[name="username"]')).toBeVisible();
  await expect(page.locator('input[type="password"]')).toBeVisible();
});

test('deve bloquear login com credenciais inválidas', async () => {
  await page.locator('input[type="email"], input[name="username"]').fill('invalido@teste.com');
  await page.locator('input[type="password"]').fill('senhaerrada');
  await page.locator('button[type="submit"]').click();
  await expect(page.locator('text=/erro|inválid|incorret/i')).toBeVisible({ timeout: 5000 });
});

test('deve realizar login com credenciais válidas', async () => {
  await page.locator('input[type="email"], input[name="username"]').fill(TEST_USER);
  await page.locator('input[type="password"]').fill(TEST_PASSWORD);
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(/dashboard/, { timeout: 10000 });
});
