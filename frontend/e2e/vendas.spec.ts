import { expect, test } from '@playwright/test'

import { mockAuthenticatedSession } from './helpers'

const vendasPage1 = {
  items: [
    {
      id: 1,
      numero_legado: 1001,
      data: '2026-01-01T10:00:00Z',
      total: 299.9,
      desconto: 0,
      forma_pagamento: 4,
      cancelada: false,
      itens: [{ id: 1, nome_produto: 'Lampada LED', quantidade: 2, preco_unitario: 149.95, preco_total: 299.9 }],
    },
  ],
  total: 2,
  page: 1,
  page_size: 50,
  pages: 2,
}

const vendasPage2 = {
  ...vendasPage1,
  items: [
    {
      ...vendasPage1.items[0],
      id: 2,
      numero_legado: 1002,
      total: 99.9,
    },
  ],
  page: 2,
}

test('Vendas carrega listagem, pagina e abre/fecha modal de detalhes', async ({ page }) => {
  await mockAuthenticatedSession(page)

  await page.route('**/api/v1/vendas/?*', (route) => {
    const url = new URL(route.request().url())
    const requestedPage = url.searchParams.get('page')
    if (requestedPage === '2') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(vendasPage2) })
    }
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(vendasPage1) })
  })

  await page.route('**/api/v1/vendas/1', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(vendasPage1.items[0]) }),
  )

  await page.goto('/#/vendas')

  await expect(page.getByText('1001')).toBeVisible()

  await page.getByRole('button', { name: 'Próxima' }).click()
  await expect(page.getByText('1002')).toBeVisible()

  await page.getByRole('button', { name: 'Anterior' }).click()
  await expect(page.getByText('1001')).toBeVisible()

  await page.getByText('Ver Detalhes').first().click()
  await expect(page.getByRole('heading', { name: /Detalhes da Venda/ })).toBeVisible()
  await page.getByRole('button', { name: 'Fechar' }).click()
  await expect(page.getByRole('heading', { name: /Detalhes da Venda/ })).not.toBeVisible()
})
