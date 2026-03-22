import type { Page } from '@playwright/test'

import { expect, test } from './fixtures'
import { createPaginatedResponse, fulfillJson } from './helpers'

type OrcamentoStatus = 'aberto' | 'aprovado' | 'cancelado' | 'convertido'

interface OrcamentoItemMock {
  id: number
  descricao: string
  quantidade: number
  preco_unitario: number
  desconto: number
  preco_total: number
}

interface OrcamentoMock {
  id: number
  cliente_id?: number | null
  cliente_nome?: string | null
  status: OrcamentoStatus
  desconto_geral: number
  observacao?: string | null
  data_criacao: string
  data_validade?: string | null
  venda_id?: number | null
  itens: OrcamentoItemMock[]
  total: number
}

const orcamentoRoutePattern = /\/api\/v1\/orcamentos(\/.*)?(\?.*)?$/

const createOrcamento = (overrides?: Partial<OrcamentoMock>): OrcamentoMock => ({
  id: overrides?.id ?? 101,
  cliente_id: overrides?.cliente_id ?? 1,
  cliente_nome: overrides?.cliente_nome ?? 'Cliente Base',
  status: overrides?.status ?? 'aberto',
  desconto_geral: overrides?.desconto_geral ?? 0,
  observacao: overrides?.observacao ?? null,
  data_criacao: overrides?.data_criacao ?? '2026-03-21T12:00:00Z',
  data_validade: overrides?.data_validade ?? '2026-03-31',
  venda_id: overrides?.venda_id ?? null,
  itens:
    overrides?.itens ??
    [
      {
        id: 1,
        descricao: 'Cabo Flex 2.5mm',
        quantidade: 2,
        preco_unitario: 15,
        desconto: 0,
        preco_total: 30,
      },
    ],
  total: overrides?.total ?? 30,
})

const setupOrcamentosApi = async (page: Page, initialBudgets: OrcamentoMock[]) => {
  let budgets = [...initialBudgets]
  let nextId = Math.max(0, ...budgets.map((orcamento) => orcamento.id)) + 1

  await page.route('**/api/v1/clientes/?*', (route) =>
    fulfillJson(route, [
      { id: 10, nome: 'Maria Oliveira', cpf_cnpj: '12345678900' },
      { id: 11, nome: 'Cliente Base', cpf_cnpj: '00998877665' },
    ]),
  )

  await page.route('**/api/v1/produtos/?*', (route) =>
    fulfillJson(route, {
      items: [
        {
          id: 501,
          nome: 'Disjuntor 40A',
          preco_unitario: 32.5,
          preco_liquido: 32.5,
          unidade_medida: 'UN',
        },
      ],
      total: 1,
    }),
  )

  await page.route(orcamentoRoutePattern, async (route) => {
    const request = route.request()
    const method = request.method()
    const url = new URL(request.url())

    if (method === 'GET' && url.pathname.endsWith('/orcamentos/')) {
      const statusFilter = url.searchParams.get('status')
      const filtered = statusFilter
        ? budgets.filter((orcamento) => orcamento.status === statusFilter)
        : budgets
      await fulfillJson(route, createPaginatedResponse(filtered, { page_size: 20 }))
      return
    }

    if (method === 'POST' && url.pathname.endsWith('/orcamentos/')) {
      const payload = request.postDataJSON() as {
        cliente_id: number | null
        cliente_nome: string
        desconto_geral: number
        observacao?: string | null
        data_validade?: string | null
        itens: Array<{
          produto_id?: number | null
          descricao: string
          quantidade: number
          preco_unitario: number
          desconto: number
        }>
      }
      const created = createOrcamento({
        id: nextId++,
        cliente_id: payload.cliente_id,
        cliente_nome: payload.cliente_nome,
        desconto_geral: payload.desconto_geral,
        observacao: payload.observacao ?? null,
        data_validade: payload.data_validade ?? null,
        itens: payload.itens.map((item, index) => ({
          id: index + 1,
          descricao: item.descricao,
          quantidade: item.quantidade,
          preco_unitario: item.preco_unitario,
          desconto: item.desconto,
          preco_total: item.quantidade * item.preco_unitario * (1 - item.desconto / 100),
        })),
        total:
          payload.itens.reduce(
            (sum, item) => sum + item.quantidade * item.preco_unitario * (1 - item.desconto / 100),
            0,
          ) - payload.desconto_geral,
      })
      budgets = [created, ...budgets]
      await fulfillJson(route, created)
      return
    }

    const cancelMatch = url.pathname.match(/\/orcamentos\/(\d+)$/)
    const convertMatch = url.pathname.match(/\/orcamentos\/(\d+)\/converter$/)

    if (method === 'DELETE' && cancelMatch) {
      const budgetId = Number(cancelMatch[1])
      budgets = budgets.map((orcamento) =>
        orcamento.id === budgetId ? { ...orcamento, status: 'cancelado' } : orcamento,
      )
      await route.fulfill({ status: 204, body: '' })
      return
    }

    if (method === 'POST' && convertMatch) {
      const budgetId = Number(convertMatch[1])
      budgets = budgets.map((orcamento) =>
        orcamento.id === budgetId ? { ...orcamento, status: 'convertido', venda_id: 9001 } : orcamento,
      )
      await fulfillJson(route, { venda_id: 9001 })
      return
    }

    if (method === 'GET' && /\/orcamentos\/\d+\/pdf$/.test(url.pathname)) {
      await route.fulfill({
        status: 200,
        contentType: 'application/pdf',
        body: 'fake-pdf',
      })
      return
    }

    await route.abort()
  })
}

test.describe('Orcamentos', () => {
  test('deve criar um orcamento com item e exibi-lo na listagem', async ({ authenticatedPage: page }) => {
    await setupOrcamentosApi(page, [])

    await page.goto('/#/orcamentos')

    await page.getByRole('button', { name: /novo or.amento/i }).click()
    await page.getByPlaceholder(/buscar cliente/i).fill('Maria')
    await page.getByText('Maria Oliveira').click()
    await page.getByPlaceholder(/buscar produto/i).fill('Disjuntor')
    await page.getByText('Disjuntor 40A').click()
    await page.getByPlaceholder('Qtd').fill('3')
    await page.getByPlaceholder(/pre.o unit.rio/i).fill('35')
    await page.getByRole('button', { name: /salvar or.amento/i }).click()

    await expect(page.getByText(/or.amento criado com sucesso/i)).toBeVisible()
    await expect(page.locator('tr', { hasText: 'Maria Oliveira' })).toBeVisible()
    await expect(page.locator('tr', { hasText: 'R$ 105,00' })).toBeVisible()
  })

  test('deve converter um orcamento aberto em venda', async ({ authenticatedPage: page }) => {
    await setupOrcamentosApi(page, [createOrcamento({ id: 201, cliente_nome: 'Cliente Conversao' })])

    await page.goto('/#/orcamentos')

    const row = page.locator('tr', { hasText: 'Cliente Conversao' })
    await row.getByRole('button', { name: 'Converter' }).click()
    await page.getByRole('button', { name: 'Confirmar' }).click()

    await expect(page.getByText(/or.amento convertido em venda com sucesso/i)).toBeVisible()

    await page.getByRole('combobox').first().selectOption('convertido')
    await expect(page.locator('tr', { hasText: 'Cliente Conversao' })).toContainText(/convertido/i)
  })

  test('deve cancelar um orcamento aberto e manter o estado final na listagem', async ({ authenticatedPage: page }) => {
    await setupOrcamentosApi(page, [createOrcamento({ id: 301, cliente_nome: 'Cliente Cancelamento' })])

    await page.goto('/#/orcamentos')

    await page.locator('tr', { hasText: 'Cliente Cancelamento' }).getByRole('button', { name: 'Cancelar' }).click()

    await expect(page.getByText(/or.amento cancelado com sucesso/i)).toBeVisible()

    await page.getByRole('combobox').first().selectOption('cancelado')
    await expect(page.locator('tr', { hasText: 'Cliente Cancelamento' })).toContainText(/cancelado/i)
  })
})
