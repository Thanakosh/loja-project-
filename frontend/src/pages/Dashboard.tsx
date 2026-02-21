import axios from 'axios'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import api from '../services/api'
import { getToken } from '../utils/auth'

const apiV2 = axios.create({ baseURL: api.defaults.baseURL?.replace('/api/v1', '/api/v2') })
apiV2.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

interface Venda {
  total?: number | string | null
}

interface OrcamentosResponse {
  total?: number
}

interface ProdutosResponse {
  total?: number
}

interface EstoqueAlerta {
  id?: number
  produto_id?: number
  nome?: string
  produto_nome?: string
  estoque_atual?: number
  quantidade_atual?: number
  estoque_minimo?: number
  quantidade_minima?: number
}

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)

const getVendaTotal = (venda: Venda) => {
  if (typeof venda.total === 'number') {
    return venda.total
  }

  const parsedValue = Number(venda.total)
  return Number.isFinite(parsedValue) ? parsedValue : 0
}

const CardSkeleton = () => <div className="h-7 w-24 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />

const Dashboard = () => {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const hoje = new Date().toISOString().split('T')[0]
  const inicioMes = new Date(new Date().getFullYear(), new Date().getMonth(), 1)
    .toISOString()
    .split('T')[0]

  const vendasHojeQuery = useQuery({
    queryKey: ['dashboard', 'vendas-hoje', hoje],
    queryFn: async () => {
      const response = await api.get('/vendas/', {
        params: {
          start_date: hoje,
          end_date: hoje,
          limit: 50
        }
      })

      const vendas = Array.isArray(response.data) ? (response.data as Venda[]) : []
      return vendas.reduce((accumulator, venda) => accumulator + getVendaTotal(venda), 0)
    },
    refetchInterval: 60_000
  })

  const vendasMesQuery = useQuery({
    queryKey: ['dashboard', 'vendas-mes', inicioMes, hoje],
    queryFn: async () => {
      const response = await api.get('/vendas/', {
        params: {
          start_date: inicioMes,
          end_date: hoje,
          limit: 50
        }
      })

      const vendas = Array.isArray(response.data) ? (response.data as Venda[]) : []
      return vendas.reduce((accumulator, venda) => accumulator + getVendaTotal(venda), 0)
    },
    refetchInterval: 60_000
  })

  const orcamentosAbertosQuery = useQuery({
    queryKey: ['dashboard', 'orcamentos-abertos'],
    queryFn: async () => {
      const response = await api.get('/orcamentos/', {
        params: {
          status: 'aberto',
          page_size: 1
        }
      })

      return (response.data as OrcamentosResponse).total ?? 0
    },
    refetchInterval: 60_000
  })

  const produtosQuery = useQuery({
    queryKey: ['dashboard', 'produtos-total'],
    queryFn: async () => {
      const response = await api.get('/produtos/', {
        params: {
          page: 1,
          page_size: 1
        }
      })

      return (response.data as ProdutosResponse).total ?? 0
    },
    refetchInterval: 60_000
  })

  const estoqueAlertasQuery = useQuery({
    queryKey: ['dashboard', 'estoque-alertas'],
    queryFn: async () => {
      const response = await apiV2.get('/estoque/alertas')

      return Array.isArray(response.data) ? (response.data as EstoqueAlerta[]) : []
    },
    refetchInterval: 60_000
  })

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  }

  const estoqueAlertas = estoqueAlertasQuery.data ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Dashboard</h1>
        <button
          type="button"
          onClick={handleRefresh}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-emerald-700"
        >
          Atualizar
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <article className="rounded-lg bg-white dark:bg-gray-800 p-4 shadow">
          <p className="text-sm text-gray-500">🛒 Vendas Hoje</p>
          <div className="mt-2 text-2xl font-semibold text-gray-800 dark:text-gray-100">
            {vendasHojeQuery.isLoading ? (
              <CardSkeleton />
            ) : vendasHojeQuery.isError ? (
              '--'
            ) : (
              formatCurrency(vendasHojeQuery.data ?? 0)
            )}
          </div>
        </article>

        <article className="rounded-lg bg-white dark:bg-gray-800 p-4 shadow">
          <p className="text-sm text-gray-500">📅 Vendas do Mês</p>
          <div className="mt-2 text-2xl font-semibold text-gray-800 dark:text-gray-100">
            {vendasMesQuery.isLoading ? (
              <CardSkeleton />
            ) : vendasMesQuery.isError ? (
              '--'
            ) : (
              formatCurrency(vendasMesQuery.data ?? 0)
            )}
          </div>
        </article>

        <article className="rounded-lg bg-white dark:bg-gray-800 p-4 shadow">
          <p className="text-sm text-gray-500">💰 Orçamentos Abertos</p>
          <div className="mt-2 text-2xl font-semibold text-gray-800 dark:text-gray-100">
            {orcamentosAbertosQuery.isLoading ? (
              <CardSkeleton />
            ) : orcamentosAbertosQuery.isError ? (
              '--'
            ) : (
              orcamentosAbertosQuery.data ?? 0
            )}
          </div>
        </article>

        <article
          className={`rounded-lg bg-white dark:bg-gray-800 p-4 shadow ${
            estoqueAlertas.length > 0 ? 'border border-red-200 dark:border-red-700' : ''
          }`}
        >
          <p className={`text-sm ${estoqueAlertas.length > 0 ? 'text-red-500' : 'text-gray-500'}`}>
            ⚠️ Alertas de Estoque
          </p>
          <div className={`mt-2 text-2xl font-semibold ${estoqueAlertas.length > 0 ? 'text-red-600' : 'text-gray-800'}`}>
            {estoqueAlertasQuery.isLoading ? (
              <CardSkeleton />
            ) : estoqueAlertasQuery.isError ? (
              '--'
            ) : (
              estoqueAlertas.length
            )}
          </div>
          {!produtosQuery.isLoading && !produtosQuery.isError && (
            <p className="mt-2 text-xs text-gray-500">Total de produtos: {produtosQuery.data ?? 0}</p>
          )}
        </article>
      </div>

      {estoqueAlertas.length > 0 && (
        <section className="rounded-lg bg-white dark:bg-gray-800 p-5 shadow">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Produtos com Estoque Baixo</h2>
            <button
              type="button"
              onClick={() => navigate('/estoque')}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700"
            >
              Ver Estoque
            </button>
          </div>

          <ul className="space-y-2">
            {estoqueAlertas.map((alerta, index) => {
              const nomeProduto = alerta.nome ?? alerta.produto_nome ?? `Produto ${index + 1}`
              const estoqueAtual = alerta.estoque_atual ?? alerta.quantidade_atual ?? 0
              const estoqueMinimo = alerta.estoque_minimo ?? alerta.quantidade_minima ?? 0

              return (
                <li
                  key={alerta.id ?? alerta.produto_id ?? `${nomeProduto}-${index}`}
                  className="rounded-md border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-300"
                >
                  <span className="font-medium text-gray-800 dark:text-gray-100">{nomeProduto}</span>
                  <span className="ml-2 text-gray-600">
                    Estoque: {estoqueAtual} / Mínimo: {estoqueMinimo}
                  </span>
                </li>
              )
            })}
          </ul>
        </section>
      )}
    </div>
  )
}

export default Dashboard
