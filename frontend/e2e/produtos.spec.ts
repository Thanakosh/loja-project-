import type { Page } from '@playwright/test'

import { expect, test } from './fixtures'
import { createPaginatedResponse, fulfillJson } from './helpers'

type ProdutoMock = {
  id: number
  nome: string
  fornecedor: string
  preco_unitario: number
  preco_liquido: number
  estoque_atual: number
  estoque_baixo: boolean
  estoque_minimo: number
  ativo: boolean
  categoria_id?: number | null
}

const produtoRoutePattern = /\/api\/v1\/produtos(\/.*)?(\?.*)?$/

const createProduto = (overrides?: Partial<ProdutoMock>): ProdutoMock => ({
  id: overrides?.id ?? 1,
  nome: overrides?.nome ?? 'Cabo Flex 2.5mm',
  fornecedor: overrides?.fornecedor ?? 'Fornecedor Base',
  preco_unitario: overrides?.preco_unitario ?? 12.5,
  preco_liquido: overrides?.preco_liquido ?? 12.5,
  estoque_atual: overrides?.estoque_atual ?? 30,
  estoque_baixo: overrides?.estoque_baixo ?? false,
  estoque_minimo: overrides?.estoque_minimo ?? 5,
  ativo: overrides?.ativo ?? true,
  categoria_id: overrides?.categoria_id ?? null,
})

const setupProdutosApi = async (page: Page, initialProducts: ProdutoMock[]) => {
  let products = [...initialProducts]
  let nextId = Math.max(0, ...products.map((produto) => produto.id)) + 1

  await page.route('**/api/v1/categorias/arvore', (route) =>
    fulfillJson(route, [{ id: 10, nome: 'Cabos', ativo: true, children: [] }]),
  )

  await page.route('**/api/v1/ai/check-duplicate', (route) =>
    fulfillJson(route, { tem_duplicata: false, tem_alerta: false, metodo: 'e2e', candidatos: [] }),
  )

  await page.route(produtoRoutePattern, async (route) => {
    const request = route.request()
    const method = request.method()
    const url = new URL(request.url())

    if (method === 'GET' && url.pathname.endsWith('/produtos/')) {
      const incluirInativos = url.searchParams.get('incluir_inativos') === 'true'
      const search = (url.searchParams.get('search') ?? '').toLowerCase()
      const filtered = products.filter((produto) => {
        if (!incluirInativos && !produto.ativo) return false
        if (search && !produto.nome.toLowerCase().includes(search)) return false
        return true
      })
      await fulfillJson(route, createPaginatedResponse(filtered, { page_size: 50 }))
      return
    }

    if (method === 'POST' && url.pathname.endsWith('/produtos/')) {
      const payload = request.postDataJSON() as Record<string, unknown>
      const novoProduto = createProduto({
        id: nextId++,
        nome: String(payload.nome),
        fornecedor: String(payload.fornecedor),
        preco_unitario: Number(payload.preco_unitario),
        preco_liquido: Number(payload.preco_liquido),
        estoque_minimo: Number(payload.estoque_minimo ?? 0),
        estoque_atual: Number(payload.quantidade_inicial ?? 0),
        categoria_id: payload.categoria_id ? Number(payload.categoria_id) : null,
      })
      products = [novoProduto, ...products]
      await fulfillJson(route, novoProduto, 200, { 'x-produto-acao': 'criado' })
      return
    }

    const idMatch = url.pathname.match(/\/produtos\/(\d+)(?:\/(reativar))?$/)

    if (method === 'PUT' && idMatch) {
      const produtoId = Number(idMatch[1])
      const payload = request.postDataJSON() as Record<string, unknown>
      products = products.map((produto) =>
        produto.id === produtoId
          ? {
              ...produto,
              nome: String(payload.nome),
              fornecedor: String(payload.fornecedor),
              preco_unitario: Number(payload.preco_unitario),
              preco_liquido: Number(payload.preco_liquido),
              estoque_minimo: Number(payload.estoque_minimo ?? produto.estoque_minimo),
            }
          : produto,
      )
      await fulfillJson(route, products.find((produto) => produto.id === produtoId))
      return
    }

    if (method === 'DELETE' && idMatch) {
      const produtoId = Number(idMatch[1])
      products = products.map((produto) =>
        produto.id === produtoId ? { ...produto, ativo: false } : produto,
      )
      await route.fulfill({ status: 204, body: '' })
      return
    }

    if (method === 'POST' && idMatch?.[2] === 'reativar') {
      const produtoId = Number(idMatch[1])
      products = products.map((produto) =>
        produto.id === produtoId ? { ...produto, ativo: true } : produto,
      )
      await fulfillJson(route, { ok: true })
      return
    }

    await route.abort()
  })
}

test.describe('Produtos', () => {
  test('deve criar um produto e exibi-lo na listagem', async ({ authenticatedPage: page }) => {
    await setupProdutosApi(page, [createProduto()])

    await page.goto('/#/produtos')

    await page.getByRole('button', { name: /novo produto/i }).click()
    await page.getByLabel(/nome/i).fill('Disjuntor Tripolar 50A')
    await page.getByLabel(/fornecedor/i).fill('Fornecedor E2E')
    await page.getByLabel(/pre.o unit.rio/i).fill('79.9')
    await page.getByLabel(/pre.o l.quido/i).fill('74.5')
    await page.getByLabel(/estoque m.nimo/i).fill('8')
    await page.getByRole('button', { name: /criar produto/i }).click()

    await expect(page.getByText(/produto criado com sucesso/i)).toBeVisible()
    await expect(page.locator('tr', { hasText: 'Disjuntor Tripolar 50A' })).toBeVisible()
    await expect(page.locator('tr', { hasText: 'Fornecedor E2E' })).toBeVisible()
  })

  test('deve editar um produto e refletir a alteracao na listagem', async ({ authenticatedPage: page }) => {
    await setupProdutosApi(page, [createProduto({ nome: 'Lampada LED 12W', fornecedor: 'Fornecedor Antigo' })])

    await page.goto('/#/produtos')

    const row = page.locator('tr', { hasText: 'Lampada LED 12W' })
    await row.getByRole('button', { name: 'Editar' }).click()

    await page.getByLabel(/fornecedor/i).fill('Fornecedor Atualizado')
    await page.getByLabel(/pre.o unit.rio/i).fill('18.4')
    await page.getByRole('button', { name: /salvar altera..es/i }).click()

    await expect(page.getByText(/produto atualizado com sucesso/i)).toBeVisible()
    await expect(page.locator('tr', { hasText: 'Fornecedor Atualizado' })).toBeVisible()
    await expect(page.locator('tr', { hasText: 'R$ 18,40' })).toBeVisible()
  })

  test('deve desativar e reativar um produto na mesma listagem', async ({ authenticatedPage: page }) => {
    await setupProdutosApi(page, [createProduto({ nome: 'Tomada 20A' })])

    await page.goto('/#/produtos')

    page.once('dialog', (dialog) => dialog.accept())
    await page.locator('tr', { hasText: 'Tomada 20A' }).getByRole('button', { name: 'Desativar' }).click()

    await expect(page.getByText(/produto desativado com sucesso/i)).toBeVisible()
    await page.getByRole('checkbox', { name: /mostrar inativos/i }).check()
    await expect(page.locator('tr', { hasText: 'Tomada 20A' }).getByText('Inativo')).toBeVisible()

    await page.locator('tr', { hasText: 'Tomada 20A' }).getByRole('button', { name: 'Reativar' }).click()

    await expect(page.getByText(/produto reativado com sucesso/i)).toBeVisible()
    await expect(page.locator('tr', { hasText: 'Tomada 20A' }).getByText('Ativo')).toBeVisible()
  })
})
