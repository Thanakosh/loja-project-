import { expect, test } from '@playwright/test'

import { createSeededUser, ensureOpenCash, fetchCurrentCash, loginThroughUi } from './integration-helpers'

const BACKEND_BASE_URL =
  process.env.PLAYWRIGHT_BACKEND_URL ?? process.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

test('Caixa integrado registra sangria e suprimento e fecha com saldo esperado', async ({ page, request }) => {
  const user = await createSeededUser(request, `${Date.now()}`)
  let workingCash = await fetchCurrentCash(request, user.token)
  const saldoBase = workingCash?.saldo_esperado ?? 100
  const totalSuprimentosBase = workingCash?.total_suprimentos ?? 0
  const totalSangriasBase = workingCash?.total_sangrias ?? 0

  try {
    await loginThroughUi(page, user)
    await page.goto('/#/caixa')

    if (!workingCash) {
      await page.getByLabel('Valor de abertura').fill('100')
      await page.getByLabel('Observacao da abertura').fill('Abertura pelo teste integrado')
      await page.getByRole('button', { name: 'Abrir Caixa' }).click()
      workingCash = await fetchCurrentCash(request, user.token)
    }

    await expect(page.getByText(/Caixa aberto desde/i)).toBeVisible({ timeout: 30_000 })

    await page.getByRole('button', { name: 'Registrar Suprimento' }).click()
    await page.getByLabel('Valor da movimentacao').fill('20')
    await page.getByLabel('Motivo da movimentacao').fill('Reposicao de troco')
    await page.getByLabel('Observacao da movimentacao').fill('Entrada manual do teste')
    await page.getByRole('button', { name: 'Salvar Movimentacao' }).click()
    await expect(page.getByText('Reposicao de troco')).toBeVisible({ timeout: 30_000 })

    await page.getByRole('button', { name: 'Registrar Sangria' }).click()
    await page.getByLabel('Valor da movimentacao').fill('5')
    await page.getByLabel('Motivo da movimentacao').fill('Retirada para cofre')
    await page.getByLabel('Observacao da movimentacao').fill('Saida manual do teste')
    await page.getByRole('button', { name: 'Salvar Movimentacao' }).click()
    await expect(page.getByText('Retirada para cofre')).toBeVisible({ timeout: 30_000 })

    await page.getByRole('button', { name: 'Fechar Caixa' }).click()
    await page.getByLabel('Valor contado no fechamento').fill(String(saldoBase + 15))
    await page.getByRole('button', { name: 'Confirmar Fechamento' }).click()

    await expect(page.getByText(/Nenhum caixa aberto/i)).toBeVisible({ timeout: 30_000 })

    await expect.poll(async () => {
      const historyResponse = await request.get(`${BACKEND_BASE_URL}/api/v1/caixa/historico`, {
        headers: { Authorization: `Bearer ${user.token}` },
        params: { limit: 1 },
      })
      expect(historyResponse.ok()).toBeTruthy()
      const history = await historyResponse.json() as Array<{
        id: number
        diferenca: number
      }>
      return history.find((cash) => cash.id === workingCash?.id)?.diferenca ?? null
    }).toBe(0)

    const historyResponse = await request.get(`${BACKEND_BASE_URL}/api/v1/caixa/historico`, {
      headers: { Authorization: `Bearer ${user.token}` },
      params: { limit: 20 },
    })
    expect(historyResponse.ok()).toBeTruthy()
    const history = await historyResponse.json() as Array<{
      id: number
      saldo_esperado: number
      total_suprimentos: number
      total_sangrias: number
      diferenca: number
    }>
    const latestCash = history.find((cash) => cash.id === workingCash?.id)
    if (!latestCash) {
      throw new Error('Caixa fechado pelo teste nao encontrado no historico')
    }

    expect(latestCash.total_suprimentos).toBe(totalSuprimentosBase + 20)
    expect(latestCash.total_sangrias).toBe(totalSangriasBase + 5)
    expect(latestCash.saldo_esperado).toBe(saldoBase + 15)
    expect(latestCash.diferenca).toBe(0)
  } finally {
    await ensureOpenCash(request, user.token)
  }
})
