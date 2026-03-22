import type { Page, Route } from '@playwright/test'

export const fulfillJson = (
  route: Route,
  payload: unknown,
  status = 200,
  headers?: Record<string, string>,
) =>
  route.fulfill({
    status,
    contentType: 'application/json',
    headers,
    body: JSON.stringify(payload),
  })

export const createPaginatedResponse = <T>(
  items: T[],
  overrides?: Partial<{
    total: number
    page: number
    page_size: number
    pages: number
  }>,
) => ({
  items,
  total: overrides?.total ?? items.length,
  page: overrides?.page ?? 1,
  page_size: overrides?.page_size ?? (items.length || 1),
  pages: overrides?.pages ?? 1,
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
      await fulfillJson(route, { detail: 'Email ou senha invalidos.' }, 401)
      return
    }

    await fulfillJson(route, {
      access_token: 'token-e2e',
      refresh_token: 'refresh-e2e',
      token_type: 'bearer',
      expires_in: 3600,
    })
  })

  await page.route('**/api/v1/users/me', (route) =>
    fulfillJson(route, {
      id: 1,
      email: 'admin@empresa.com',
      full_name: 'Administrador E2E',
      is_active: true,
      is_superuser: true,
    }),
  )
}

export const mockDashboardApi = async (page: Page) => {
  await page.route('**/api/v1/vendas/**', (route) =>
    fulfillJson(route, { items: [{ total: 125.5 }], total: 1, page: 1, pages: 1 }),
  )
  await page.route('**/api/v1/orcamentos/**', (route) =>
    fulfillJson(route, { total: 3, items: [] }),
  )
  await page.route('**/api/v1/produtos/**', (route) =>
    fulfillJson(route, { total: 12, items: [] }),
  )
  await page.route('**/api/v2/estoque/alertas', (route) =>
    fulfillJson(route, [
      { id: 1, nome_produto: 'Cabo Flex 2.5mm', estoque_atual: 1, estoque_minimo: 5 },
    ]),
  )
}
