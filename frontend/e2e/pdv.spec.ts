import { expect, test } from '@playwright/test'

import { mockAuthenticatedSession } from './helpers'

test('PDV permite adicionar item e finalizar venda no fluxo feliz', async ({ page }) => {
  await mockAuthenticatedSession(page)

  await page.route('**/api/v1/produtos/?*', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 10,
            nome: 'Disjuntor 20A',
            preco_unitario: 25.5,
            estoque_atual: 30,
            ativo: true,
          },
        ],
        total: 1,
        page: 1,
        pages: 1,
      }),
    }),
  )

  await page.route('**/api/v1/clientes/?*', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], total: 0 }) }),
  )

  await page.route('**/api/v1/pdv/venda', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 9001, numero_legado: 9001, total: 25.5, forma_pagamento: 1 }),
    }),
  )

  await page.goto('/#/pdv')

  await page.getByRole('button', { name: /Disjuntor 20A/ }).click()
  await expect(page.getByText('Disjuntor 20A').first()).toBeVisible()

  await page.getByRole('button', { name: 'Finalizar Venda' }).click()

  await expect(page.getByRole('heading', { name: 'Venda concluída' })).toBeVisible()
  await expect(page.getByText('Número da venda:')).toBeVisible()
})
