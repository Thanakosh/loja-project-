import { expect, test } from '@playwright/test'

import { createSeededUser, fetchProductByName, loginThroughUi } from './integration-helpers'

test('Produtos integrados permitem criar, editar e desativar um cadastro real', async ({ page, request }) => {
  const suffix = `produtos-${Date.now()}`
  const user = await createSeededUser(request, suffix)
  const productName = `Produto UI ${suffix}`
  const editedProductName = `${productName} Editado`

  await loginThroughUi(page, user)

  await page.goto('/#/produtos')
  await expect(page.getByRole('button', { name: /\+ Novo Produto/i })).toBeVisible({ timeout: 30_000 })

  await page.getByRole('button', { name: /\+ Novo Produto/i }).click()
  await page.locator('#produto-nome').fill(productName)
  await page.locator('#produto-fornecedor').fill(`Fornecedor ${suffix}`)
  await page.locator('#produto-preco-unitario').fill('29.90')
  await page.locator('#produto-preco-liquido').fill('24.50')
  await page.locator('#produto-estoque-minimo').fill('2')
  await page.locator('#produto-estoque-inicial').fill('7')
  await page.locator('#produto-unidade').fill('UN')
  await page.locator('#produto-descricao').fill('Produto criado pelo fluxo E2E integrado')
  await page.getByRole('button', { name: /Criar produto/i }).click()

  const createdRow = page.getByRole('row').filter({
    has: page.getByRole('cell', { name: productName, exact: true }),
  })
  await expect(createdRow).toBeVisible()

  await expect
    .poll(async () => await fetchProductByName(request, user.token, productName))
    .not.toBeNull()

  const createdProduct = await fetchProductByName(request, user.token, productName)
  expect(createdProduct).not.toBeNull()
  expect(createdProduct?.estoque_atual).toBe(7)
  expect(createdProduct?.ativo).toBeTruthy()

  await createdRow.getByRole('button', { name: 'Editar' }).click()
  await page.locator('#produto-nome').fill(editedProductName)
  await page.locator('#produto-preco-unitario').fill('34.90')
  await page.locator('#produto-preco-liquido').fill('30.10')
  await page.getByRole('button', { name: /Salvar altera/i }).click()

  const editedRow = page.getByRole('row').filter({
    has: page.getByRole('cell', { name: editedProductName, exact: true }),
  })
  await expect(editedRow).toBeVisible()

  await expect.poll(async () => {
    const product = await fetchProductByName(request, user.token, editedProductName)
    return product?.preco_unitario ?? null
  }).toBe(34.9)

  const deactivateResponsePromise = page.waitForResponse((response) => {
    return response.request().method() === 'DELETE'
      && response.url().endsWith(`/api/v1/produtos/${createdProduct!.id}`)
  })
  page.once('dialog', (dialog) => dialog.accept())
  await editedRow.getByRole('button', { name: 'Desativar' }).click()
  const deactivateResponse = await deactivateResponsePromise
  expect(deactivateResponse.ok()).toBeTruthy()

  await expect.poll(async () => {
    const product = await fetchProductByName(request, user.token, editedProductName)
    return product?.ativo ?? null
  }, { timeout: 30_000 }).toBe(false)

  await expect(editedRow).toHaveCount(0)
})
