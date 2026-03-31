import path from 'node:path'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

import { expect, test } from '@playwright/test'

import { createSeededUser, fetchProductByName, loginThroughUi } from './integration-helpers'

const testDir = path.dirname(fileURLToPath(import.meta.url))
const nfeFixturePath = path.resolve(testDir, '../../backend/tests/fixtures/nfe_minima.xml')

const buildUniqueXmlFixture = (suffix: string): string => {
  const fixture = readFileSync(nfeFixturePath, 'utf-8')

  return fixture.replace('Produto de Teste', `Produto XML ${suffix}`)
}

test('Importacao de nota integrada processa XML valido e cadastra produto no backend real', async ({ page, request }) => {
  const suffix = `xml-${Date.now()}`
  const productName = `Produto XML ${suffix}`
  const user = await createSeededUser(request, suffix)

  await loginThroughUi(page, user)

  await page.goto('/#/importar-nota')
  await expect(page.getByText('Arraste o XML da NFe aqui')).toBeVisible({ timeout: 30_000 })

  await page.locator('input[type="file"]').setInputFiles({
    name: `nota-${suffix}.xml`,
    mimeType: 'application/xml',
    buffer: Buffer.from(buildUniqueXmlFixture(suffix), 'utf-8'),
  })
  await expect(page.getByText(`nota-${suffix}.xml`)).toBeVisible()
  await page.getByRole('button', { name: /Processar XML/i }).click()

  await expect(page.getByRole('heading', { name: 'Dados da Nota Fiscal' })).toBeVisible({ timeout: 30_000 })

  const importButton = page.getByRole('button', { name: /Importar 1 Produto/i })
  await expect(importButton).toBeEnabled({ timeout: 30_000 })
  await importButton.click()
  const confirmResolutionButton = page.getByRole('button', { name: /Confirmar resolucoes e importar/i })
  if (await confirmResolutionButton.isVisible()) {
    await confirmResolutionButton.click()
  }

  await expect(page.getByRole('heading', { name: 'Importação Concluída!' })).toBeVisible({ timeout: 30_000 })

  await expect.poll(async () => {
    const importedProduct = await fetchProductByName(request, user.token, productName)
    return importedProduct?.estoque_atual ?? null
  }).toBe(2)
})

test('Importacao de nota integrada rejeita arquivo invalido com mensagem de erro', async ({ page, request }) => {
  const suffix = `xml-invalido-${Date.now()}`
  const user = await createSeededUser(request, suffix)

  await loginThroughUi(page, user)

  await page.goto('/#/importar-nota')
  await expect(page.getByText('Arraste o XML da NFe aqui')).toBeVisible({ timeout: 30_000 })

  await page.locator('input[type="file"]').setInputFiles({
    name: `nota-${suffix}.txt`,
    mimeType: 'text/plain',
    buffer: Buffer.from('arquivo invalido para importacao', 'utf-8'),
  })

  await expect(page.getByText('Arquivo não suportado. Envie o XML da NFe.')).toBeVisible()
})
