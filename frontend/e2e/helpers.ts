import type { Page, Route } from '@playwright/test'

const json = (route: Route, payload: unknown, status = 200) =>
  route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(payload),
  })

export const mockAuthenticatedSession = async (page: Page) => {
  await page.addInitScript(() => {
    localStorage.setItem('token', 'token-e2e')
    localStorage.setItem('refresh_token', 'refresh-e2e')
  })
}

export const mockLoginApi = async (page: Page) => {
  await page.route('**/api/v1/users/token', async (route) => {
    const body = route.request().postData() ?? ''
    const invalidCredentials = body.includes('username=invalido%40empresa.com')

    if (invalidCredentials) {
      await json(route, { detail: 'Email ou senha inválidos.' }, 401)
      return
    }

    await json(route, {
      access_token: 'token-e2e',
      refresh_token: 'refresh-e2e',
      token_type: 'bearer',
      expires_in: 3600,
    })
  })

  await page.route('**/api/v1/users/me', (route) =>
    json(route, {
      id: 1,
      email: 'admin@empresa.com',
      full_name: 'Administrador E2E',
      is_active: true,
      is_superuser: true,
    }),
  )
}

export const mockDashboardApi = async (page: Page) => {
  await page.route('**/api/v1/vendas/**', (route) => json(route, { items: [{ total: 125.5 }], total: 1, page: 1, pages: 1 }))
  await page.route('**/api/v1/orcamentos/**', (route) => json(route, { total: 3, items: [] }))
  await page.route('**/api/v1/produtos/**', (route) => json(route, { total: 12, items: [] }))
  await page.route('**/api/v1/fiscal-ai/risk-dashboard', (route) =>
    json(route, {
      total_notas: 2,
      score_medio: 17.5,
      notas_risco_alto: 1,
      periodo_rotulo: 'ultimas notas importadas',
      top_fornecedores_alertas: [{ nome: 'Fornecedor Teste', alertas: 2 }],
      entradas: {
        total_notas: 1,
        score_medio: 35,
        notas_risco_alto: 1,
        periodo_rotulo: 'ultimas notas importadas',
        top_fornecedores_alertas: [{ nome: 'Fornecedor Entrada', alertas: 1 }],
      },
      saidas: {
        total_notas: 1,
        score_medio: 0,
        notas_risco_alto: 0,
        periodo_rotulo: 'ultimas notas importadas',
        top_fornecedores_alertas: [{ nome: 'Fornecedor Saida', alertas: 0 }],
      },
    }),
  )
  await page.route('**/api/v2/estoque/alertas', (route) =>
    json(route, [{ id: 1, nome_produto: 'Cabo Flex 2.5mm', estoque_atual: 1, estoque_minimo: 5 }]),
  )
}
