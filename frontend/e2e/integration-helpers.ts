import { expect, type APIRequestContext, type Page } from '@playwright/test'

const BACKEND_BASE_URL = process.env.PLAYWRIGHT_BACKEND_URL ?? process.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

export interface SeededUser {
  email: string
  password: string
  token: string
}

interface SeededProduct {
  id: number
  nome: string
}

export interface BackendProduct {
  id: number
  nome: string
  fornecedor: string
  preco_unitario: number
  preco_liquido: number
  estoque_atual: number
  ativo: boolean
}

const buildUrl = (path: string) => `${BACKEND_BASE_URL}${path}`

export const createSeededUser = async (request: APIRequestContext, suffix: string): Promise<SeededUser> => {
  const email = `e2e-integrado-${suffix}@teste.com.br`
  const password = 'SenhaForte123!'

  const registerResponse = await request.post(buildUrl('/api/v1/users/register'), {
    data: {
      email,
      password,
      full_name: `E2E Integrado ${suffix}`,
    },
  })
  expect(registerResponse.ok()).toBeTruthy()

  const tokenResponse = await request.post(buildUrl('/api/v1/users/token'), {
    form: {
      username: email,
      password,
    },
  })
  expect(tokenResponse.ok()).toBeTruthy()

  const tokenData = await tokenResponse.json()
  return {
    email,
    password,
    token: tokenData.access_token as string,
  }
}

export const loginThroughUi = async (
  page: Page,
  user: Pick<SeededUser, 'email' | 'password'>,
): Promise<void> => {
  await page.goto('/#/login')

  await page.locator('#username').fill(user.email)
  await page.locator('#password').fill(user.password)
  await page.getByRole('button', { name: 'Entrar' }).click()

  await expect(page).toHaveURL(/#\/dashboard$/)
}

export const createSeededProduct = async (
  request: APIRequestContext,
  token: string,
  suffix: string,
): Promise<SeededProduct> => {
  const nome = `Produto E2E ${suffix}`
  const productResponse = await request.post(buildUrl('/api/v1/produtos/'), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    data: {
      nome,
      descricao: 'Produto criado para fluxo E2E integrado',
      fornecedor: 'Fornecedor E2E',
      preco_unitario: 25.0,
      preco_liquido: 20.0,
      preco_custo: 10.0,
      preco_varejo: 25.0,
      unidade: 'UN',
      unidade_medida: 'UN',
      estoque_minimo: 1,
      quantidade_inicial: 5,
    },
  })
  expect(productResponse.ok()).toBeTruthy()

  const product = await productResponse.json()
  return {
    id: product.id as number,
    nome,
  }
}

export const ensureOpenCash = async (request: APIRequestContext, token: string): Promise<void> => {
  const currentCashResponse = await request.get(buildUrl('/api/v1/caixa/atual'), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (currentCashResponse.ok()) {
    return
  }

  const openCashResponse = await request.post(buildUrl('/api/v1/caixa/abrir'), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    data: {
      valor_abertura: 100,
      observacao: 'Caixa aberto pelo E2E integrado',
    },
  })
  expect(openCashResponse.ok()).toBeTruthy()
}

export const fetchProductStock = async (
  request: APIRequestContext,
  token: string,
  productId: number,
): Promise<number> => {
  const stockResponse = await request.get(buildUrl(`/api/v2/estoque/produto/${productId}`), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  expect(stockResponse.ok()).toBeTruthy()

  const stock = await stockResponse.json()
  return Number(stock.quantidade_atual)
}

export const fetchProductByName = async (
  request: APIRequestContext,
  token: string,
  productName: string,
): Promise<BackendProduct | null> => {
  const productsResponse = await request.get(buildUrl('/api/v1/produtos/'), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    params: {
      incluir_inativos: true,
      page: 1,
      page_size: 20,
      search: productName,
    },
  })
  expect(productsResponse.ok()).toBeTruthy()

  const products = await productsResponse.json() as { items?: BackendProduct[] }
  const normalizedName = productName.trim().toLowerCase()

  return (
    products.items?.find((product) => product.nome.trim().toLowerCase() === normalizedName)
    ?? null
  )
}
