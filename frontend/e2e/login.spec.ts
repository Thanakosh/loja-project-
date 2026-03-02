import { expect, test } from '@playwright/test'

import { mockDashboardApi, mockLoginApi } from './helpers'

test.describe('Login', () => {
  test('deve exibir erro para credenciais inválidas', async ({ page }) => {
    await mockLoginApi(page)

    await page.goto('/#/login')

    await page.getByLabel('Email').fill('invalido@empresa.com')
    await page.getByLabel('Senha').fill('senha-errada')
    await page.getByRole('button', { name: 'Entrar' }).click()

    await expect(page.getByText(/Email ou senha inv(a|á)lid[oa]s?\./i)).toBeVisible()
  })

  test('deve redirecionar para dashboard com credenciais válidas', async ({ page }) => {
    await mockLoginApi(page)
    await mockDashboardApi(page)

    await page.goto('/#/login')

    await page.getByLabel('Email').fill('admin@empresa.com')
    await page.getByLabel('Senha').fill('senha-valida')
    await page.getByRole('button', { name: 'Entrar' }).click()

    await expect(page).toHaveURL(/#\/dashboard$/)
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
  })
})
