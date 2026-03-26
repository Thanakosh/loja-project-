import { expect, test } from '@playwright/test'

import { createSeededProduct, createSeededUser, ensureOpenCash, fetchProductStock } from './integration-helpers'

test('Login real e PDV finalizam venda com backend+frontend integrados', async ({ page, request }) => {
  const suffix = `${Date.now()}`
  const user = await createSeededUser(request, suffix)
  const product = await createSeededProduct(request, user.token, suffix)
  await ensureOpenCash(request, user.token)

  await page.goto('/#/login')

  await page.locator('#username').fill(user.email)
  await page.locator('#password').fill(user.password)
  await page.getByRole('button', { name: 'Entrar' }).click()

  await expect(page).toHaveURL(/#\/dashboard$/)

  await page.goto('/#/pdv')
  await expect(page.getByRole('heading', { name: 'PDV' })).toBeVisible()

  await page.getByLabel('Buscar produto').fill(product.nome)

  const productsSection = page.locator('section').filter({
    has: page.getByRole('heading', { name: 'Produtos' }),
  })
  const productButton = productsSection.getByRole('button', { name: new RegExp(product.nome) })
  await expect(productButton).toBeVisible()
  await productButton.click()

  const cartRow = page.getByRole('row').filter({
    has: page.getByRole('cell', { name: product.nome, exact: true }),
  })
  await expect(cartRow).toBeVisible()

  await page.getByRole('button', { name: 'Finalizar Venda' }).click()

  await expect(page.getByRole('heading', { name: /Venda conclu/i })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Nova Venda' })).toBeVisible()

  await expect.poll(async () => fetchProductStock(request, user.token, product.id)).toBe(4)
})
