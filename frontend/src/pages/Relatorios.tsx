import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import api from '../services/api'

interface Venda {
  id: number
  data: string
  total?: number | string | null
  cliente_id?: number | null
  forma_pagamento?: number | string | null
}

interface Produto {
  id: number
  nome: string
  estoque_atual?: number | null
  estoque_minimo?: number | null
  estoque_baixo?: boolean
}

interface PaginatedProdutosResponse {
  items?: Produto[]
}

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)

const formatDate = (value: string) => {
  const parsedDate = new Date(value)
  return Number.isNaN(parsedDate.getTime()) ? '-' : parsedDate.toLocaleDateString('pt-BR')
}

const parseNumber = (value: number | string | null | undefined) => {
  if (typeof value === 'number') return value

  const parsedValue = Number(value)
  return Number.isFinite(parsedValue) ? parsedValue : 0
}

const PAYMENT_METHODS: Record<number, string> = {
  0: 'Não informado',
  1: 'Dinheiro',
  2: 'Cartão de Débito',
  3: 'Cartão de Crédito',
  4: 'Pix',
  5: 'Transferência',
  6: 'Boleto'
}

const getPaymentMethodLabel = (paymentMethod: number | string | null | undefined) => {
  const parsedMethod = Number(paymentMethod)
  if (!Number.isFinite(parsedMethod)) return 'Não informado'

  return PAYMENT_METHODS[parsedMethod] ?? `Código ${parsedMethod}`
}

const getTodayDate = () => new Date().toISOString().split('T')[0]

const Relatorios = () => {
  const [startDate, setStartDate] = useState(getTodayDate())
  const [endDate, setEndDate] = useState(getTodayDate())
  const [filterStartDate, setFilterStartDate] = useState(getTodayDate())
  const [filterEndDate, setFilterEndDate] = useState(getTodayDate())

  const vendasPeriodoQuery = useQuery({
    queryKey: ['relatorios', 'vendas-periodo', filterStartDate, filterEndDate],
    queryFn: async () => {
      const response = await api.get('/vendas/', {
        params: {
          data_inicio: filterStartDate,
          data_fim: filterEndDate,
          start_date: filterStartDate,
          end_date: filterEndDate,
          limit: 200
        }
      })

      return Array.isArray(response.data) ? (response.data as Venda[]) : []
    }
  })

  const resumoDiaQuery = useQuery({
    queryKey: ['relatorios', 'resumo-dia', getTodayDate()],
    queryFn: async () => {
      const today = getTodayDate()
      const response = await api.get('/vendas/', {
        params: {
          data_inicio: today,
          data_fim: today,
          start_date: today,
          end_date: today,
          limit: 200
        }
      })

      return Array.isArray(response.data) ? (response.data as Venda[]) : []
    }
  })

  const estoqueBaixoQuery = useQuery({
    queryKey: ['relatorios', 'estoque-baixo'],
    queryFn: async () => {
      const response = await api.get('/produtos/', {
        params: {
          estoque_baixo: true,
          page: 1,
          page_size: 200
        }
      })

      const responseData = response.data as PaginatedProdutosResponse | Produto[]
      const produtos = Array.isArray(responseData) ? responseData : (responseData.items ?? [])

      return produtos.filter((produto) => {
        if (produto.estoque_baixo) return true

        const estoqueAtual = produto.estoque_atual ?? 0
        const estoqueMinimo = produto.estoque_minimo ?? 0
        return estoqueAtual < estoqueMinimo
      })
    }
  })

  const resumoDia = useMemo(() => {
    const vendas = resumoDiaQuery.data ?? []
    const total = vendas.reduce((acc, venda) => acc + parseNumber(venda.total), 0)
    const transacoes = vendas.length
    const ticketMedio = transacoes > 0 ? total / transacoes : 0

    return {
      total,
      transacoes,
      ticketMedio
    }
  }, [resumoDiaQuery.data])

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setFilterStartDate(startDate)
    setFilterEndDate(endDate)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Relatórios</h1>
      </div>

      <section className="grid gap-4 md:grid-cols-3">
        <article className="rounded-lg bg-white p-4 shadow dark:bg-gray-800">
          <p className="text-sm text-gray-500 dark:text-gray-400">Total de vendas do dia</p>
          <p className="mt-2 text-2xl font-semibold text-emerald-600 dark:text-emerald-400">
            {resumoDiaQuery.isLoading ? 'Carregando...' : formatCurrency(resumoDia.total)}
          </p>
        </article>

        <article className="rounded-lg bg-white p-4 shadow dark:bg-gray-800">
          <p className="text-sm text-gray-500 dark:text-gray-400">Transações do dia</p>
          <p className="mt-2 text-2xl font-semibold text-gray-800 dark:text-gray-100">
            {resumoDiaQuery.isLoading ? 'Carregando...' : resumoDia.transacoes}
          </p>
        </article>

        <article className="rounded-lg bg-white p-4 shadow dark:bg-gray-800">
          <p className="text-sm text-gray-500 dark:text-gray-400">Ticket médio</p>
          <p className="mt-2 text-2xl font-semibold text-blue-600 dark:text-blue-400">
            {resumoDiaQuery.isLoading ? 'Carregando...' : formatCurrency(resumoDia.ticketMedio)}
          </p>
        </article>
      </section>

      <section className="rounded-lg bg-white p-5 shadow dark:bg-gray-800">
        <div className="mb-4 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Vendas por período</h2>

          <form onSubmit={handleSubmit} className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Data inicial</label>
              <input
                type="date"
                value={startDate}
                onChange={(event) => setStartDate(event.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-800 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Data final</label>
              <input
                type="date"
                value={endDate}
                onChange={(event) => setEndDate(event.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-800 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
              />
            </div>

            <button
              type="submit"
              className="rounded-lg bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700"
            >
              Filtrar
            </button>
          </form>
        </div>

        <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Data</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Cliente</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Forma de pagamento</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
              {vendasPeriodoQuery.isLoading ? (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-sm text-gray-500 dark:text-gray-400">Carregando vendas...</td>
                </tr>
              ) : vendasPeriodoQuery.isError ? (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-sm text-red-600 dark:text-red-400">Erro ao carregar vendas.</td>
                </tr>
              ) : (vendasPeriodoQuery.data ?? []).length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-sm text-gray-500 dark:text-gray-400">Nenhuma venda encontrada para o período.</td>
                </tr>
              ) : (
                (vendasPeriodoQuery.data ?? []).map((venda) => (
                  <tr key={venda.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/40">
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-200">{formatDate(venda.data)}</td>
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-200">
                      {venda.cliente_id ? `Cliente #${venda.cliente_id}` : 'Não informado'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-200">
                      {getPaymentMethodLabel(venda.forma_pagamento)}
                    </td>
                    <td className="px-4 py-3 text-right text-sm font-medium text-emerald-600 dark:text-emerald-400">
                      {formatCurrency(parseNumber(venda.total))}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-lg bg-white p-5 shadow dark:bg-gray-800">
        <h2 className="mb-4 text-lg font-semibold text-gray-800 dark:text-gray-100">Produtos com estoque baixo</h2>

        <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Produto</th>
                <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Estoque atual</th>
                <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Estoque mínimo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
              {estoqueBaixoQuery.isLoading ? (
                <tr>
                  <td colSpan={3} className="px-4 py-6 text-center text-sm text-gray-500 dark:text-gray-400">Carregando produtos...</td>
                </tr>
              ) : estoqueBaixoQuery.isError ? (
                <tr>
                  <td colSpan={3} className="px-4 py-6 text-center text-sm text-red-600 dark:text-red-400">Erro ao carregar produtos.</td>
                </tr>
              ) : (estoqueBaixoQuery.data ?? []).length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-4 py-6 text-center text-sm text-gray-500 dark:text-gray-400">Nenhum produto com estoque baixo.</td>
                </tr>
              ) : (
                (estoqueBaixoQuery.data ?? []).map((produto) => (
                  <tr key={produto.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/40">
                    <td className="px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-200">{produto.nome}</td>
                    <td className="px-4 py-3 text-center text-sm text-red-600 dark:text-red-400">{produto.estoque_atual ?? 0}</td>
                    <td className="px-4 py-3 text-center text-sm text-gray-700 dark:text-gray-200">{produto.estoque_minimo ?? 0}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

export default Relatorios
