import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import toast from 'react-hot-toast'

import api from '../services/api'
import type { CaixaDiario, MovimentacaoCaixa, TipoMovimentacaoCaixa } from '../types/caixa'

const formatCurrency = (value: number) =>
  value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

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
    <div className="space-y-6 p-4 md:p-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Controle de Caixa</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Sangrias, suprimentos e saldo esperado calculado no backend.
        </p>
      </div>

      {loadingAtual ? (
        <div className="text-gray-500 dark:text-gray-400">Carregando status do caixa...</div>
      ) : caixaAtual ? (
        <div className="space-y-6">
          <section className="space-y-4 rounded-2xl border border-emerald-300 bg-emerald-50 p-5 dark:border-emerald-700 dark:bg-emerald-900/20">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="inline-block h-3 w-3 animate-pulse rounded-full bg-emerald-500" />
                  <span className="font-semibold text-emerald-800 dark:text-emerald-300">
                    Caixa aberto desde {formatDatetime(caixaAtual.data_abertura)}
                  </span>
                </div>
                <p className="mt-1 text-sm text-emerald-700/80 dark:text-emerald-200/80">
                  Aberto por {formatUsuario(caixaAtual.usuario_abertura_nome, caixaAtual.usuario_abertura_id)}
                </p>
              </div>
              <div className="rounded-xl border border-emerald-200 bg-white/80 px-4 py-3 text-right dark:border-emerald-800 dark:bg-emerald-950/40">
                <p className="text-xs uppercase tracking-wide text-emerald-700 dark:text-emerald-300">
                  Saldo Esperado
                </p>
                <p className="text-2xl font-semibold text-emerald-900 dark:text-emerald-100">
                  {formatCurrency(caixaAtual.saldo_esperado)}
                </p>
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-4">
              {[
                ['Valor de abertura', caixaAtual.valor_abertura, 'text-gray-900 dark:text-gray-100'],
                ['Vendas em dinheiro', caixaAtual.valor_em_dinheiro_vendas, 'text-gray-900 dark:text-gray-100'],
                ['Total de suprimentos', caixaAtual.total_suprimentos, 'text-sky-700 dark:text-sky-300'],
                ['Total de sangrias', caixaAtual.total_sangrias, 'text-rose-700 dark:text-rose-300'],
              ].map(([label, value, tone]) => (
                <div key={label} className="rounded-xl border border-white/70 bg-white/80 p-4 dark:border-emerald-900 dark:bg-emerald-950/30">
                  <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">{label}</p>
                  <p className={`mt-2 text-lg font-semibold ${tone}`}>{formatCurrency(value as number)}</p>
                </div>
              ))}
            </div>
          </section>

          <div className="grid gap-6 xl:grid-cols-[1.1fr,0.9fr]">
            <section className="space-y-4 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-gray-900">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Movimentacoes</h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Retiradas e reforcos do caixa aberto.</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300"
                    onClick={() => setTipoMovimentacao('sangria')}
                  >
                    Registrar Sangria
                  </button>
                  <button
                    className="rounded-lg border border-sky-200 bg-sky-50 px-3 py-2 text-sm font-medium text-sky-700 dark:border-sky-900 dark:bg-sky-950/40 dark:text-sky-300"
                    onClick={() => setTipoMovimentacao('suprimento')}
                  >
                    Registrar Suprimento
                  </button>
                </div>
              </div>

              {tipoMovimentacao ? (
                <div className="space-y-3 rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-950/40">
                  <p className="text-sm font-semibold text-gray-800 dark:text-gray-100">
                    {MOVIMENTACAO_LABELS[tipoMovimentacao]}
                  </p>
                  <div className="grid gap-3 md:grid-cols-[180px,1fr]">
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={valorMovimentacao}
                      onChange={(event) => setValorMovimentacao(event.target.value)}
                      className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                      aria-label="Valor da movimentacao"
                    />
                    <input
                      type="text"
                      value={motivoMovimentacao}
                      onChange={(event) => setMotivoMovimentacao(event.target.value)}
                      placeholder="Motivo"
                      className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                      aria-label="Motivo da movimentacao"
                    />
                  </div>
                  <input
                    type="text"
                    value={obsMovimentacao}
                    onChange={(event) => setObsMovimentacao(event.target.value)}
                    placeholder="Observacao opcional"
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                    aria-label="Observacao da movimentacao"
                  />
                  <div className="flex flex-wrap gap-2">
                    <button
                      className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                      onClick={() => movimentacaoMutation.mutate()}
                      disabled={
                        movimentacaoMutation.isPending ||
                        !tipoMovimentacao ||
                        (parseFloat(valorMovimentacao) || 0) <= 0 ||
                        !motivoMovimentacao.trim()
                      }
                    >
                      {movimentacaoMutation.isPending ? 'Registrando...' : 'Salvar Movimentacao'}
                    </button>
                    <button
                      className="rounded-lg bg-gray-200 px-4 py-2 text-sm font-medium text-gray-800 dark:bg-gray-700 dark:text-gray-100"
                      onClick={() =>
                        resetMovimentacaoState(setTipoMovimentacao, setValorMovimentacao, setMotivoMovimentacao, setObsMovimentacao)
                      }
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              ) : null}

              {loadingMovimentacoes ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">Carregando movimentacoes...</p>
              ) : movimentacoes.length === 0 ? (
                <p className="rounded-xl border border-dashed border-gray-300 px-4 py-6 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
                  Nenhuma movimentacao registrada para este caixa.
                </p>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-xs uppercase text-gray-600 dark:bg-gray-800 dark:text-gray-300">
                      <tr>
                        <th className="px-4 py-3 text-left">Horario</th>
                        <th className="px-4 py-3 text-left">Tipo</th>
                        <th className="px-4 py-3 text-left">Motivo</th>
                        <th className="px-4 py-3 text-left">Usuario</th>
                        <th className="px-4 py-3 text-left">Observacao</th>
                        <th className="px-4 py-3 text-right">Valor</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                      {movimentacoes.map((movimentacao) => (
                        <tr key={movimentacao.id} className="text-gray-700 dark:text-gray-300">
                          <td className="px-4 py-3">{formatDatetime(movimentacao.created_at)}</td>
                          <td className="px-4 py-3">{MOVIMENTACAO_LABELS[movimentacao.tipo]}</td>
                          <td className="px-4 py-3">{movimentacao.motivo}</td>
                          <td className="px-4 py-3">{formatUsuario(movimentacao.usuario_nome, movimentacao.usuario_id)}</td>
                          <td className="px-4 py-3">{movimentacao.observacao || '-'}</td>
                          <td className="px-4 py-3 text-right font-medium">{formatCurrency(movimentacao.valor)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            <section className="space-y-4 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-gray-900">
              <div>
                <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Fechamento</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Diferencas usam o saldo esperado calculado pelo backend.
                </p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-950/40">
                  <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Esperado</p>
                  <p className="mt-2 text-xl font-semibold text-gray-900 dark:text-gray-100">
                    {formatCurrency(caixaAtual.saldo_esperado)}
                  </p>
                </div>
                <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-950/40">
                  <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Diferenca prevista</p>
                  <p className="mt-2 text-xl font-semibold text-gray-900 dark:text-gray-100">
                    {diferencaPreview == null ? '-' : `${diferencaPreview >= 0 ? '+' : ''}${formatCurrency(diferencaPreview)}`}
                  </p>
                </div>
              </div>

              {!confirmFechamento ? (
                <button className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white" onClick={() => setConfirmFechamento(true)}>
                  Fechar Caixa
                </button>
              ) : (
                <div className="space-y-3 rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-950/40">
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={valorFechamento}
                    onChange={(event) => setValorFechamento(event.target.value)}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                    aria-label="Valor contado no fechamento"
                  />
                  <input
                    type="text"
                    value={obsFechamento}
                    onChange={(event) => setObsFechamento(event.target.value)}
                    placeholder="Observacao do fechamento"
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                    aria-label="Observacao do fechamento"
                  />
                  {exigeObservacao ? (
                    <p className="text-sm font-medium text-amber-700 dark:text-amber-300">
                      Diferenca diferente de zero detectada. Informe observacao antes de confirmar.
                    </p>
                  ) : null}
                  <div className="flex flex-wrap gap-2">
                    <button
                      className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                      onClick={() => fecharMutation.mutate()}
                      disabled={fecharMutation.isPending}
                    >
                      {fecharMutation.isPending ? 'Fechando...' : 'Confirmar Fechamento'}
                    </button>
                    <button
                      className="rounded-lg bg-gray-200 px-4 py-2 text-sm font-medium text-gray-800 dark:bg-gray-700 dark:text-gray-100"
                      onClick={() => setConfirmFechamento(false)}
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              )}
            </section>
          </div>
        </div>
      ) : (
        <div className="space-y-4 rounded-2xl border border-amber-300 bg-amber-50 p-5 dark:border-amber-700 dark:bg-amber-900/20">
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full bg-amber-500" />
            <span className="font-semibold text-amber-800 dark:text-amber-300">
              Nenhum caixa aberto. O PDV permanece bloqueado ate a abertura.
            </span>
          </div>
          <div className="grid gap-3 md:grid-cols-[180px,1fr]">
            <input
              type="number"
              min="0"
              step="0.01"
              value={valorAbertura}
              onChange={(event) => setValorAbertura(event.target.value)}
              className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
              aria-label="Valor de abertura"
            />
            <input
              type="text"
              value={obsAbertura}
              onChange={(event) => setObsAbertura(event.target.value)}
              placeholder="Observacao da abertura"
              className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
              aria-label="Observacao da abertura"
            />
          </div>
          <button className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50" onClick={() => abrirMutation.mutate()} disabled={abrirMutation.isPending}>
            {abrirMutation.isPending ? 'Abrindo...' : 'Abrir Caixa'}
          </button>
        </div>
      )}

      <section>
        <div className="mb-3">
          <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200">Historico de Caixas</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Resumo de abertura, vendas em dinheiro, movimentacoes e resultado do fechamento.
          </p>
        </div>
        {loadingHistorico ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">Carregando...</p>
        ) : historico.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">Nenhum caixa registrado.</p>
        ) : (
          <div className="overflow-x-auto rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-900">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs uppercase text-gray-600 dark:bg-gray-800 dark:text-gray-300">
                <tr>
                  <th className="px-4 py-3 text-left">ID</th>
                  <th className="px-4 py-3 text-left">Abertura</th>
                  <th className="px-4 py-3 text-left">Fechamento</th>
                  <th className="px-4 py-3 text-left">Aberto por</th>
                  <th className="px-4 py-3 text-left">Fechado por</th>
                  <th className="px-4 py-3 text-right">Abertura</th>
                  <th className="px-4 py-3 text-right">Vendas dinheiro</th>
                  <th className="px-4 py-3 text-right">Suprimentos</th>
                  <th className="px-4 py-3 text-right">Sangrias</th>
                  <th className="px-4 py-3 text-right">Esperado</th>
                  <th className="px-4 py-3 text-right">Contado</th>
                  <th className="px-4 py-3 text-right">Diferenca</th>
                  <th className="px-4 py-3 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {historico.map((caixa) => (
                  <tr key={caixa.id} className="text-gray-700 dark:text-gray-300">
                    <td className="px-4 py-3">{caixa.id}</td>
                    <td className="px-4 py-3">{formatDatetime(caixa.data_abertura)}</td>
                    <td className="px-4 py-3">{caixa.data_fechamento ? formatDatetime(caixa.data_fechamento) : '-'}</td>
                    <td className="px-4 py-3">{formatUsuario(caixa.usuario_abertura_nome, caixa.usuario_abertura_id)}</td>
                    <td className="px-4 py-3">{formatUsuario(caixa.usuario_fechamento_nome, caixa.usuario_fechamento_id)}</td>
                    <td className="px-4 py-3 text-right">{formatCurrency(caixa.valor_abertura)}</td>
                    <td className="px-4 py-3 text-right">{formatCurrency(caixa.valor_em_dinheiro_vendas)}</td>
                    <td className="px-4 py-3 text-right">{formatCurrency(caixa.total_suprimentos)}</td>
                    <td className="px-4 py-3 text-right">{formatCurrency(caixa.total_sangrias)}</td>
                    <td className="px-4 py-3 text-right font-medium">{formatCurrency(caixa.saldo_esperado)}</td>
                    <td className="px-4 py-3 text-right">{caixa.valor_fechamento != null ? formatCurrency(caixa.valor_fechamento) : '-'}</td>
                    <td className="px-4 py-3 text-right font-medium">
                      {caixa.diferenca != null ? `${caixa.diferenca >= 0 ? '+' : ''}${formatCurrency(caixa.diferenca)}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${caixa.status === 'aberto' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'}`}>
                        {caixa.status === 'aberto' ? 'Aberto' : 'Fechado'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
