import { expect, test, type APIRequestContext, type Locator, type Page } from '@playwright/test'

import {
  createSeededProduct,
  createSeededUser,
  ensureOpenCash,
  fetchProductStock,
  loginThroughUi,
} from './integration-helpers'

const BACKEND_BASE_URL = process.env.PLAYWRIGHT_BACKEND_URL ?? process.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

interface BudgetListItem {
  id: number
  cliente_nome: string | null
  status: 'aberto' | 'aprovado' | 'cancelado' | 'convertido'
  total: number
}

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

const fetchBudgetByClientName = async (
  request: APIRequestContext,
  token: string,
  clientName: string,
): Promise<BudgetListItem | null> => {
  const response = await request.get(`${BACKEND_BASE_URL}/api/v1/orcamentos/`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    params: {
      page: 1,
      page_size: 200,
    },
  })

  expect(response.ok()).toBeTruthy()

  const body = await response.json() as { items?: BudgetListItem[] }
  return body.items?.find((budget) => budget.cliente_nome === clientName) ?? null
}

const selectRadixOption = async (page: Page, trigger: Locator, optionName: string | RegExp): Promise<void> => {
  await trigger.click()
  await page.getByRole('option', { name: optionName }).click()
}

test('Orcamentos integrados permitem criar pela UI, filtrar e gerar PDF', async ({ page, request }) => {
  const suffix = `orcamento-ui-${Date.now()}`
  const user = await createSeededUser(request, suffix)
  const product = await createSeededProduct(request, user.token, suffix)
  const clientName = `Cliente UI ${suffix}`

  await loginThroughUi(page, user)

  await page.goto('/#/orcamentos')
  await expect(page.getByRole('button', { name: /Novo or/i })).toBeVisible({ timeout: 30_000 })

  await page.getByRole('button', { name: /Novo or/i }).click()
  const dialog = page.getByRole('dialog', { name: /Novo orcamento/i })
  await expect(dialog).toBeVisible()

  await dialog.locator('#orcamento-cliente').fill(clientName)
  await dialog.locator('#orcamento-validade').fill('2026-12-31')
  await dialog.locator('#orcamento-desconto-geral').fill('2')
  await dialog.locator('#orcamento-observacao').fill('Orcamento criado pela UI integrada')

  await dialog.locator('#orcamento-item-descricao-0').fill(product.nome)
  await expect(dialog.locator('li').filter({ hasText: product.nome })).toBeVisible({ timeout: 30_000 })
  await dialog.locator('li').filter({ hasText: product.nome }).click()
  await expect(dialog.getByText('Produto vinculado')).toBeVisible()

  await dialog.locator('#orcamento-item-quantidade-0').fill('2')
  await dialog.locator('#orcamento-item-desconto-0').fill('10')
  await expect(dialog.getByText('R$ 43,00')).toBeVisible()

  await page.getByRole('button', { name: /Salvar orcamento/i }).click()

  const createdRow = page.getByRole('row').filter({
    has: page.getByRole('cell', { name: clientName, exact: true }),
  }).first()
  await expect(createdRow).toBeVisible({ timeout: 30_000 })
  await expect(createdRow.getByText(/Aberto/i)).toBeVisible()
  await expect(createdRow.getByText('R$ 43,00')).toBeVisible()

  await expect.poll(async () => {
    const budget = await fetchBudgetByClientName(request, user.token, clientName)
    return budget?.status ?? null
  }).toBe('aberto')

  await selectRadixOption(page, page.getByRole('combobox').first(), 'Cancelados')
  await expect(createdRow).toHaveCount(0)

  await selectRadixOption(page, page.getByRole('combobox').first(), 'Abertos')
  await expect(createdRow).toBeVisible()

  const createdBudget = await fetchBudgetByClientName(request, user.token, clientName)
  expect(createdBudget).not.toBeNull()

  const pdfResponsePromise = page.waitForResponse((response) => (
    response.request().method() === 'GET'
    && response.url().endsWith(`/api/v1/orcamentos/${createdBudget!.id}/pdf`)
  ))
  await createdRow.getByRole('button', { name: 'PDF' }).click()
  const pdfResponse = await pdfResponsePromise
  expect(pdfResponse.ok()).toBeTruthy()
  expect(pdfResponse.headers()['content-type']).toContain('application/pdf')
})

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

  await selectRadixOption(page, page.locator('#orcamento-conversao-forma-pagamento'), 'A prazo')
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
