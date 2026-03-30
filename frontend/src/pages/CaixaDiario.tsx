import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import toast from 'react-hot-toast'

import api from '../services/api'
import type { CaixaDiario } from '../types/caixa'

const formatCurrency = (value: number) =>
  value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const formatDatetime = (iso: string) =>
  new Date(iso).toLocaleString('pt-BR')

const formatUsuario = (nome?: string | null, id?: number | null) => {
  if (nome && nome.trim()) {
    return nome
  }

  if (id != null) {
    return `Usuario #${id}`
  }

  return '-'
}

export default function CaixaDiarioPage() {
  const queryClient = useQueryClient()
  const [valorAbertura, setValorAbertura] = useState('0')
  const [valorFechamento, setValorFechamento] = useState('0')
  const [obsAbertura, setObsAbertura] = useState('')
  const [obsFechamento, setObsFechamento] = useState('')
  const [confirmFechamento, setConfirmFechamento] = useState(false)

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
    queryFn: async () => {
      const response = await api.get('/caixa/historico?limit=20')
      return response.data
    },
  })

  const abrirMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/caixa/abrir', {
        valor_abertura: parseFloat(valorAbertura) || 0,
        observacao: obsAbertura || null,
      })
      return response.data
    },
    onSuccess: () => {
      toast.success('Caixa aberto com sucesso!')
      setValorAbertura('0')
      setObsAbertura('')
      queryClient.invalidateQueries({ queryKey: ['caixa-atual'] })
      queryClient.invalidateQueries({ queryKey: ['caixa-historico'] })
    },
    onError: (error: unknown) => {
      const message = isAxiosError<{ message?: string }>(error)
        ? error.response?.data?.message || 'Erro ao abrir caixa'
        : 'Erro ao abrir caixa'
      toast.error(message)
    },
  })

  const fecharMutation = useMutation({
    mutationFn: async () => {
      if (!caixaAtual) {
        return
      }

      const response = await api.post(`/caixa/${caixaAtual.id}/fechar`, {
        valor_fechamento: parseFloat(valorFechamento) || 0,
        observacao: obsFechamento || null,
      })
      return response.data as CaixaDiario
    },
    onSuccess: (data) => {
      const diferenca = data?.diferenca ?? 0
      const sinal = diferenca >= 0 ? '+' : ''
      toast.success(`Caixa fechado! Diferenca: ${sinal}${formatCurrency(diferenca)}`)
      setValorFechamento('0')
      setObsFechamento('')
      setConfirmFechamento(false)
      queryClient.invalidateQueries({ queryKey: ['caixa-atual'] })
      queryClient.invalidateQueries({ queryKey: ['caixa-historico'] })
    },
    onError: (error: unknown) => {
      const message = isAxiosError<{ message?: string }>(error)
        ? error.response?.data?.message || 'Erro ao fechar caixa'
        : 'Erro ao fechar caixa'
      toast.error(message)
    },
  })

  return (
    <div className="space-y-6 p-4 md:p-6">
      <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">
        Controle de Caixa
      </h1>

      {loadingAtual ? (
        <div className="text-gray-500 dark:text-gray-400">Carregando status do caixa...</div>
      ) : caixaAtual ? (
        <div className="space-y-4 rounded-xl border border-green-300 bg-green-50 p-4 dark:border-green-700 dark:bg-green-900/30">
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 animate-pulse rounded-full bg-green-500" />
            <span className="font-semibold text-green-700 dark:text-green-300">
              Caixa aberto desde {formatDatetime(caixaAtual.data_abertura)}
            </span>
          </div>

          <div className="space-y-1 text-sm text-gray-600 dark:text-gray-300">
            <p>
              Valor de abertura: <strong>{formatCurrency(caixaAtual.valor_abertura)}</strong>
            </p>
            <p>
              Aberto por:{' '}
              <strong>{formatUsuario(caixaAtual.usuario_abertura_nome, caixaAtual.usuario_abertura_id)}</strong>
            </p>
          </div>

          {!confirmFechamento ? (
            <button
              className="mt-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
              onClick={() => setConfirmFechamento(true)}
            >
              Fechar Caixa
            </button>
          ) : (
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Valor contado no fechamento (R$)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={valorFechamento}
                  onChange={(event) => setValorFechamento(event.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 md:w-48"
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Observacao (opcional)
                </label>
                <input
                  type="text"
                  value={obsFechamento}
                  onChange={(event) => setObsFechamento(event.target.value)}
                  placeholder="ex: sangria, sobra de troco"
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 md:w-96"
                />
              </div>

              <div className="flex gap-2">
                <button
                  className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 hover:bg-red-700"
                  onClick={() => fecharMutation.mutate()}
                  disabled={fecharMutation.isPending}
                >
                  {fecharMutation.isPending ? 'Fechando...' : 'Confirmar Fechamento'}
                </button>
                <button
                  className="rounded-lg bg-gray-200 px-4 py-2 text-sm font-medium text-gray-800 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"
                  onClick={() => setConfirmFechamento(false)}
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4 rounded-xl border border-yellow-300 bg-yellow-50 p-4 dark:border-yellow-700 dark:bg-yellow-900/20">
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full bg-yellow-500" />
            <span className="font-semibold text-yellow-700 dark:text-yellow-300">
              Nenhum caixa aberto - PDV bloqueado
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Valor de abertura / troco inicial (R$)
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={valorAbertura}
                onChange={(event) => setValorAbertura(event.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 md:w-48"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Observacao (opcional)
              </label>
              <input
                type="text"
                value={obsAbertura}
                onChange={(event) => setObsAbertura(event.target.value)}
                placeholder="ex: abertura diaria"
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 md:w-96"
              />
            </div>

            <button
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 hover:bg-blue-700"
              onClick={() => abrirMutation.mutate()}
              disabled={abrirMutation.isPending}
            >
              {abrirMutation.isPending ? 'Abrindo...' : 'Abrir Caixa'}
            </button>
          </div>
        </div>
      )}

      <div>
        <h2 className="mb-3 text-lg font-semibold text-gray-700 dark:text-gray-200">
          Historico de Caixas
        </h2>

        {loadingHistorico ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">Carregando...</p>
        ) : historico.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">Nenhum caixa registrado.</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs uppercase text-gray-600 dark:bg-gray-800 dark:text-gray-300">
                <tr>
                  <th className="px-4 py-3 text-left">ID</th>
                  <th className="px-4 py-3 text-left">Abertura</th>
                  <th className="px-4 py-3 text-left">Fechamento</th>
                  <th className="px-4 py-3 text-left">Aberto por</th>
                  <th className="px-4 py-3 text-left">Fechado por</th>
                  <th className="px-4 py-3 text-right">Vl. Abertura</th>
                  <th className="px-4 py-3 text-right">Vl. Fechamento</th>
                  <th className="px-4 py-3 text-right">Diferenca</th>
                  <th className="px-4 py-3 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {historico.map((caixa) => {
                  const diferenca =
                    caixa.valor_fechamento != null
                      ? caixa.valor_fechamento - caixa.valor_abertura
                      : null

                  return (
                    <tr
                      key={caixa.id}
                      className="text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
                    >
                      <td className="px-4 py-3">{caixa.id}</td>
                      <td className="px-4 py-3">{formatDatetime(caixa.data_abertura)}</td>
                      <td className="px-4 py-3">
                        {caixa.data_fechamento ? formatDatetime(caixa.data_fechamento) : '-'}
                      </td>
                      <td className="px-4 py-3">
                        {formatUsuario(caixa.usuario_abertura_nome, caixa.usuario_abertura_id)}
                      </td>
                      <td className="px-4 py-3">
                        {formatUsuario(caixa.usuario_fechamento_nome, caixa.usuario_fechamento_id)}
                      </td>
                      <td className="px-4 py-3 text-right">{formatCurrency(caixa.valor_abertura)}</td>
                      <td className="px-4 py-3 text-right">
                        {caixa.valor_fechamento != null ? formatCurrency(caixa.valor_fechamento) : '-'}
                      </td>
                      <td
                        className={`px-4 py-3 text-right font-medium ${
                          diferenca == null
                            ? 'text-gray-400'
                            : diferenca >= 0
                              ? 'text-green-600 dark:text-green-400'
                              : 'text-red-600 dark:text-red-400'
                        }`}
                      >
                        {diferenca != null ? `${diferenca >= 0 ? '+' : ''}${formatCurrency(diferenca)}` : '-'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                            caixa.status === 'aberto'
                              ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'
                              : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                          }`}
                        >
                          {caixa.status === 'aberto' ? 'Aberto' : 'Fechado'}
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
