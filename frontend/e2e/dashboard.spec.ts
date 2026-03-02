import { expect, test } from '@playwright/test'

import { mockAuthenticatedSession, mockDashboardApi } from './helpers'

test('Dashboard renderiza cards e alertas de estoque após login', async ({ page }) => {
  await mockAuthenticatedSession(page)
  await mockDashboardApi(page)

  await page.goto('/#/dashboard')

  await expect(page.getByText('🛒 Vendas Hoje')).toBeVisible()
  await expect(page.getByText('⚠️ Alertas de Estoque')).toBeVisible()
  await expect(page.getByText('Produtos com Estoque Baixo')).toBeVisible()
  await expect(page.getByText('Cabo Flex 2.5mm')).toBeVisible()
})
