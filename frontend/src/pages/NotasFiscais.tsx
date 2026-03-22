import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { useAccessibleModal } from '../hooks/useAccessibleModal'
import api from '../services/api'

interface NotaFiscalItem {
  id: number
  nome_produto?: string | null
  unidade?: string | null
  quantidade: number
  preco_unitario: number
  preco_total: number
  ncm?: string | null
  cfop?: string | null
}

interface NotaFiscal {
  id: number
  numero_legado: number
  chave_acesso?: string | null
  serie?: string | null
  data_emissao?: string | null
  situacao: number
  entrada_saida?: 'E' | 'S' | null
  cfop_descricao?: string | null
  cliente_id?: number | null
  valor_produtos: number
  valor_total: number
  valor_desconto: number
  valor_icms: number
  valor_ipi: number
  observacao?: string | null
  itens: NotaFiscalItem[]
}

const LIMIT = 10

const moneyFormatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const dateFormatter = new Intl.DateTimeFormat('pt-BR')

const NotasFiscais = () => {
  const [dataInicio, setDataInicio] = useState('')
  const [dataFim, setDataFim] = useState('')
  const [appliedDataInicio, setAppliedDataInicio] = useState('')
  const [appliedDataFim, setAppliedDataFim] = useState('')
  const [page, setPage] = useState(1)
  const [notaSelecionadaId, setNotaSelecionadaId] = useState<number | null>(null)

  const skip = (page - 1) * LIMIT

  const notasQuery = useQuery({
    queryKey: ['notas-fiscais', skip, appliedDataInicio, appliedDataFim],
    queryFn: async () => {
      const response = await api.get('/notas-fiscais/', {
        params: {
          skip,
          limit: LIMIT,
          data_inicio: appliedDataInicio || undefined,
          data_fim: appliedDataFim || undefined
        }
      })
      return response.data as NotaFiscal[]
    },
    placeholderData: (previousData) => previousData
  })

  const detalhesNotaQuery = useQuery({
    queryKey: ['nota-fiscal', notaSelecionadaId],
    queryFn: async () => {
      const response = await api.get(`/notas-fiscais/${notaSelecionadaId}`)
      return response.data as NotaFiscal
    },
    enabled: notaSelecionadaId !== null
  })

  const notas = useMemo(() => notasQuery.data ?? [], [notasQuery.data])
  const hasNextPage = notas.length === LIMIT
  const closeDetalhesModal = () => setNotaSelecionadaId(null)
  const detalhesModalRef = useAccessibleModal(notaSelecionadaId !== null, closeDetalhesModal)

  const resumo = useMemo(() => {
    return notas.reduce(
      (acc, nota) => {
        acc.totalNotas += 1
        acc.totalValor += nota.valor_total
        return acc
      },
      { totalNotas: 0, totalValor: 0 }
    )
  }, [notas])

  const handleFiltrar = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setAppliedDataInicio(dataInicio)
    setAppliedDataFim(dataFim)
    setPage(1)
  }

  return (
    <div className="container mx-auto space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Notas Fiscais</h1>
        <form onSubmit={handleFiltrar} className="flex flex-wrap items-end gap-2">
          <div>
            <label className="mb-1 block text-xs text-gray-500 dark:text-gray-400">Data início</label>
            <input
              type="date"
              className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={dataInicio}
              onChange={(event) => setDataInicio(event.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-gray-500 dark:text-gray-400">Data fim</label>
            <input
              type="date"
              className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={dataFim}
              onChange={(event) => setDataFim(event.target.value)}
            />
          </div>
          <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700">Filtrar</button>
        </form>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg bg-white p-4 shadow dark:bg-gray-800">
          <p className="text-sm text-gray-500 dark:text-gray-400">Total de NFs no período/página</p>
          <p className="text-2xl font-semibold text-gray-800 dark:text-gray-100">{resumo.totalNotas}</p>
        </div>
        <div className="rounded-lg bg-white p-4 shadow dark:bg-gray-800">
          <p className="text-sm text-gray-500 dark:text-gray-400">Soma de valor total</p>
          <p className="text-2xl font-semibold text-gray-800 dark:text-gray-100">{moneyFormatter.format(resumo.totalValor)}</p>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg bg-white shadow dark:bg-gray-800">
        <table className="min-w-[860px] divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              {['Número', 'Data Emissão', 'Tipo', 'CFOP', 'Valor Produtos', 'Valor Total'].map((header) => (
                <th key={header} className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">{header}</th>
              ))}
              <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {notasQuery.isLoading ? (
              <tr><td colSpan={7} className="px-6 py-6 text-center text-gray-500 dark:text-gray-400">Carregando notas fiscais...</td></tr>
            ) : notasQuery.isError ? (
              <tr><td colSpan={7} className="px-6 py-6 text-center text-red-600 dark:text-red-400">Erro ao carregar notas fiscais.</td></tr>
            ) : notas.length === 0 ? (
              <tr><td colSpan={7} className="px-6 py-6 text-center text-gray-500 dark:text-gray-400">Nenhuma nota fiscal encontrada.</td></tr>
            ) : (
              notas.map((nota) => (
                <tr key={nota.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 text-sm font-medium text-gray-800 dark:text-gray-100">{nota.numero_legado}</td>
                  <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-300">{nota.data_emissao ? dateFormatter.format(new Date(nota.data_emissao)) : '-'}</td>
                  <td className="px-6 py-4 text-sm">
                    {nota.entrada_saida === 'E' ? (
                      <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">Entrada</span>
                    ) : nota.entrada_saida === 'S' ? (
                      <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">Saída</span>
                    ) : (
                      <span className="text-gray-500 dark:text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-300">{nota.cfop_descricao || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-300">{moneyFormatter.format(nota.valor_produtos)}</td>
                  <td className="px-6 py-4 text-sm font-medium text-gray-800 dark:text-gray-100">{moneyFormatter.format(nota.valor_total)}</td>
                  <td className="px-6 py-4 text-right text-sm">
                    <button
                      type="button"
                      onClick={() => setNotaSelecionadaId(nota.id)}
                      className="rounded-lg bg-indigo-600 px-3 py-2 text-white transition hover:bg-indigo-700"
                    >
                      Ver Itens
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <button
          type="button"
          onClick={() => setPage((prev) => Math.max(1, prev - 1))}
          disabled={page === 1}
          className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-gray-800 dark:text-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Anterior
        </button>
        <span className="text-sm text-gray-600 dark:text-gray-300">Página {page}</span>
        <button
          type="button"
          onClick={() => setPage((prev) => prev + 1)}
          disabled={!hasNextPage}
          className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-gray-800 dark:text-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Próxima
        </button>
      </div>

      {notaSelecionadaId !== null && (
        <div
          className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 px-4"
          role="dialog"
          aria-modal="true"
          aria-label="Detalhes da nota fiscal"
          onMouseDown={closeDetalhesModal}
        >
          <div
            ref={detalhesModalRef}
            tabIndex={-1}
            onMouseDown={(event) => event.stopPropagation()}
            className="max-h-[85vh] w-full max-w-5xl overflow-auto rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800"
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100">Itens da Nota Fiscal</h2>
              <button
                type="button"
                className="rounded-lg bg-gray-100 dark:bg-gray-700 px-3 py-2 text-gray-700 dark:text-gray-200"
                onClick={closeDetalhesModal}
              >
                Fechar
              </button>
            </div>

            {detalhesNotaQuery.isLoading ? (
              <p className="text-gray-500 dark:text-gray-400">Carregando itens...</p>
            ) : detalhesNotaQuery.isError ? (
              <p className="text-red-600 dark:text-red-400">Erro ao carregar detalhes da nota fiscal.</p>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-gray-300 dark:border-gray-600">
                <table className="min-w-[720px] divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      {['Produto', 'Unidade', 'Qtd', 'Preço Unit.', 'Total', 'NCM'].map((header) => (
                        <th key={header} className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">{header}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {(detalhesNotaQuery.data?.itens ?? []).length === 0 ? (
                      <tr><td colSpan={6} className="px-4 py-6 text-center text-gray-500 dark:text-gray-400">Nenhum item encontrado para esta NF.</td></tr>
                    ) : (
                      detalhesNotaQuery.data?.itens.map((item) => (
                        <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                          <td className="px-4 py-3 text-sm text-gray-800 dark:text-gray-100">{item.nome_produto || '-'}</td>
                          <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{item.unidade || '-'}</td>
                          <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{item.quantidade}</td>
                          <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{moneyFormatter.format(item.preco_unitario)}</td>
                          <td className="px-4 py-3 text-sm font-medium text-gray-800 dark:text-gray-100">{moneyFormatter.format(item.preco_total)}</td>
                          <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{item.ncm || '-'}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default NotasFiscais
