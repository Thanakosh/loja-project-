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
  nome_produto?: string
  nome?: string
  produto_nome?: string
  quantidade_atual?: number
  estoque_atual?: number
  estoque_minimo?: number
  quantidade_minima?: number
  estoque_baixo?: boolean
}

interface RiskDashboardNotaItem {
  nota_id: number
  numero_nota: number
  score: number
  classificacao: 'baixo' | 'medio' | 'alto'
}

interface RiskDashboardResponse {
  score_medio: number
  total_notas_analisadas: number
  total_alto_risco: number
  total_medio_risco: number
  total_baixo_risco: number
  notas_maior_risco: RiskDashboardNotaItem[]
  estado_vazio: boolean
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

const RISCO_CONFIG = {
  baixo: { label: 'Baixo', badgeClass: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' },
  medio: { label: 'Médio', badgeClass: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' },
  alto: { label: 'Alto', badgeClass: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' },
}

const DEFAULT_RISK_ANALYSIS_LIMIT = 20

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
          page: 1,
          page_size: 200
        }
      })

      const data = response.data
      const vendas: Venda[] = Array.isArray(data) ? data : (data?.items ?? [])
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
          page: 1,
          page_size: 200
        }
      })

      const data = response.data
      const vendas: Venda[] = Array.isArray(data) ? data : (data?.items ?? [])
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

  const saudeFiscalQuery = useQuery({
    queryKey: ['dashboard', 'saude-fiscal'],
    queryFn: async () => {
      const response = await api.get('/fiscal-ai/risk-dashboard', { params: { ultimas_n: DEFAULT_RISK_ANALYSIS_LIMIT } })
      return response.data as RiskDashboardResponse
    },
    refetchInterval: 60_000
  })

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  }

  const estoqueAlertas = estoqueAlertasQuery.data ?? []
  const saudeFiscal = saudeFiscalQuery.data

  const scoreMedio = saudeFiscal?.score_medio ?? 0
  const scoreColor =
    scoreMedio <= 30
      ? 'text-green-600 dark:text-green-400'
      : scoreMedio <= 60
        ? 'text-yellow-600 dark:text-yellow-400'
        : 'text-red-600 dark:text-red-400'
  const scoreBarColor =
    scoreMedio <= 30 ? 'bg-green-500' : scoreMedio <= 60 ? 'bg-yellow-500' : 'bg-red-500'

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

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <article className="rounded-lg bg-white dark:bg-gray-800 p-4 shadow">
          <p className="text-sm text-gray-500 dark:text-gray-400">🛒 Vendas Hoje</p>
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
          <p className="text-sm text-gray-500 dark:text-gray-400">📅 Vendas do Mês</p>
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
          <p className="text-sm text-gray-500 dark:text-gray-400">💰 Orçamentos Abertos</p>
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
          className={`rounded-lg bg-white dark:bg-gray-800 p-4 shadow ${estoqueAlertas.length > 0 ? 'border border-red-200 dark:border-red-700' : ''
            }`}
        >
          <p className={`text-sm ${estoqueAlertas.length > 0 ? 'text-red-500 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'}`}>
            ⚠️ Alertas de Estoque
          </p>
          <div className={`mt-2 text-2xl font-semibold ${estoqueAlertas.length > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-800 dark:text-gray-100'}`}>
            {estoqueAlertasQuery.isLoading ? (
              <CardSkeleton />
            ) : estoqueAlertasQuery.isError ? (
              '--'
            ) : (
              estoqueAlertas.length
            )}
          </div>
          {!produtosQuery.isLoading && !produtosQuery.isError && (
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">Total de produtos: {produtosQuery.data ?? 0}</p>
          )}
        </article>
      </div>

      {/* Card de Saúde Fiscal */}
      <section className="rounded-lg bg-white dark:bg-gray-800 p-5 shadow">
        <h2 className="mb-4 text-lg font-semibold text-gray-800 dark:text-gray-100">🏥 Saúde Fiscal</h2>

        {saudeFiscalQuery.isLoading ? (
          <div className="space-y-2">
            <div className="h-5 w-48 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
            <div className="h-3 w-full animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
          </div>
        ) : saudeFiscalQuery.isError ? (
          <p className="text-sm text-gray-400 dark:text-gray-500">Auditoria fiscal indisponível no momento.</p>
        ) : saudeFiscal?.estado_vazio ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">Nenhuma nota fiscal importada ainda.</p>
        ) : (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-6">
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Score médio de risco</p>
                <p className={`text-3xl font-bold ${scoreColor}`}>{scoreMedio.toFixed(1)}<span className="text-lg font-normal">/100</span></p>
                <div className="mt-1 h-2 w-40 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                  <div className={`h-full rounded-full ${scoreBarColor}`} style={{ width: `${scoreMedio}%` }} />
                </div>
              </div>

              <div className="flex gap-4 text-center">
                <div>
                  <p className="text-2xl font-semibold text-red-600 dark:text-red-400">{saudeFiscal.total_alto_risco}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Alto risco</p>
                </div>
                <div>
                  <p className="text-2xl font-semibold text-yellow-600 dark:text-yellow-400">{saudeFiscal.total_medio_risco}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Médio risco</p>
                </div>
                <div>
                  <p className="text-2xl font-semibold text-green-600 dark:text-green-400">{saudeFiscal.total_baixo_risco}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Baixo risco</p>
                </div>
              </div>

              <p className="text-xs text-gray-400 dark:text-gray-500 self-end">
                {saudeFiscal.total_notas_analisadas} nota{saudeFiscal.total_notas_analisadas !== 1 ? 's' : ''} analisada{saudeFiscal.total_notas_analisadas !== 1 ? 's' : ''}
              </p>
            </div>

            {saudeFiscal.notas_maior_risco.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-medium text-gray-600 dark:text-gray-400">Notas com maior risco:</p>
                <ul className="space-y-1">
                  {saudeFiscal.notas_maior_risco.map((nota) => {
                    const cfg = RISCO_CONFIG[nota.classificacao]
                    return (
                      <li key={nota.nota_id} className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${cfg.badgeClass}`}>{cfg.label}</span>
                        <span>Nota #{nota.numero_nota}</span>
                        <span className="text-gray-400 dark:text-gray-500">— score {nota.score.toFixed(1)}</span>
                      </li>
                    )
                  })}
                </ul>
              </div>
            )}
          </div>
        )}
      </section>

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
              const nomeProduto = alerta.nome_produto ?? alerta.nome ?? alerta.produto_nome ?? `Produto ${index + 1}`
              const estoqueAtual = alerta.quantidade_atual ?? alerta.estoque_atual ?? 0
              const estoqueMinimo = alerta.estoque_minimo ?? alerta.quantidade_minima ?? 0

              return (
                <li
                  key={alerta.id ?? alerta.produto_id ?? `${nomeProduto}-${index}`}
                  className="rounded-md border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-300"
                >
                  <span className="font-medium text-gray-800 dark:text-gray-100">{nomeProduto}</span>
                  <span className="ml-2 text-gray-600 dark:text-gray-400">
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
