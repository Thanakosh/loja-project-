import { expect, test } from './fixtures'
import { fulfillJson } from './helpers'

const duplicateCheckRoute = '**/api/v1/ai/check-duplicate'

test.describe('Importacao de nota', () => {
  test('deve processar um XML valido e concluir a importacao com resolucao de duplicatas', async ({ authenticatedPage: page }) => {
    const importedNames: string[] = []

    await page.route('**/api/v1/ocr/upload-arquivo', (route) =>
      fulfillJson(route, {
        task_id: 'task-e2e-1',
        status: 'completed',
        message: 'XML processado com sucesso!',
      }),
    )

    await page.route('**/api/v1/ocr/status/task-e2e-1', (route) =>
      fulfillJson(route, {
        task_id: 'task-e2e-1',
        status: 'completed',
        result: {
          nota_fiscal: {
            fornecedor: 'Fornecedor XML',
            nome_fantasia_fornecedor: 'Fornecedor XML LTDA',
            cnpj_fornecedor: '12345678000199',
            numero_nota: '99881',
            data_emissao: '2026-03-21',
            valor_total: 240,
            fornecedor_status: 'existente',
            produtos: [
              {
                nome: 'CABO FLEX 2,5MM',
                quantidade: 4,
                preco_unitario: 15,
                unidade: 'UN',
                codigo_ncm: '85444900',
                codigo_barras: '111',
              },
              {
                nome: 'DISJUNTOR 20A',
                quantidade: 2,
                preco_unitario: 90,
                unidade: 'UN',
                codigo_ncm: '85362000',
                codigo_barras: '222',
              },
            ],
          },
        },
      }),
    )

    await page.route(duplicateCheckRoute, async (route) => {
      const payload = route.request().postDataJSON() as { descricao: string }
      const descricao = payload.descricao.toLowerCase()

      if (descricao.includes('cabo flex')) {
        await fulfillJson(route, {
          tem_duplicata: true,
          tem_alerta: false,
          metodo: 'e2e',
          candidatos: [
            {
              produto_id: 101,
              produto_nome: 'CABO FLEX 2,5MM',
              similaridade: 0.99,
              nivel: 'duplicata',
            },
          ],
        })
        return
      }

      if (descricao.includes('disjuntor')) {
        await fulfillJson(route, {
          tem_duplicata: false,
          tem_alerta: true,
          metodo: 'e2e',
          candidatos: [
            {
              produto_id: 202,
              produto_nome: 'Disjuntor 20 A',
              similaridade: 0.87,
              nivel: 'alerta',
            },
          ],
        })
        return
      }

      await fulfillJson(route, { tem_duplicata: false, tem_alerta: false, metodo: 'e2e', candidatos: [] })
    })

    await page.route('**/api/v1/produtos/', async (route) => {
      const payload = route.request().postDataJSON() as { nome: string }
      importedNames.push(payload.nome)
      const estoqueSomado = payload.nome === 'CABO FLEX 2,5MM'
      await fulfillJson(
        route,
        { id: importedNames.length, nome: payload.nome },
        200,
        { 'x-produto-acao': estoqueSomado ? 'estoque_somado' : 'criado' },
      )
    })

    await page.goto('/#/importar-nota')

    await page.locator('input[type="file"]').setInputFiles({
      name: 'nota.xml',
      mimeType: 'application/xml',
      buffer: Buffer.from('<nfe />'),
    })
    await page.getByRole('button', { name: /processar xml/i }).click()

    await expect(page.getByRole('heading', { name: /dados da nota fiscal/i })).toBeVisible()
    await expect(page.getByPlaceholder('Nome do fornecedor')).toHaveValue('Fornecedor XML')
    await expect(page.getByText(/soma estoque/i)).toBeVisible()

    await page.getByRole('button', { name: /importar 2 produtos/i }).click()
    await expect(page.getByText(/ia detectou nomes similares/i)).toBeVisible()

    await page.getByLabel(/usar nome existente/i).check()
    await page.getByRole('button', { name: /confirmar resolucoes e importar/i }).click()

    await expect(page.getByRole('heading', { name: /importa..o conclu.da/i })).toBeVisible()
    await expect(page.getByText(/produtos novos foram cadastrados/i)).toBeVisible()
    expect(importedNames).toEqual(['CABO FLEX 2,5MM', 'Disjuntor 20 A'])
  })

  test('deve rejeitar arquivo invalido antes do upload', async ({ authenticatedPage: page }) => {
    await page.goto('/#/importar-nota')

    await page.locator('input[type="file"]').setInputFiles({
      name: 'nota.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('conteudo-invalido'),
    })

    await expect(page.getByText(/arquivo n.o suportado\. envie o xml da nfe/i)).toBeVisible()
    await expect(page.getByText(/arraste o xml da nfe aqui/i)).toBeVisible()
  })
})
