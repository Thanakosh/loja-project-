import { expect, test } from '@playwright/test'

import {
  createSeededProduct,
  createSeededUser,
  createStockTransaction,
  fetchProductStock,
  loginThroughUi,
} from './integration-helpers'

test('Estoque integrado registra entrada e saida pela UI e reflete saldo real no backend', async ({ page, request }) => {
  const suffix = `estoque-${Date.now()}`
  const user = await createSeededUser(request, suffix)
  const product = await createSeededProduct(request, user.token, suffix)

  await loginThroughUi(page, user)
  await page.goto('/#/estoque')

  await expect(page.getByRole('heading', { name: 'Estoque' })).toBeVisible({ timeout: 30_000 })
  await page.getByPlaceholder('Buscar por nome').fill(product.nome)
  await page.getByRole('button', { name: 'Buscar', exact: true }).click()

  const stockRow = page.getByRole('row').filter({
    has: page.getByRole('cell', { name: product.nome, exact: true }),
  })
  await expect(stockRow).toBeVisible()
  await expect.poll(async () => fetchProductStock(request, user.token, product.id)).toBe(5)

  await stockRow.getByRole('button', { name: 'Ajustar' }).click()
  await expect(page.getByRole('dialog')).toContainText('Lancar movimentacao')
  await page.locator('#movimentacao-quantidade').fill('3')
  await page.locator('#movimentacao-motivo').fill('Entrada E2E integrada')
  await page.getByRole('button', { name: 'Confirmar lancamento' }).click()

  await expect.poll(async () => fetchProductStock(request, user.token, product.id)).toBe(8)

  await stockRow.getByRole('button', { name: 'Ver kardex' }).click()
  await expect(page.getByRole('dialog')).toContainText(`Kardex: ${product.nome}`)
  await expect(page.getByRole('dialog')).toContainText('Entrada E2E integrada')

  await page.getByRole('button', { name: 'Novo lancamento' }).click()
  await page.locator('#movimentacao-tipo').click()
  await page.getByRole('option', { name: 'Saida' }).click()
  await page.locator('#movimentacao-quantidade').fill('2')
  await page.locator('#movimentacao-motivo').fill('Saida E2E integrada')
  await page.getByRole('button', { name: 'Confirmar lancamento' }).click()

  await expect.poll(async () => fetchProductStock(request, user.token, product.id)).toBe(6)
  await expect(page.getByRole('dialog')).toContainText('Saida E2E integrada')
})

test('Dashboard integrado exibe alerta de estoque baixo real e navega para estoque', async ({ page, request }) => {
  const suffix = `dashboard-${Date.now()}`
  const user = await createSeededUser(request, suffix)
  const product = await createSeededProduct(request, user.token, suffix)

  await createStockTransaction(request, user.token, {
    produto_id: product.id,
    tipo: 'saida',
    quantidade: 5,
    motivo: 'Forcar alerta de estoque baixo no dashboard',
  })
  await expect.poll(async () => fetchProductStock(request, user.token, product.id)).toBe(0)

  await loginThroughUi(page, user)
  await page.goto('/#/dashboard')

  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 30_000 })
  await expect(page.getByText('Alertas de Estoque')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Produtos com Estoque Baixo' })).toBeVisible()
  await expect(page.getByText(product.nome)).toBeVisible()

  await page.getByRole('button', { name: 'Ver Estoque' }).click()
  await expect(page).toHaveURL(/#\/estoque$/)
  await page.getByPlaceholder('Buscar por nome').fill(product.nome)
  await page.getByRole('button', { name: 'Buscar', exact: true }).click()
  await expect(
    page.getByRole('row').filter({
      has: page.getByRole('cell', { name: product.nome, exact: true }),
    }),
  ).toBeVisible()
})
