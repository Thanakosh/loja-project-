import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { useVendasTotal } from '../hooks/useVendas'
import { useOrcamentosTotal } from '../hooks/useOrcamentos'
import { useProdutosTotal } from '../hooks/useProdutos'
import { useEstoqueAlertas } from '../hooks/useEstoque'
import { useFiscalRiskDashboard } from '../hooks/useDashboard'
import type { FiscalRiskDashboardResumo } from '../types/dashboard'

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)

const CardSkeleton = () => <div className="h-7 w-24 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />

const clampPercent = (value: number) => Math.max(0, Math.min(100, value))

const FiscalResumoCard = ({
  titulo,
  resumo,
}: {
  titulo: string
  resumo: FiscalRiskDashboardResumo
}) => {
  const score = clampPercent(resumo.score_medio)

  return (
    <article className="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900/30">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100">{titulo}</h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{resumo.periodo_rotulo}</p>
        </div>
        <span className="rounded-full bg-gray-200 px-2.5 py-1 text-xs font-medium text-gray-700 dark:bg-gray-700 dark:text-gray-200">
          {resumo.notas_risco_alto} alto
        </span>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-[120px_1fr]">
        <div className="rounded-lg bg-white p-3 dark:bg-gray-800">
          <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Score</p>
          <p className="mt-1 text-2xl font-semibold text-gray-900 dark:text-gray-100">{score.toFixed(1)}</p>
        </div>
        <div>
          <div className="h-2.5 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
            <div
              className={`h-full rounded-full transition-all ${score >= 61 ? 'bg-red-500' : score >= 31 ? 'bg-amber-500' : 'bg-emerald-500'}`}
              style={{ width: `${score}%` }}
            />
          </div>
          <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-lg bg-white p-3 dark:bg-gray-800">
              <p className="text-gray-500 dark:text-gray-400">Notas</p>
              <p className="mt-1 text-lg font-semibold text-gray-800 dark:text-gray-100">{resumo.total_notas}</p>
            </div>
            <div className="rounded-lg bg-white p-3 dark:bg-gray-800">
              <p className="text-gray-500 dark:text-gray-400">Risco alto</p>
              <p className="mt-1 text-lg font-semibold text-gray-800 dark:text-gray-100">{resumo.notas_risco_alto}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-600 dark:text-gray-300">Top alertas</h4>
        {resumo.top_fornecedores_alertas.length === 0 ? (
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">Nenhuma nota deste tipo ainda.</p>
        ) : (
          <ul className="mt-2 space-y-2">
            {resumo.top_fornecedores_alertas.map((fornecedor, index) => (
              <li
                key={`${titulo}-${fornecedor.nome}-${index}`}
                className="flex items-center justify-between rounded-lg bg-white px-3 py-2 text-sm dark:bg-gray-800"
              >
                <span className="font-medium text-gray-800 dark:text-gray-100">{fornecedor.nome}</span>
                <span className="text-gray-500 dark:text-gray-300">{fornecedor.alertas} alertas</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </article>
  )
}

const Dashboard = () => {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const hoje = new Date().toISOString().split('T')[0]
  const inicioMes = new Date(new Date().getFullYear(), new Date().getMonth(), 1)
    .toISOString()
    .split('T')[0]

  const vendasHojeQuery = useVendasTotal(
    {
      start_date: hoje,
      end_date: hoje,
      page: 1,
      page_size: 200,
    },
    'vendas-hoje',
  )

  const vendasMesQuery = useVendasTotal(
    {
      start_date: inicioMes,
      end_date: hoje,
      page: 1,
      page_size: 200,
    },
    'vendas-mes',
  )

  const orcamentosAbertosQuery = useOrcamentosTotal({
    status: 'aberto',
    page_size: 1,
  })

  const produtosQuery = useProdutosTotal()
  const estoqueAlertasQuery = useEstoqueAlertas()
  const fiscalDashboardQuery = useFiscalRiskDashboard()

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  }

  const estoqueAlertas = estoqueAlertasQuery.data ?? []
  const fiscalDashboard = fiscalDashboardQuery.data
  const fiscalScore = clampPercent(fiscalDashboard?.score_medio ?? 0)

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
          <p className="text-sm text-gray-500 dark:text-gray-400">Vendas Hoje</p>
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
          <p className="text-sm text-gray-500 dark:text-gray-400">Vendas do Mes</p>
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
          <p className="text-sm text-gray-500 dark:text-gray-400">Orcamentos Abertos</p>
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
            Alertas de Estoque
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

      <section className="rounded-lg bg-white p-5 shadow dark:bg-gray-800">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Saude Fiscal</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {fiscalDashboard?.periodo_rotulo ?? 'ultimas notas importadas'}
            </p>
          </div>
          {fiscalDashboard && fiscalDashboard.total_notas > 0 && (
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-700 dark:bg-amber-900/40 dark:text-amber-300">
              {fiscalDashboard.notas_risco_alto} com risco alto
            </span>
          )}
        </div>

        {fiscalDashboardQuery.isLoading ? (
          <div className="space-y-3">
            <CardSkeleton />
            <div className="h-2 w-full animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
          </div>
        ) : fiscalDashboardQuery.isError ? (
          <p className="text-sm text-red-600 dark:text-red-400">Erro ao carregar indicadores fiscais.</p>
        ) : !fiscalDashboard || fiscalDashboard.total_notas === 0 ? (
          <div className="rounded-lg border border-dashed border-gray-300 px-4 py-6 text-sm text-gray-500 dark:border-gray-600 dark:text-gray-400">
            Nenhuma nota importada ainda para calcular a saude fiscal.
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-[160px_1fr]">
              <div className="rounded-xl bg-emerald-50 p-4 dark:bg-emerald-950/30">
                <p className="text-xs uppercase tracking-wide text-emerald-700 dark:text-emerald-300">Score medio</p>
                <p className="mt-2 text-3xl font-semibold text-emerald-900 dark:text-emerald-100">{fiscalScore.toFixed(1)}</p>
              </div>
              <div>
                <div className="h-3 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                  <div
                    className={`h-full rounded-full transition-all ${fiscalScore >= 61 ? 'bg-red-500' : fiscalScore >= 31 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                    style={{ width: `${fiscalScore}%` }}
                  />
                </div>
                <div className="mt-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
                  <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-700/60">
                    <p className="text-gray-500 dark:text-gray-400">Notas analisadas</p>
                    <p className="mt-1 text-lg font-semibold text-gray-800 dark:text-gray-100">{fiscalDashboard.total_notas}</p>
                  </div>
                  <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-700/60">
                    <p className="text-gray-500 dark:text-gray-400">Risco alto</p>
                    <p className="mt-1 text-lg font-semibold text-gray-800 dark:text-gray-100">{fiscalDashboard.notas_risco_alto}</p>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-200">Top fornecedores com alertas</h3>
              <ul className="mt-3 space-y-2">
                {fiscalDashboard.top_fornecedores_alertas.map((fornecedor, index) => (
                  <li
                    key={`${fornecedor.nome}-${index}`}
                    className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-sm dark:bg-gray-700/60"
                  >
                    <span className="font-medium text-gray-800 dark:text-gray-100">{fornecedor.nome}</span>
                    <span className="text-gray-500 dark:text-gray-300">{fornecedor.alertas} alertas</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
              <FiscalResumoCard titulo="Notas de Entrada" resumo={fiscalDashboard.entradas} />
              <FiscalResumoCard titulo="Notas de Saida" resumo={fiscalDashboard.saidas} />
            </div>
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
                    Estoque: {estoqueAtual} / Minimo: {estoqueMinimo}
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
