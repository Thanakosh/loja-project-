import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import api from '../services/api'

type StatusOrcamento = 'aberto' | 'aprovado' | 'cancelado' | 'convertido'
type FormaPagamento = 'dinheiro' | 'debito' | 'credito' | 'pix' | 'boleto' | 'crediario'

interface OrcamentoItem {
  id: number
  descricao: string
  quantidade: number
  preco_unitario: number
  desconto: number
  preco_total: number
}

interface Orcamento {
  id: number
  cliente_id?: number | null
  cliente_nome?: string | null
  status: StatusOrcamento
  desconto_geral: number
  observacao?: string | null
  data_criacao: string
  data_validade?: string | null
  venda_id?: number | null
  itens: OrcamentoItem[]
  total: number
}

interface OrcamentoListResponse {
  items: Orcamento[]
  total: number
  page: number
  pages: number
}

interface ItemFormState {
  descricao: string
  quantidade: string
  preco_unitario: string
  desconto: string
}

interface OrcamentoFormState {
  cliente_nome: string
  desconto_geral: string
  data_validade: string
  observacao: string
  itens: ItemFormState[]
}

const PAGE_SIZE = 20

const statusLabel: Record<StatusOrcamento, string> = {
  aberto: 'Aberto',
  aprovado: 'Aprovado',
  cancelado: 'Cancelado',
  convertido: 'Convertido'
}

const statusBadgeClass: Record<StatusOrcamento, string> = {
  aberto: 'bg-blue-50 text-blue-700',
  aprovado: 'bg-emerald-50 text-emerald-700',
  cancelado: 'bg-rose-50 text-rose-700',
  convertido: 'bg-purple-50 text-purple-700'
}

const moneyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL'
})

const createEmptyItem = (): ItemFormState => ({
  descricao: '',
  quantidade: '1',
  preco_unitario: '',
  desconto: '0'
})

const createInitialForm = (): OrcamentoFormState => ({
  cliente_nome: '',
  desconto_geral: '0',
  data_validade: '',
  observacao: '',
  itens: [createEmptyItem()]
})

const Orcamentos = () => {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<'todos' | StatusOrcamento>('todos')
  const [page, setPage] = useState(1)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [formState, setFormState] = useState<OrcamentoFormState>(createInitialForm)
  const [formError, setFormError] = useState('')

  const orcamentosQuery = useQuery({
    queryKey: ['orcamentos', statusFilter, page],
    queryFn: async () => {
      const response = await api.get('/orcamentos/', {
        params: {
          page,
          page_size: PAGE_SIZE,
          status: statusFilter === 'todos' ? undefined : statusFilter
        }
      })
      return response.data as OrcamentoListResponse
    },
    placeholderData: (previousData) => previousData
  })

  const createMutation = useMutation({
    mutationFn: async (payload: unknown) => {
      const response = await api.post('/orcamentos/', payload)
      return response.data as Orcamento
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orcamentos'] })
      setIsCreateModalOpen(false)
      setFormState(createInitialForm())
      setFormError('')
    },
    onError: () => {
      setFormError('Não foi possível criar o orçamento. Revise os dados e tente novamente.')
    }
  })

  const cancelMutation = useMutation({
    mutationFn: async (orcamentoId: number) => {
      await api.delete(`/orcamentos/${orcamentoId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orcamentos'] })
    }
  })

  const convertMutation = useMutation({
    mutationFn: async (orcamentoId: number) => {
      await api.post(`/orcamentos/${orcamentoId}/converter`, {
        forma_pagamento: 'pix' as FormaPagamento,
        parcelas: 1
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orcamentos'] })
    }
  })

  const orcamentos = orcamentosQuery.data?.items ?? []
  const totalPages = Math.max(1, orcamentosQuery.data?.pages ?? 1)

  const totalPreview = useMemo(() => {
    const descontoGeral = Number(formState.desconto_geral) || 0
    const subtotal = formState.itens.reduce((accumulator, item) => {
      const quantidade = Number(item.quantidade) || 0
      const precoUnitario = Number(item.preco_unitario) || 0
      const desconto = Number(item.desconto) || 0
      return accumulator + quantidade * precoUnitario * (1 - desconto / 100)
    }, 0)

    return Math.max(0, subtotal - descontoGeral)
  }, [formState])

  const handleOpenModal = () => {
    setFormState(createInitialForm())
    setFormError('')
    setIsCreateModalOpen(true)
  }

  const handleCreateSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setFormError('')

    if (!formState.cliente_nome.trim()) {
      setFormError('Informe o nome do cliente para criar o orçamento.')
      return
    }

    if (formState.itens.some((item) => !item.descricao.trim())) {
      setFormError('Todos os itens precisam ter descrição.')
      return
    }

    const payload = {
      cliente_nome: formState.cliente_nome.trim(),
      desconto_geral: Number(formState.desconto_geral) || 0,
      observacao: formState.observacao.trim() || null,
      data_validade: formState.data_validade || null,
      itens: formState.itens.map((item) => ({
        descricao: item.descricao.trim(),
        quantidade: Number(item.quantidade) || 0,
        preco_unitario: Number(item.preco_unitario) || 0,
        desconto: Number(item.desconto) || 0
      }))
    }

    createMutation.mutate(payload)
  }

  const updateItem = (index: number, field: keyof ItemFormState, value: string) => {
    setFormState((previous) => ({
      ...previous,
      itens: previous.itens.map((item, itemIndex) =>
        itemIndex === index
          ? {
              ...item,
              [field]: value
            }
          : item
      )
    }))
  }

  const addItem = () => {
    setFormState((previous) => ({
      ...previous,
      itens: [...previous.itens, createEmptyItem()]
    }))
  }

  const removeItem = (index: number) => {
    setFormState((previous) => ({
      ...previous,
      itens: previous.itens.length === 1 ? previous.itens : previous.itens.filter((_, i) => i !== index)
    }))
  }

  return (
    <div className="container mx-auto space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-800">Orçamentos</h1>
          <p className="text-sm text-gray-500">Gerencie propostas comerciais e converta em venda quando necessário.</p>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <select
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(event.target.value as 'todos' | StatusOrcamento)
              setPage(1)
            }}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="todos">Todos os status</option>
            <option value="aberto">Abertos</option>
            <option value="aprovado">Aprovados</option>
            <option value="cancelado">Cancelados</option>
            <option value="convertido">Convertidos</option>
          </select>

          <button
            onClick={handleOpenModal}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700"
          >
            Novo orçamento
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg bg-white shadow">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">ID</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Cliente</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Criação</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Total</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Ações</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-200 bg-white">
            {orcamentosQuery.isLoading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-500">
                  Carregando orçamentos...
                </td>
              </tr>
            ) : orcamentosQuery.isError ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-rose-500">
                  Erro ao buscar orçamentos. Tente novamente.
                </td>
              </tr>
            ) : orcamentos.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-500">
                  Nenhum orçamento encontrado para o filtro selecionado.
                </td>
              </tr>
            ) : (
              orcamentos.map((orcamento) => (
                <tr key={orcamento.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-600">#{orcamento.id}</td>
                  <td className="px-4 py-3 text-sm font-medium text-gray-800">{orcamento.cliente_nome ?? 'Cliente não informado'}</td>
                  <td className="px-4 py-3 text-sm">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${statusBadgeClass[orcamento.status]}`}>
                      {statusLabel[orcamento.status]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{new Date(orcamento.data_criacao).toLocaleDateString('pt-BR')}</td>
                  <td className="px-4 py-3 text-sm font-semibold text-emerald-600">{moneyFormatter.format(orcamento.total)}</td>
                  <td className="px-4 py-3 text-sm">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => cancelMutation.mutate(orcamento.id)}
                        disabled={orcamento.status !== 'aberto' || cancelMutation.isPending}
                        className="rounded border border-rose-200 px-2 py-1 text-xs font-medium text-rose-600 transition hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        Cancelar
                      </button>
                      <button
                        onClick={() => convertMutation.mutate(orcamento.id)}
                        disabled={(orcamento.status !== 'aberto' && orcamento.status !== 'aprovado') || convertMutation.isPending}
                        className="rounded border border-purple-200 px-2 py-1 text-xs font-medium text-purple-600 transition hover:bg-purple-50 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        Converter
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-end gap-2">
        <button
          onClick={() => setPage((previous) => Math.max(1, previous - 1))}
          disabled={page === 1}
          className="rounded border px-3 py-1.5 text-sm text-gray-600 transition hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Anterior
        </button>
        <span className="text-sm text-gray-500">
          Página {page} de {totalPages}
        </span>
        <button
          onClick={() => setPage((previous) => Math.min(totalPages, previous + 1))}
          disabled={page >= totalPages}
          className="rounded border px-3 py-1.5 text-sm text-gray-600 transition hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Próxima
        </button>
      </div>

      {isCreateModalOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-xl bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
              <h2 className="text-lg font-semibold text-gray-800">Novo orçamento</h2>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="text-2xl text-gray-400 transition hover:text-gray-600"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-5 px-6 py-5">
              <div className="grid gap-4 md:grid-cols-2">
                <label className="space-y-1 text-sm">
                  <span className="font-medium text-gray-700">Cliente</span>
                  <input
                    value={formState.cliente_nome}
                    onChange={(event) =>
                      setFormState((previous) => ({
                        ...previous,
                        cliente_nome: event.target.value
                      }))
                    }
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Nome do cliente"
                  />
                </label>

                <label className="space-y-1 text-sm">
                  <span className="font-medium text-gray-700">Validade</span>
                  <input
                    type="date"
                    value={formState.data_validade}
                    onChange={(event) =>
                      setFormState((previous) => ({
                        ...previous,
                        data_validade: event.target.value
                      }))
                    }
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </label>

                <label className="space-y-1 text-sm">
                  <span className="font-medium text-gray-700">Desconto geral (R$)</span>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={formState.desconto_geral}
                    onChange={(event) =>
                      setFormState((previous) => ({
                        ...previous,
                        desconto_geral: event.target.value
                      }))
                    }
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </label>
              </div>

              <label className="block space-y-1 text-sm">
                <span className="font-medium text-gray-700">Observação</span>
                <textarea
                  value={formState.observacao}
                  onChange={(event) =>
                    setFormState((previous) => ({
                      ...previous,
                      observacao: event.target.value
                    }))
                  }
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={2}
                  placeholder="Informações adicionais"
                />
              </label>

              <section className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-600">Itens do orçamento</h3>
                  <button
                    type="button"
                    onClick={addItem}
                    className="rounded border border-blue-200 px-2.5 py-1 text-xs font-semibold text-blue-700 hover:bg-blue-50"
                  >
                    + Adicionar item
                  </button>
                </div>

                {formState.itens.map((item, index) => (
                  <div key={`item-${index}`} className="grid gap-3 rounded-lg border border-gray-200 p-3 md:grid-cols-12">
                    <input
                      value={item.descricao}
                      onChange={(event) => updateItem(index, 'descricao', event.target.value)}
                      placeholder="Descrição"
                      className="md:col-span-5 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={item.quantidade}
                      onChange={(event) => updateItem(index, 'quantidade', event.target.value)}
                      placeholder="Qtd"
                      className="md:col-span-2 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={item.preco_unitario}
                      onChange={(event) => updateItem(index, 'preco_unitario', event.target.value)}
                      placeholder="Preço"
                      className="md:col-span-2 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.01"
                      value={item.desconto}
                      onChange={(event) => updateItem(index, 'desconto', event.target.value)}
                      placeholder="Desc.%"
                      className="md:col-span-2 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      type="button"
                      onClick={() => removeItem(index)}
                      className="md:col-span-1 rounded-lg border border-gray-300 px-2 py-2 text-sm text-gray-500 transition hover:bg-gray-100"
                    >
                      −
                    </button>
                  </div>
                ))}
              </section>

              <div className="rounded-lg bg-gray-50 px-4 py-3 text-sm text-gray-700">
                Total estimado: <span className="font-semibold text-emerald-600">{moneyFormatter.format(totalPreview)}</span>
              </div>

              {formError && <p className="text-sm font-medium text-rose-600">{formError}</p>}

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {createMutation.isPending ? 'Salvando...' : 'Salvar orçamento'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Orcamentos
