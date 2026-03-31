import { expect, test, type APIRequestContext } from '@playwright/test'

import {
  createSeededProduct,
  createSeededUser,
  ensureOpenCash,
  fetchProductStock,
  loginThroughUi,
} from './integration-helpers'

const BACKEND_BASE_URL = process.env.PLAYWRIGHT_BACKEND_URL ?? process.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

const createBudgetThroughApi = async (
  request: APIRequestContext,
  token: string,
  options: {
    clientName: string
    productId: number
    productName: string
    quantity: number
    discount?: number
    generalDiscount?: number
  },
): Promise<void> => {
  const response = await request.post(`${BACKEND_BASE_URL}/api/v1/orcamentos/`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    data: {
      cliente_nome: options.clientName,
      desconto_geral: options.generalDiscount ?? 0,
      observacao: 'Orcamento criado pelo seed E2E integrado',
      itens: [
        {
          produto_id: options.productId,
          descricao: options.productName,
          quantidade: options.quantity,
          preco_unitario: 25,
          desconto: options.discount ?? 0,
        },
      ],
    },
  })

  expect(response.ok()).toBeTruthy()
}

test('Orcamentos integrados permitem criar e converter em venda com baixa real de estoque', async ({ page, request }) => {
  const suffix = `orcamento-conversao-${Date.now()}`
  const user = await createSeededUser(request, suffix)
  const product = await createSeededProduct(request, user.token, suffix)
  const clientName = `Cliente Orcamento ${suffix}`

  await ensureOpenCash(request, user.token)
  await createBudgetThroughApi(request, user.token, {
    clientName,
    productId: product.id,
    productName: product.nome,
    quantity: 2,
    discount: 5,
    generalDiscount: 3,
  })
  await loginThroughUi(page, user)

  await page.goto('/#/orcamentos')
  await expect(page.getByRole('button', { name: /Novo or/i })).toBeVisible({ timeout: 30_000 })

  const budgetRow = page.getByRole('row').filter({
    has: page.getByRole('cell', { name: clientName, exact: true }),
  }).first()
  await expect(budgetRow).toBeVisible()
  await expect(budgetRow.getByText(/Aberto/i)).toBeVisible()

  await budgetRow.getByRole('button', { name: 'Converter' }).click()
  await expect(page.locator('#orcamento-conversao-forma-pagamento')).toBeVisible()

  await page.locator('#orcamento-conversao-forma-pagamento').selectOption('6')
  await page.locator('#orcamento-conversao-parcelas').fill('3')
  await page.getByRole('button', { name: 'Confirmar' }).click()

  await expect.poll(async () => await fetchProductStock(request, user.token, product.id)).toBe(3)
  await expect(budgetRow.getByText(/Convertido/i)).toBeVisible()
})

test('Orcamentos integrados permitem cancelar sem gerar venda nem estornar estoque', async ({ page, request }) => {
  const suffix = `orcamento-cancelamento-${Date.now()}`
  const user = await createSeededUser(request, suffix)
  const product = await createSeededProduct(request, user.token, suffix)
  const clientName = `Cliente Cancelado ${suffix}`

  await createBudgetThroughApi(request, user.token, {
    clientName,
    productId: product.id,
    productName: product.nome,
    quantity: 1,
  })
  await loginThroughUi(page, user)

  await page.goto('/#/orcamentos')
  await expect(page.getByRole('button', { name: /Novo or/i })).toBeVisible({ timeout: 30_000 })

  const budgetRow = page.getByRole('row').filter({
    has: page.getByRole('cell', { name: clientName, exact: true }),
  }).first()
  await expect(budgetRow).toBeVisible()

  await budgetRow.getByRole('button', { name: 'Cancelar' }).click()

  await expect(budgetRow.getByText(/Cancelado/i)).toBeVisible()
  await expect.poll(async () => await fetchProductStock(request, user.token, product.id)).toBe(5)
})
