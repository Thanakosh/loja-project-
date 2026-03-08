import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import toast from 'react-hot-toast'
import api from '../services/api'

interface CaixaDiario {
  id: number
  data_abertura: string
  data_fechamento?: string | null
  valor_abertura: number
  valor_fechamento?: number | null
  status: 'aberto' | 'fechado'
  observacao?: string | null
  usuario_id: number
  diferenca?: number | null
}

const formatCurrency = (v: number) =>
  v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const formatDatetime = (iso: string) =>
  new Date(iso).toLocaleString('pt-BR')

export default function CaixaDiario() {
  const queryClient = useQueryClient()
  const [valorAbertura, setValorAbertura] = useState('0')
  const [valorFechamento, setValorFechamento] = useState('0')
  const [obsAbertura, setObsAbertura] = useState('')
  const [obsFechamento, setObsFechamento] = useState('')
  const [confirmFechamento, setConfirmFechamento] = useState(false)

  // ── Consultas ──────────────────────────────────────────────────────────────

  const { data: caixaAtual, isLoading: loadingAtual } = useQuery<CaixaDiario | null>({
    queryKey: ['caixa-atual'],
    queryFn: async () => {
      try {
        const r = await api.get('/caixa/atual')
        return r.data
      } catch {
        return null
      }
    },
    retry: false,
  })

  const { data: historico = [], isLoading: loadingHistorico } = useQuery<CaixaDiario[]>({
    queryKey: ['caixa-historico'],
    queryFn: async () => {
      const r = await api.get('/caixa/historico?limit=20')
      return r.data
    },
  })

  // ── Mutações ───────────────────────────────────────────────────────────────

  const abrirMutation = useMutation({
    mutationFn: async () => {
      const r = await api.post('/caixa/abrir', {
        valor_abertura: parseFloat(valorAbertura) || 0,
        observacao: obsAbertura || null,
      })
      return r.data
    },
    onSuccess: () => {
      toast.success('Caixa aberto com sucesso!')
      setValorAbertura('0')
      setObsAbertura('')
      queryClient.invalidateQueries({ queryKey: ['caixa-atual'] })
      queryClient.invalidateQueries({ queryKey: ['caixa-historico'] })
    },
    onError: (err: unknown) => {
      const msg = isAxiosError<{ message?: string }>(err) ? err.response?.data?.message || 'Erro ao abrir caixa' : 'Erro ao abrir caixa'
      toast.error(msg)
    },
  })

  const fecharMutation = useMutation({
    mutationFn: async () => {
      if (!caixaAtual) return
      const r = await api.post(`/caixa/${caixaAtual.id}/fechar`, {
        valor_fechamento: parseFloat(valorFechamento) || 0,
        observacao: obsFechamento || null,
      })
      return r.data as CaixaDiario
    },
    onSuccess: (data) => {
      const dif = data?.diferenca ?? 0
      const sinal = dif >= 0 ? '+' : ''
      toast.success(`Caixa fechado! Diferença: ${sinal}${formatCurrency(dif)}`)
      setValorFechamento('0')
      setObsFechamento('')
      setConfirmFechamento(false)
      queryClient.invalidateQueries({ queryKey: ['caixa-atual'] })
      queryClient.invalidateQueries({ queryKey: ['caixa-historico'] })
    },
    onError: (err: unknown) => {
      const msg = isAxiosError<{ message?: string }>(err) ? err.response?.data?.message || 'Erro ao fechar caixa' : 'Erro ao fechar caixa'
      toast.error(msg)
    },
  })

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="p-4 md:p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">
        💵 Controle de Caixa
      </h1>

      {/* Status do caixa atual */}
      {loadingAtual ? (
        <div className="text-gray-500 dark:text-gray-400">Carregando status do caixa…</div>
      ) : caixaAtual ? (
        // ── Caixa aberto ──
        <div className="bg-green-50 dark:bg-green-900/30 border border-green-300 dark:border-green-700 rounded-xl p-4 space-y-4">
          <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full bg-green-500 animate-pulse" />
            <span className="font-semibold text-green-700 dark:text-green-300">
              Caixa aberto desde {formatDatetime(caixaAtual.data_abertura)}
            </span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            Valor de abertura:{' '}
            <strong>{formatCurrency(caixaAtual.valor_abertura)}</strong>
          </p>

          {/* Formulário de fechamento */}
          {!confirmFechamento ? (
            <button
              className="mt-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium"
              onClick={() => setConfirmFechamento(true)}
            >
              Fechar Caixa
            </button>
          ) : (
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Valor contado no fechamento (R$)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={valorFechamento}
                  onChange={e => setValorFechamento(e.target.value)}
                  className="w-full md:w-48 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Observação (opcional)
                </label>
                <input
                  type="text"
                  value={obsFechamento}
                  onChange={e => setObsFechamento(e.target.value)}
                  placeholder="ex: sangria, sobra de troco…"
                  className="w-full md:w-96 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex gap-2">
                <button
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
                  onClick={() => fecharMutation.mutate()}
                  disabled={fecharMutation.isPending}
                >
                  {fecharMutation.isPending ? 'Fechando…' : 'Confirmar Fechamento'}
                </button>
                <button
                  className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-100 rounded-lg text-sm font-medium"
                  onClick={() => setConfirmFechamento(false)}
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        // ── Caixa fechado: formulário de abertura ──
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-300 dark:border-yellow-700 rounded-xl p-4 space-y-4">
          <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full bg-yellow-500" />
            <span className="font-semibold text-yellow-700 dark:text-yellow-300">
              Nenhum caixa aberto — PDV bloqueado
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Valor de abertura / troco inicial (R$)
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={valorAbertura}
                onChange={e => setValorAbertura(e.target.value)}
                className="w-full md:w-48 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Observação (opcional)
              </label>
              <input
                type="text"
                value={obsAbertura}
                onChange={e => setObsAbertura(e.target.value)}
                placeholder="ex: abertura diária"
                className="w-full md:w-96 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
              onClick={() => abrirMutation.mutate()}
              disabled={abrirMutation.isPending}
            >
              {abrirMutation.isPending ? 'Abrindo…' : 'Abrir Caixa'}
            </button>
          </div>
        </div>
      )}

      {/* Histórico */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200 mb-3">
          Histórico de Caixas
        </h2>
        {loadingHistorico ? (
          <p className="text-gray-500 dark:text-gray-400 text-sm">Carregando…</p>
        ) : historico.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-sm">Nenhum caixa registrado.</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-300 uppercase text-xs">
                <tr>
                  <th className="px-4 py-3 text-left">ID</th>
                  <th className="px-4 py-3 text-left">Abertura</th>
                  <th className="px-4 py-3 text-left">Fechamento</th>
                  <th className="px-4 py-3 text-right">Vl. Abertura</th>
                  <th className="px-4 py-3 text-right">Vl. Fechamento</th>
                  <th className="px-4 py-3 text-right">Diferença</th>
                  <th className="px-4 py-3 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {historico.map(c => {
                  const dif =
                    c.valor_fechamento != null
                      ? c.valor_fechamento - c.valor_abertura
                      : null
                  return (
                    <tr
                      key={c.id}
                      className="hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300"
                    >
                      <td className="px-4 py-3">{c.id}</td>
                      <td className="px-4 py-3">{formatDatetime(c.data_abertura)}</td>
                      <td className="px-4 py-3">
                        {c.data_fechamento ? formatDatetime(c.data_fechamento) : '—'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {formatCurrency(c.valor_abertura)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {c.valor_fechamento != null
                          ? formatCurrency(c.valor_fechamento)
                          : '—'}
                      </td>
                      <td className={`px-4 py-3 text-right font-medium ${dif == null
                          ? 'text-gray-400'
                          : dif >= 0
                            ? 'text-green-600 dark:text-green-400'
                            : 'text-red-600 dark:text-red-400'
                        }`}>
                        {dif != null
                          ? `${dif >= 0 ? '+' : ''}${formatCurrency(dif)}`
                          : '—'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${c.status === 'aberto'
                              ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'
                              : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                            }`}
                        >
                          {c.status === 'aberto' ? 'Aberto' : 'Fechado'}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
