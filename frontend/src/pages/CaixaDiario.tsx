import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import toast from 'react-hot-toast'

import api from '../services/api'
import type { CaixaDiario, MovimentacaoCaixa, TipoMovimentacaoCaixa } from '../types/caixa'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const formatCurrency = (value: number) => value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const formatDatetime = (iso: string) => new Date(iso).toLocaleString('pt-BR')

const formatUsuario = (nome?: string | null, id?: number | null) => {
  if (nome && nome.trim()) return nome
  if (id != null) return `Usuario #${id}`
  return '-'
}

const getErrorMessage = (error: unknown, fallback: string) => {
  if (isAxiosError<{ message?: string }>(error)) return error.response?.data?.message || fallback
  return fallback
}

const MOVIMENTACAO_LABELS: Record<TipoMovimentacaoCaixa, string> = {
  sangria: 'Sangria',
  suprimento: 'Suprimento',
}

const textareaClassName =
  'flex min-h-24 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm transition-colors outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50'

const resetMovimentacaoState = (
  setTipo: (value: TipoMovimentacaoCaixa | null) => void,
  setValor: (value: string) => void,
  setMotivo: (value: string) => void,
  setObs: (value: string) => void,
) => {
  setTipo(null)
  setValor('0')
  setMotivo('')
  setObs('')
}

export default function CaixaDiarioPage() {
  const queryClient = useQueryClient()
  const [valorAbertura, setValorAbertura] = useState('0')
  const [valorFechamento, setValorFechamento] = useState('0')
  const [obsAbertura, setObsAbertura] = useState('')
  const [obsFechamento, setObsFechamento] = useState('')
  const [confirmFechamento, setConfirmFechamento] = useState(false)
  const [tipoMovimentacao, setTipoMovimentacao] = useState<TipoMovimentacaoCaixa | null>(null)
  const [valorMovimentacao, setValorMovimentacao] = useState('0')
  const [motivoMovimentacao, setMotivoMovimentacao] = useState('')
  const [obsMovimentacao, setObsMovimentacao] = useState('')

  const { data: caixaAtual, isLoading: loadingAtual } = useQuery<CaixaDiario | null>({
    queryKey: ['caixa-atual'],
    queryFn: async () => {
      try {
        const response = await api.get('/caixa/atual')
        return response.data
      } catch {
        return null
      }
    },
    retry: false,
  })

  const { data: historico = [], isLoading: loadingHistorico } = useQuery<CaixaDiario[]>({
    queryKey: ['caixa-historico'],
    queryFn: async () => (await api.get('/caixa/historico?limit=20')).data,
  })

  const { data: movimentacoes = [], isLoading: loadingMovimentacoes } = useQuery<MovimentacaoCaixa[]>({
    queryKey: ['caixa-movimentacoes', caixaAtual?.id],
    queryFn: async () => (await api.get(`/caixa/${caixaAtual?.id}/movimentacoes`)).data,
    enabled: Boolean(caixaAtual?.id),
  })

  const refreshCaixa = () => {
    queryClient.invalidateQueries({ queryKey: ['caixa-atual'] })
    queryClient.invalidateQueries({ queryKey: ['caixa-historico'] })
    queryClient.invalidateQueries({ queryKey: ['caixa-movimentacoes'] })
  }

  const abrirMutation = useMutation({
    mutationFn: async () =>
      (
        await api.post('/caixa/abrir', {
          valor_abertura: parseFloat(valorAbertura) || 0,
          observacao: obsAbertura || null,
        })
      ).data,
    onSuccess: () => {
      toast.success('Caixa aberto com sucesso!')
      setValorAbertura('0')
      setObsAbertura('')
      refreshCaixa()
    },
    onError: (error: unknown) => toast.error(getErrorMessage(error, 'Erro ao abrir caixa')),
  })

  const fecharMutation = useMutation({
    mutationFn: async () =>
      (
        await api.post(`/caixa/${caixaAtual?.id}/fechar`, {
          valor_fechamento: parseFloat(valorFechamento) || 0,
          observacao: obsFechamento || null,
        })
      ).data as CaixaDiario,
    onSuccess: (data) => {
      toast.success(`Caixa fechado! Diferenca: ${formatCurrency(data.diferenca ?? 0)}`)
      setValorFechamento('0')
      setObsFechamento('')
      setConfirmFechamento(false)
      resetMovimentacaoState(setTipoMovimentacao, setValorMovimentacao, setMotivoMovimentacao, setObsMovimentacao)
      refreshCaixa()
    },
    onError: (error: unknown) => toast.error(getErrorMessage(error, 'Erro ao fechar caixa')),
  })

  const movimentacaoMutation = useMutation({
    mutationFn: async () =>
      (
        await api.post(`/caixa/${caixaAtual?.id}/movimentacoes`, {
          tipo: tipoMovimentacao,
          valor: parseFloat(valorMovimentacao) || 0,
          motivo: motivoMovimentacao.trim(),
          observacao: obsMovimentacao || null,
        })
      ).data,
    onSuccess: () => {
      toast.success(`${tipoMovimentacao === 'sangria' ? 'Sangria' : 'Suprimento'} registrada com sucesso!`)
      resetMovimentacaoState(setTipoMovimentacao, setValorMovimentacao, setMotivoMovimentacao, setObsMovimentacao)
      refreshCaixa()
    },
    onError: (error: unknown) => toast.error(getErrorMessage(error, 'Erro ao registrar movimentacao')),
  })

  const valorContado = parseFloat(valorFechamento) || 0
  const diferencaPreview = caixaAtual ? valorContado - caixaAtual.saldo_esperado : null
  const exigeObservacao = diferencaPreview != null && Math.abs(diferencaPreview) > 0.009 && !obsFechamento.trim()

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold">Controle de caixa</h1>
        <p className="text-sm text-muted-foreground">Sangrias, suprimentos e saldo esperado calculado no backend.</p>
      </div>

      {loadingAtual ? (
        <p className="text-sm text-muted-foreground">Carregando status do caixa...</p>
      ) : caixaAtual ? (
        <div className="space-y-6">
          <Alert>
            <AlertTitle>Caixa aberto</AlertTitle>
            <AlertDescription>
              Aberto desde {formatDatetime(caixaAtual.data_abertura)} por {formatUsuario(caixaAtual.usuario_abertura_nome, caixaAtual.usuario_abertura_id)}.
            </AlertDescription>
          </Alert>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {[
              ['Saldo esperado', formatCurrency(caixaAtual.saldo_esperado)],
              ['Valor de abertura', formatCurrency(caixaAtual.valor_abertura)],
              ['Vendas em dinheiro', formatCurrency(caixaAtual.valor_em_dinheiro_vendas)],
              ['Total de suprimentos', formatCurrency(caixaAtual.total_suprimentos)],
            ].map(([label, value]) => (
              <Card size="sm" key={label}>
                <CardHeader>
                  <CardDescription>{label}</CardDescription>
                  <CardTitle>{value}</CardTitle>
                </CardHeader>
              </Card>
            ))}
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <Card>
              <CardHeader className="gap-3">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div className="space-y-1">
                    <CardTitle>Movimentacoes</CardTitle>
                    <CardDescription>Retiradas e reforcos realizados enquanto o caixa permanece aberto.</CardDescription>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button type="button" variant="outline" size="sm" onClick={() => setTipoMovimentacao('sangria')}>
                      Registrar sangria
                    </Button>
                    <Button type="button" variant="outline" size="sm" onClick={() => setTipoMovimentacao('suprimento')}>
                      Registrar suprimento
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {tipoMovimentacao && (
                  <Card size="sm">
                    <CardHeader>
                      <CardTitle className="text-sm">{MOVIMENTACAO_LABELS[tipoMovimentacao]}</CardTitle>
                      <CardDescription>Informe valor, motivo e observacao opcional.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid gap-4 md:grid-cols-[180px_1fr]">
                        <div className="space-y-2">
                          <Label htmlFor="caixa-movimentacao-valor">Valor</Label>
                          <Input id="caixa-movimentacao-valor" type="number" min="0.01" step="0.01" value={valorMovimentacao} onChange={(event) => setValorMovimentacao(event.target.value)} />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="caixa-movimentacao-motivo">Motivo</Label>
                          <Input id="caixa-movimentacao-motivo" value={motivoMovimentacao} onChange={(event) => setMotivoMovimentacao(event.target.value)} placeholder="Motivo" />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="caixa-movimentacao-observacao">Observacao</Label>
                        <textarea id="caixa-movimentacao-observacao" value={obsMovimentacao} onChange={(event) => setObsMovimentacao(event.target.value)} className={textareaClassName} rows={3} placeholder="Observacao opcional" />
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button
                          type="button"
                          onClick={() => movimentacaoMutation.mutate()}
                          disabled={movimentacaoMutation.isPending || !tipoMovimentacao || (parseFloat(valorMovimentacao) || 0) <= 0 || !motivoMovimentacao.trim()}
                        >
                          {movimentacaoMutation.isPending ? 'Registrando...' : 'Salvar movimentacao'}
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => resetMovimentacaoState(setTipoMovimentacao, setValorMovimentacao, setMotivoMovimentacao, setObsMovimentacao)}
                        >
                          Cancelar
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {loadingMovimentacoes ? (
                  <p className="text-sm text-muted-foreground">Carregando movimentacoes...</p>
                ) : movimentacoes.length === 0 ? (
                  <Alert>
                    <AlertTitle>Nenhuma movimentacao registrada</AlertTitle>
                    <AlertDescription>Este caixa ainda nao possui sangrias ou suprimentos registrados.</AlertDescription>
                  </Alert>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Horario</TableHead>
                        <TableHead>Tipo</TableHead>
                        <TableHead>Motivo</TableHead>
                        <TableHead>Usuario</TableHead>
                        <TableHead>Observacao</TableHead>
                        <TableHead className="text-right">Valor</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {movimentacoes.map((movimentacao) => (
                        <TableRow key={movimentacao.id}>
                          <TableCell className="text-muted-foreground">{formatDatetime(movimentacao.created_at)}</TableCell>
                          <TableCell>
                            <Badge variant="secondary" className={movimentacao.tipo === 'sangria' ? 'bg-destructive/10 text-destructive' : 'bg-sky-500/10 text-sky-700 dark:text-sky-300'}>
                              {MOVIMENTACAO_LABELS[movimentacao.tipo]}
                            </Badge>
                          </TableCell>
                          <TableCell>{movimentacao.motivo}</TableCell>
                          <TableCell className="text-muted-foreground">{formatUsuario(movimentacao.usuario_nome, movimentacao.usuario_id)}</TableCell>
                          <TableCell className="text-muted-foreground">{movimentacao.observacao || '-'}</TableCell>
                          <TableCell className="text-right font-medium">{formatCurrency(movimentacao.valor)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Fechamento</CardTitle>
                <CardDescription>Diferencas usam o saldo esperado calculado pelo backend.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  <Card size="sm">
                    <CardHeader>
                      <CardDescription>Esperado</CardDescription>
                      <CardTitle>{formatCurrency(caixaAtual.saldo_esperado)}</CardTitle>
                    </CardHeader>
                  </Card>
                  <Card size="sm">
                    <CardHeader>
                      <CardDescription>Diferenca prevista</CardDescription>
                      <CardTitle>
                        {diferencaPreview == null ? '-' : `${diferencaPreview >= 0 ? '+' : ''}${formatCurrency(diferencaPreview)}`}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                </div>

                {!confirmFechamento ? (
                  <Button type="button" variant="destructive" onClick={() => setConfirmFechamento(true)}>
                    Fechar caixa
                  </Button>
                ) : (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="caixa-valor-fechamento">Valor contado no fechamento</Label>
                      <Input id="caixa-valor-fechamento" type="number" min="0" step="0.01" value={valorFechamento} onChange={(event) => setValorFechamento(event.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="caixa-obs-fechamento">Observacao do fechamento</Label>
                      <Input id="caixa-obs-fechamento" value={obsFechamento} onChange={(event) => setObsFechamento(event.target.value)} />
                    </div>
                    {exigeObservacao && (
                      <Alert>
                        <AlertTitle>Diferenca detectada</AlertTitle>
                        <AlertDescription>Informe observacao antes de confirmar o fechamento com diferenca.</AlertDescription>
                      </Alert>
                    )}
                    <div className="flex flex-wrap gap-2">
                      <Button type="button" variant="destructive" onClick={() => fecharMutation.mutate()} disabled={fecharMutation.isPending}>
                        {fecharMutation.isPending ? 'Fechando...' : 'Confirmar fechamento'}
                      </Button>
                      <Button type="button" variant="outline" onClick={() => setConfirmFechamento(false)}>
                        Cancelar
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Nenhum caixa aberto</CardTitle>
            <CardDescription>O PDV permanece bloqueado ate a abertura do caixa do dia.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-[180px_1fr]">
              <div className="space-y-2">
                <Label htmlFor="caixa-valor-abertura">Valor de abertura</Label>
                <Input id="caixa-valor-abertura" type="number" min="0" step="0.01" value={valorAbertura} onChange={(event) => setValorAbertura(event.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="caixa-obs-abertura">Observacao da abertura</Label>
                <Input id="caixa-obs-abertura" value={obsAbertura} onChange={(event) => setObsAbertura(event.target.value)} />
              </div>
            </div>
            <Button type="button" onClick={() => abrirMutation.mutate()} disabled={abrirMutation.isPending}>
              {abrirMutation.isPending ? 'Abrindo...' : 'Abrir caixa'}
            </Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Historico de caixas</CardTitle>
          <CardDescription>Resumo de abertura, vendas em dinheiro, movimentacoes e resultado do fechamento.</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingHistorico ? (
            <p className="text-sm text-muted-foreground">Carregando...</p>
          ) : historico.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nenhum caixa registrado.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Abertura</TableHead>
                  <TableHead>Fechamento</TableHead>
                  <TableHead>Aberto por</TableHead>
                  <TableHead>Fechado por</TableHead>
                  <TableHead className="text-right">Abertura</TableHead>
                  <TableHead className="text-right">Vendas dinheiro</TableHead>
                  <TableHead className="text-right">Suprimentos</TableHead>
                  <TableHead className="text-right">Sangrias</TableHead>
                  <TableHead className="text-right">Esperado</TableHead>
                  <TableHead className="text-right">Contado</TableHead>
                  <TableHead className="text-right">Diferenca</TableHead>
                  <TableHead className="text-center">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {historico.map((caixa) => (
                  <TableRow key={caixa.id}>
                    <TableCell>{caixa.id}</TableCell>
                    <TableCell>{formatDatetime(caixa.data_abertura)}</TableCell>
                    <TableCell>{caixa.data_fechamento ? formatDatetime(caixa.data_fechamento) : '-'}</TableCell>
                    <TableCell className="text-muted-foreground">{formatUsuario(caixa.usuario_abertura_nome, caixa.usuario_abertura_id)}</TableCell>
                    <TableCell className="text-muted-foreground">{formatUsuario(caixa.usuario_fechamento_nome, caixa.usuario_fechamento_id)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(caixa.valor_abertura)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(caixa.valor_em_dinheiro_vendas)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(caixa.total_suprimentos)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(caixa.total_sangrias)}</TableCell>
                    <TableCell className="text-right font-medium">{formatCurrency(caixa.saldo_esperado)}</TableCell>
                    <TableCell className="text-right">{caixa.valor_fechamento != null ? formatCurrency(caixa.valor_fechamento) : '-'}</TableCell>
                    <TableCell className="text-right font-medium">
                      {caixa.diferenca != null ? `${caixa.diferenca >= 0 ? '+' : ''}${formatCurrency(caixa.diferenca)}` : '-'}
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant={caixa.status === 'aberto' ? 'secondary' : 'outline'} className={caixa.status === 'aberto' ? 'bg-primary/10 text-primary' : 'text-muted-foreground'}>
                        {caixa.status === 'aberto' ? 'Aberto' : 'Fechado'}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
