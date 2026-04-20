import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { useVendasTotal } from '../hooks/useVendas'
import { useOrcamentosTotal } from '../hooks/useOrcamentos'
import { useProdutosTotal } from '../hooks/useProdutos'
import { useEstoqueAlertas } from '../hooks/useEstoque'
import { useFiscalRiskDashboard } from '../hooks/useDashboard'
import type { FiscalRiskDashboardResumo } from '../types/dashboard'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardAction } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)

const CardSkeleton = () => <Skeleton className="h-7 w-24" />

const clampPercent = (value: number) => Math.max(0, Math.min(100, value))

const ScoreBar = ({ score }: { score: number }) => (
  <div className="h-2.5 overflow-hidden rounded-full bg-muted">
    <div
      className={`h-full rounded-full transition-all ${score >= 61 ? 'bg-destructive' : score >= 31 ? 'bg-amber-500' : 'bg-primary'}`}
      style={{ width: `${score}%` }}
    />
  </div>
)

const FiscalResumoCard = ({
  titulo,
  resumo,
}: {
  titulo: string
  resumo: FiscalRiskDashboardResumo
}) => {
  const score = clampPercent(resumo.score_medio)

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle className="text-sm">{titulo}</CardTitle>
            <CardDescription className="mt-1">{resumo.periodo_rotulo}</CardDescription>
          </div>
          <Badge variant="secondary">{resumo.notas_risco_alto} alto</Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid gap-3 sm:grid-cols-[120px_1fr]">
          <div className="rounded-lg bg-muted p-3">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Score</p>
            <p className="mt-1 text-2xl font-semibold">{score.toFixed(1)}</p>
          </div>
          <div>
            <ScoreBar score={score} />
            <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-lg bg-muted p-3">
                <p className="text-muted-foreground">Notas</p>
                <p className="mt-1 text-lg font-semibold">{resumo.total_notas}</p>
              </div>
              <div className="rounded-lg bg-muted p-3">
                <p className="text-muted-foreground">Risco alto</p>
                <p className="mt-1 text-lg font-semibold">{resumo.notas_risco_alto}</p>
              </div>
            </div>
          </div>
        </div>

        <Separator className="my-4" />

        <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Top alertas</h4>
        {resumo.top_fornecedores_alertas.length === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">Nenhuma nota deste tipo ainda.</p>
        ) : (
          <ul className="mt-2 space-y-2">
            {resumo.top_fornecedores_alertas.map((fornecedor, index) => (
              <li
                key={`${titulo}-${fornecedor.nome}-${index}`}
                className="flex items-center justify-between rounded-lg bg-muted px-3 py-2 text-sm"
              >
                <span className="font-medium">{fornecedor.nome}</span>
                <span className="text-muted-foreground">{fornecedor.alertas} alertas</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
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
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <Button onClick={handleRefresh}>
          Atualizar
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardDescription>Vendas Hoje</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold">
              {vendasHojeQuery.isLoading ? (
                <CardSkeleton />
              ) : vendasHojeQuery.isError ? (
                '--'
              ) : (
                formatCurrency(vendasHojeQuery.data ?? 0)
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardDescription>Vendas do Mes</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold">
              {vendasMesQuery.isLoading ? (
                <CardSkeleton />
              ) : vendasMesQuery.isError ? (
                '--'
              ) : (
                formatCurrency(vendasMesQuery.data ?? 0)
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardDescription>Orcamentos Abertos</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold">
              {orcamentosAbertosQuery.isLoading ? (
                <CardSkeleton />
              ) : orcamentosAbertosQuery.isError ? (
                '--'
              ) : (
                orcamentosAbertosQuery.data ?? 0
              )}
            </div>
          </CardContent>
        </Card>

        <Card className={estoqueAlertas.length > 0 ? 'ring-destructive/30' : ''}>
          <CardHeader>
            <CardDescription className={estoqueAlertas.length > 0 ? 'text-destructive' : ''}>
              Alertas de Estoque
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-semibold ${estoqueAlertas.length > 0 ? 'text-destructive' : ''}`}>
              {estoqueAlertasQuery.isLoading ? (
                <CardSkeleton />
              ) : estoqueAlertasQuery.isError ? (
                '--'
              ) : (
                estoqueAlertas.length
              )}
            </div>
            {!produtosQuery.isLoading && !produtosQuery.isError && (
              <p className="mt-2 text-xs text-muted-foreground">Total de produtos: {produtosQuery.data ?? 0}</p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Saude Fiscal</CardTitle>
          <CardDescription>
            {fiscalDashboard?.periodo_rotulo ?? 'ultimas notas importadas'}
          </CardDescription>
          {fiscalDashboard && fiscalDashboard.total_notas > 0 && (
            <CardAction>
              <Badge variant="outline" className="text-amber-600 border-amber-300 dark:text-amber-400 dark:border-amber-700">
                {fiscalDashboard.notas_risco_alto} com risco alto
              </Badge>
            </CardAction>
          )}
        </CardHeader>

        <CardContent>
          {fiscalDashboardQuery.isLoading ? (
            <div className="space-y-3">
              <CardSkeleton />
              <Skeleton className="h-2 w-full" />
            </div>
          ) : fiscalDashboardQuery.isError ? (
            <p className="text-sm text-destructive">Erro ao carregar indicadores fiscais.</p>
          ) : !fiscalDashboard || fiscalDashboard.total_notas === 0 ? (
            <div className="rounded-lg border border-dashed px-4 py-6 text-sm text-muted-foreground">
              Nenhuma nota importada ainda para calcular a saude fiscal.
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-[160px_1fr]">
                <div className="rounded-xl bg-primary/10 p-4">
                  <p className="text-xs uppercase tracking-wide text-primary">Score medio</p>
                  <p className="mt-2 text-3xl font-semibold">{fiscalScore.toFixed(1)}</p>
                </div>
                <div>
                  <div className="h-3 overflow-hidden rounded-full bg-muted">
                    <div
                      className={`h-full rounded-full transition-all ${fiscalScore >= 61 ? 'bg-destructive' : fiscalScore >= 31 ? 'bg-amber-500' : 'bg-primary'}`}
                      style={{ width: `${fiscalScore}%` }}
                    />
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
                    <div className="rounded-lg bg-muted p-3">
                      <p className="text-muted-foreground">Notas analisadas</p>
                      <p className="mt-1 text-lg font-semibold">{fiscalDashboard.total_notas}</p>
                    </div>
                    <div className="rounded-lg bg-muted p-3">
                      <p className="text-muted-foreground">Risco alto</p>
                      <p className="mt-1 text-lg font-semibold">{fiscalDashboard.notas_risco_alto}</p>
                    </div>
                  </div>
                </div>
              </div>

              <Separator />

              <div>
                <h3 className="text-sm font-semibold">Top fornecedores com alertas</h3>
                <ul className="mt-3 space-y-2">
                  {fiscalDashboard.top_fornecedores_alertas.map((fornecedor, index) => (
                    <li
                      key={`${fornecedor.nome}-${index}`}
                      className="flex items-center justify-between rounded-lg bg-muted px-3 py-2 text-sm"
                    >
                      <span className="font-medium">{fornecedor.nome}</span>
                      <span className="text-muted-foreground">{fornecedor.alertas} alertas</span>
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
        </CardContent>
      </Card>

      {estoqueAlertas.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Produtos com Estoque Baixo</CardTitle>
            <CardAction>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/estoque')}
              >
                Ver Estoque
              </Button>
            </CardAction>
          </CardHeader>

          <CardContent>
            <ul className="space-y-2">
              {estoqueAlertas.map((alerta, index) => {
                const nomeProduto = alerta.nome_produto ?? alerta.nome ?? alerta.produto_nome ?? `Produto ${index + 1}`
                const estoqueAtual = alerta.quantidade_atual ?? alerta.estoque_atual ?? 0
                const estoqueMinimo = alerta.estoque_minimo ?? alerta.quantidade_minima ?? 0

                return (
                  <li
                    key={alerta.id ?? alerta.produto_id ?? `${nomeProduto}-${index}`}
                    className="flex items-center justify-between rounded-lg border bg-muted/50 px-3 py-2 text-sm"
                  >
                    <span className="font-medium">{nomeProduto}</span>
                    <span className="text-muted-foreground">
                      Estoque: {estoqueAtual} / Minimo: {estoqueMinimo}
                    </span>
                  </li>
                )
              })}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default Dashboard
