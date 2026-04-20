import path from 'node:path'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

import { expect, test, type Page } from '@playwright/test'

import {
  createSeededUser,
  fetchProductByName,
  fetchSupplierByCnpj,
  loginThroughUi,
} from './integration-helpers'

const testDir = path.dirname(fileURLToPath(import.meta.url))
const nfeFixturePath = path.resolve(testDir, '../../backend/tests/fixtures/nfe_minima.xml')

interface XmlFixtureOptions {
  productName: string
  supplierName: string
  supplierCnpj: string
  noteNumber: string
}

const buildUniqueDigits = (seed: string, totalLength: number): string => {
  const digits = seed.replace(/\D/g, '')
  return digits.padStart(totalLength, '0').slice(-totalLength)
}

const buildXmlFixture = (options: XmlFixtureOptions): string => {
  const fixture = readFileSync(nfeFixturePath, 'utf-8')

  return fixture
    .replace('Produto de Teste', options.productName)
    .replace('Fornecedor Exemplo LTDA', options.supplierName)
    .replaceAll('12345678000123', options.supplierCnpj)
    .replace('<nNF>123</nNF>', `<nNF>${options.noteNumber}</nNF>`)
}

const processXmlThroughUi = async (
  page: Page,
  options: XmlFixtureOptions & { fileName: string },
): Promise<void> => {
  await page.goto('/#/importar-nota')

  const resetImportButton = page.getByRole('button', { name: /Nova Importacao|Importar Outra Nota/i }).first()
  if (!await page.getByText('Arraste o XML da NFe aqui').isVisible().catch(() => false) && await resetImportButton.isVisible().catch(() => false)) {
    await resetImportButton.click()
  }

  await expect(page.getByText('Arraste o XML da NFe aqui')).toBeVisible({ timeout: 30_000 })

  await page.locator('input[type="file"]').setInputFiles({
    name: options.fileName,
    mimeType: 'application/xml',
    buffer: Buffer.from(buildXmlFixture(options), 'utf-8'),
  })
  await expect(page.getByText(options.fileName)).toBeVisible()
  await page.getByRole('button', { name: /Processar XML/i }).click()

  await expect(page.getByRole('heading', { name: 'Dados da Nota Fiscal' })).toBeVisible({ timeout: 30_000 })
}

const confirmImportThroughUi = async (page: Page): Promise<void> => {
  const importButton = page.getByRole('button', { name: /Importar 1 Produto/i })
  await expect(importButton).toBeEnabled({ timeout: 30_000 })
  await importButton.click()

  const confirmResolutionButton = page.getByRole('button', { name: /Confirmar resolucoes e importar/i })
  if (await confirmResolutionButton.isVisible()) {
    await confirmResolutionButton.click()
  }

  await expect(page.getByRole('heading', { name: 'Importacao Concluida!' })).toBeVisible({ timeout: 30_000 })
}

test('Importacao de nota integrada processa XML valido, cadastra fornecedor e cria produto no backend real', async ({ page, request }) => {
  const suffix = `xml-${Date.now()}`
  const productName = `Produto XML ${suffix}`
  const supplierName = `Fornecedor XML ${suffix}`
  const supplierCnpj = buildUniqueDigits(suffix, 14)
  const noteNumber = buildUniqueDigits(suffix, 6)
  const user = await createSeededUser(request, suffix)

  await loginThroughUi(page, user)
  await processXmlThroughUi(page, {
    fileName: `nota-${suffix}.xml`,
    productName,
    supplierName,
    supplierCnpj,
    noteNumber,
  })

  await expect(page.getByText('Novo fornecedor cadastrado')).toBeVisible()
  await confirmImportThroughUi(page)

  await expect.poll(async () => {
    const importedProduct = await fetchProductByName(request, user.token, productName)
    return importedProduct?.estoque_atual ?? null
  }).toBe(2)

  const importedProduct = await fetchProductByName(request, user.token, productName)
  expect(importedProduct).not.toBeNull()
  expect(importedProduct?.fornecedor).toBe(supplierName)

  const supplier = await fetchSupplierByCnpj(request, user.token, supplierCnpj)
  expect(supplier).not.toBeNull()
  expect(supplier?.razao_social).toBe(supplierName)
})

test('Importacao de nota integrada reaproveita fornecedor existente e soma estoque de produto ja cadastrado', async ({ page, request }) => {
  const suffix = `xml-reimport-${Date.now()}`
  const productName = `Produto XML ${suffix}`
  const supplierName = `Fornecedor XML ${suffix}`
  const supplierCnpj = buildUniqueDigits(suffix, 14)
  const user = await createSeededUser(request, suffix)

  await loginThroughUi(page, user)

  await processXmlThroughUi(page, {
    fileName: `nota-${suffix}-1.xml`,
    productName,
    supplierName,
    supplierCnpj,
    noteNumber: buildUniqueDigits(`${suffix}1`, 6),
  })
  await expect(page.getByText('Novo fornecedor cadastrado')).toBeVisible()
  await confirmImportThroughUi(page)

  await expect.poll(async () => {
    const importedProduct = await fetchProductByName(request, user.token, productName)
    return importedProduct?.estoque_atual ?? null
  }).toBe(2)

  await processXmlThroughUi(page, {
    fileName: `nota-${suffix}-2.xml`,
    productName,
    supplierName,
    supplierCnpj,
    noteNumber: buildUniqueDigits(`${suffix}2`, 6),
  })

  await expect(page.getByText('Fornecedor ja cadastrado')).toBeVisible()
  await expect(page.getByText(/1 ja no estoque/i)).toBeVisible()
  await expect(page.getByText('Soma estoque')).toBeVisible()
  await confirmImportThroughUi(page)

  await expect.poll(async () => {
    const importedProduct = await fetchProductByName(request, user.token, productName)
    return importedProduct?.estoque_atual ?? null
  }).toBe(4)
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

  await expect(page.getByText(/Arquivo .* XML da NFe/i)).toBeVisible()
})
