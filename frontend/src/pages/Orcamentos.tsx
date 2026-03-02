import { useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { isAxiosError } from 'axios'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import api from '../services/api'

type StatusOrcamento = 'aberto' | 'aprovado' | 'cancelado' | 'convertido'

interface ClienteSugestao {
  id: number
  nome: string
  cpf_cnpj?: string | null
}

interface ProdutoSugestao {
  id: number
  nome: string
  preco_unitario: number
  preco_liquido: number
  unidade_medida?: string | null
}

// Enum espelhando backend/app/core/enums.py FormaPagamento (int)
const FormaPagamento = {
  DINHEIRO: 1,
  CARTAO_DEBITO: 2,
  CARTAO_CREDITO: 3,
  PIX: 4,
  BOLETO: 5,
  PRAZO: 6
} as const
type FormaPagamentoValue = typeof FormaPagamento[keyof typeof FormaPagamento]

const formaPagamentoLabel: Record<FormaPagamentoValue, string> = {
  1: 'Dinheiro',
  2: 'Cartão Débito',
  3: 'Cartão Crédito',
  4: 'PIX',
  5: 'Boleto',
  6: 'A Prazo'
}

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

interface OrcamentoFormState {
  cliente_id: number | null
  cliente_nome: string
  desconto_geral: string
  data_validade: string
  observacao: string
  itens: ItemFormState[]
}

interface ItemFormState {
  produto_id: number | null
  descricao: string
  quantidade: string
  preco_unitario: string
  desconto: string
}

const PAGE_SIZE = 20

const statusLabel: Record<StatusOrcamento, string> = {
  aberto: 'Aberto',
  aprovado: 'Aprovado',
  cancelado: 'Cancelado',
  convertido: 'Convertido'
}

const statusBadgeClass: Record<StatusOrcamento, string> = {
  aberto: 'bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400',
  aprovado: 'bg-emerald-50 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400',
  cancelado: 'bg-rose-50 dark:bg-rose-900/40 text-rose-700 dark:text-rose-400',
  convertido: 'bg-purple-50 dark:bg-purple-900/40 text-purple-700 dark:text-purple-400'
}

const moneyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL'
})

const createEmptyItem = (): ItemFormState => ({
  produto_id: null,
  descricao: '',
  quantidade: '1',
  preco_unitario: '',
  desconto: '0'
})

const createInitialForm = (): OrcamentoFormState => ({
  cliente_id: null,
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

  // --- Autocomplete cliente ---
  const [clienteSearch, setClienteSearch] = useState('')
  const [showClienteSugestoes, setShowClienteSugestoes] = useState(false)
  const clienteRef = useRef<HTMLDivElement>(null)

  const clientesQuery = useQuery({
    queryKey: ['clientes-sugestao', clienteSearch],
    queryFn: async () => {
      const resp = await api.get('/clientes/', { params: { search: clienteSearch, limit: 8 } })
      return resp.data as ClienteSugestao[]
    },
    enabled: isCreateModalOpen && clienteSearch.length >= 1,
  })

  // --- Autocomplete produto: search por item ---
  const [produtoSearches, setProdutoSearches] = useState<string[]>([''])
  const [showProdutoSugestoes, setShowProdutoSugestoes] = useState<boolean[]>([false])
  const [activeProdutoIndex, setActiveProdutoIndex] = useState<number | null>(null)
  const [produtoResults, setProdutoResults] = useState<ProdutoSugestao[]>([])
  const produtoSearchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)

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
      toast.success('Orçamento criado com sucesso!')
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
      toast.success('Orçamento cancelado com sucesso!')
    }
  })

  const [downloadingPdfId, setDownloadingPdfId] = useState<number | null>(null)

  const handleExportarPdf = async (orcamento: Orcamento) => {
    setDownloadingPdfId(orcamento.id)
    try {
      const response = await api.get(`/orcamentos/${orcamento.id}/pdf`, {
        responseType: 'blob',
      })
      const url = URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
      const link = document.createElement('a')
      link.href = url
      link.download = `orcamento-${String(orcamento.id).padStart(5, '0')}.pdf`
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch {
      toast.error('Erro ao gerar PDF. Tente novamente.')
    } finally {
      setDownloadingPdfId(null)
    }
  }

  const [convertModal, setConvertModal] = useState<{ orcamentoId: number } | null>(null)
  const [convertError, setConvertError] = useState('')
  const [convertForm, setConvertForm] = useState<{ forma_pagamento: FormaPagamentoValue; parcelas: number }>({
    forma_pagamento: FormaPagamento.PIX,
    parcelas: 1
  })

  const convertMutation = useMutation({
    mutationFn: async ({ orcamentoId, forma_pagamento, parcelas }: { orcamentoId: number; forma_pagamento: FormaPagamentoValue; parcelas: number }) => {
      await api.post(`/orcamentos/${orcamentoId}/converter`, {
        forma_pagamento,
        parcelas
      })
    },
    onError: (error) => {
      let message = 'Não foi possível converter o orçamento. Tente novamente.'

      if (isAxiosError(error)) {
        const apiData = error.response?.data as {
          message?: unknown
          detail?: unknown
          details?: {
            produto_nome?: string
            disponivel?: number
            solicitado?: number
          }
        } | undefined

        const detail = apiData?.message ?? apiData?.detail

        if (typeof detail === 'string') {
          if (apiData?.details?.produto_nome) {
            const disponivel = apiData.details.disponivel ?? 0
            const solicitado = apiData.details.solicitado ?? 0
            message = `${detail}: ${apiData.details.produto_nome} (disponível: ${disponivel}, solicitado: ${solicitado}).`
          } else {
            message = detail
          }
        } else if (Array.isArray(detail)) {
          const parsedDetail = detail
            .map((item) => {
              if (typeof item === 'string') {
                return item
              }
              return (item as { msg?: string })?.msg
            })
            .filter(Boolean)
            .join(' | ')

          message = parsedDetail || 'Não foi possível converter o orçamento.'
        }
      }

      setConvertError(message)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orcamentos'] })
      setConvertModal(null)
      setConvertError('')
      toast.success('Orçamento convertido em venda com sucesso!')
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

  const buscarProdutos = (search: string, index: number) => {
    if (produtoSearchTimeout.current) clearTimeout(produtoSearchTimeout.current)
    if (!search.trim()) { setProdutoResults([]); return }
    produtoSearchTimeout.current = setTimeout(async () => {
      try {
        const resp = await api.get('/produtos/', { params: { search: search.trim(), page_size: 8 } })
        // Só atualiza se o índice ainda for o ativo
        setActiveProdutoIndex((current) => {
          if (current === index) setProdutoResults(resp.data.items ?? [])
          return current
        })
      } catch { /* silencioso */ }
    }, 250)
  }

  const handleOpenModal = () => {
    setFormState(createInitialForm())
    setFormError('')
    setClienteSearch('')
    setShowClienteSugestoes(false)
    setProdutoSearches([''])
    setShowProdutoSugestoes([false])
    setProdutoResults([])
    setActiveProdutoIndex(null)
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
      cliente_id: formState.cliente_id || null,
      cliente_nome: formState.cliente_nome.trim(),
      desconto_geral: Number(formState.desconto_geral) || 0,
      observacao: formState.observacao.trim() || null,
      data_validade: formState.data_validade || null,
      itens: formState.itens.map((item) => ({
        produto_id: item.produto_id || null,
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
    setFormState((previous) => ({ ...previous, itens: [...previous.itens, createEmptyItem()] }))
    setProdutoSearches((prev) => [...prev, ''])
    setShowProdutoSugestoes((prev) => [...prev, false])
  }

  const removeItem = (index: number) => {
    if (formState.itens.length === 1) return
    setFormState((previous) => ({ ...previous, itens: previous.itens.filter((_, i) => i !== index) }))
    setProdutoSearches((prev) => prev.filter((_, i) => i !== index))
    setShowProdutoSugestoes((prev) => prev.filter((_, i) => i !== index))
  }

  const selecionarCliente = (cliente: ClienteSugestao) => {
    setFormState((prev) => ({ ...prev, cliente_id: cliente.id, cliente_nome: cliente.nome }))
    setClienteSearch(cliente.nome)
    setShowClienteSugestoes(false)
  }

  const selecionarProduto = (index: number, produto: ProdutoSugestao) => {
    setFormState((prev) => ({
      ...prev,
      itens: prev.itens.map((item, i) =>
        i === index
          ? { ...item, produto_id: produto.id, descricao: produto.nome, preco_unitario: String(produto.preco_unitario) }
          : item
      )
    }))
    setProdutoSearches((prev) => prev.map((s, i) => i === index ? produto.nome : s))
    setShowProdutoSugestoes((prev) => prev.map((_, i) => i === index ? false : _))
    setActiveProdutoIndex(null)
  }

  return (
    <div className="container mx-auto space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Orçamentos</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Gerencie propostas comerciais e converta em venda quando necessário.</p>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <select
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(event.target.value as 'todos' | StatusOrcamento)
              setPage(1)
            }}
            className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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

      <div className="overflow-hidden rounded-lg bg-white dark:bg-gray-800 shadow">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">ID</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Cliente</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Criação</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Total</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Ações</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-800">
            {orcamentosQuery.isLoading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
                  Carregando orçamentos...
                </td>
              </tr>
            ) : orcamentosQuery.isError ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-rose-500 dark:text-rose-400">
                  Erro ao buscar orçamentos. Tente novamente.
                </td>
              </tr>
            ) : orcamentos.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
                  Nenhum orçamento encontrado para o filtro selecionado.
                </td>
              </tr>
            ) : (
              orcamentos.map((orcamento) => (
                <tr key={orcamento.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">#{orcamento.id}</td>
                  <td className="px-4 py-3 text-sm font-medium text-gray-800 dark:text-gray-100">{orcamento.cliente_nome ?? 'Cliente não informado'}</td>
                  <td className="px-4 py-3 text-sm">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${statusBadgeClass[orcamento.status]}`}>
                      {statusLabel[orcamento.status]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{new Date(orcamento.data_criacao).toLocaleDateString('pt-BR')}</td>
                  <td className="px-4 py-3 text-sm font-semibold text-emerald-600">{moneyFormatter.format(orcamento.total)}</td>
                  <td className="px-4 py-3 text-sm">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => cancelMutation.mutate(orcamento.id)}
                        disabled={orcamento.status !== 'aberto' || cancelMutation.isPending}
                        className="rounded border border-rose-200 dark:border-rose-700 px-2 py-1 text-xs font-medium text-rose-600 dark:text-rose-400 transition hover:bg-rose-50 dark:hover:bg-rose-900/40 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        Cancelar
                      </button>
                      <button
                        onClick={() => {
                          setConvertForm({ forma_pagamento: FormaPagamento.PIX, parcelas: 1 })
                          setConvertError('')
                          setConvertModal({ orcamentoId: orcamento.id })
                        }}
                        disabled={(orcamento.status !== 'aberto' && orcamento.status !== 'aprovado') || convertMutation.isPending}
                        className="rounded border border-purple-200 dark:border-purple-700 px-2 py-1 text-xs font-medium text-purple-600 dark:text-purple-400 transition hover:bg-purple-50 dark:hover:bg-purple-900/40 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        Converter
                      </button>
                      <button
                        type="button"
                        onClick={() => handleExportarPdf(orcamento)}
                        disabled={downloadingPdfId === orcamento.id}
                        className="rounded border border-emerald-200 dark:border-emerald-700 px-2 py-1 text-xs font-medium text-emerald-600 dark:text-emerald-400 transition hover:bg-emerald-50 dark:hover:bg-emerald-900/40 disabled:cursor-not-allowed disabled:opacity-50"
                        title="Exportar PDF"
                      >
                        {downloadingPdfId === orcamento.id ? '...' : 'PDF'}
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
          className="rounded border border-gray-300 dark:border-gray-600 px-3 py-1.5 text-sm text-gray-700 dark:text-gray-300 transition hover:bg-gray-50 dark:hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Anterior
        </button>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          Página {page} de {totalPages}
        </span>
        <button
          onClick={() => setPage((previous) => Math.min(totalPages, previous + 1))}
          disabled={page >= totalPages}
          className="rounded border border-gray-300 dark:border-gray-600 px-3 py-1.5 text-sm text-gray-700 dark:text-gray-300 transition hover:bg-gray-50 dark:hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Próxima
        </button>
      </div>

      {convertModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-sm rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
              <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Converter em Venda</h2>
              <button onClick={() => setConvertModal(null)} className="text-2xl text-gray-400 hover:text-gray-600">×</button>
            </div>
            <div className="space-y-4 px-6 py-5">
              <label className="block space-y-1 text-sm">
                <span className="font-medium text-gray-700 dark:text-gray-300">Forma de Pagamento</span>
                <select
                  value={convertForm.forma_pagamento}
                  onChange={(e) => setConvertForm(prev => ({ ...prev, forma_pagamento: Number(e.target.value) as FormaPagamentoValue }))}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  {(Object.entries(FormaPagamento) as [string, FormaPagamentoValue][]).map(([, value]) => (
                    <option key={value} value={value}>{formaPagamentoLabel[value]}</option>
                  ))}
                </select>
              </label>
              {convertForm.forma_pagamento === FormaPagamento.PRAZO && (
                <label className="block space-y-1 text-sm">
                  <span className="font-medium text-gray-700 dark:text-gray-300">Número de Parcelas</span>
                  <input
                    type="number"
                    min={1}
                    max={48}
                    value={convertForm.parcelas}
                    onChange={(e) => setConvertForm(prev => ({ ...prev, parcelas: Math.max(1, Number(e.target.value)) }))}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </label>
              )}
              {convertError && (
                <div className="rounded-md border border-rose-300/60 dark:border-rose-700 bg-rose-50 dark:bg-rose-900/20 px-3 py-2 text-sm text-rose-700 dark:text-rose-300">
                  {convertError}
                </div>
              )}
              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={() => {
                    setConvertModal(null)
                    setConvertError('')
                  }}
                  className="rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancelar
                </button>
                <button
                  onClick={() => convertMutation.mutate({ orcamentoId: convertModal.orcamentoId, ...convertForm })}
                  disabled={convertMutation.isPending}
                  className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-purple-700 disabled:opacity-60"
                >
                  {convertMutation.isPending ? 'Convertendo...' : 'Confirmar'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {isCreateModalOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
              <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Novo orçamento</h2>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="text-2xl text-gray-400 transition hover:text-gray-600"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-5 px-6 py-5">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-1 text-sm" ref={clienteRef}>
                  <span className="font-medium text-gray-700 dark:text-gray-300">Cliente</span>
                  <div className="relative">
                    <input
                      value={clienteSearch}
                      onChange={(e) => {
                        const v = e.target.value
                        setClienteSearch(v)
                        setFormState((prev) => ({ ...prev, cliente_id: null, cliente_nome: v }))
                        setShowClienteSugestoes(true)
                      }}
                      onFocus={() => { if (clienteSearch) setShowClienteSugestoes(true) }}
                      onBlur={() => setTimeout(() => setShowClienteSugestoes(false), 150)}
                      className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Digite para buscar cliente..."
                    />
                    {showClienteSugestoes && clientesQuery.data && clientesQuery.data.length > 0 && (
                      <ul className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                        {clientesQuery.data.map((c) => (
                          <li
                            key={c.id}
                            onMouseDown={() => selecionarCliente(c)}
                            className="px-3 py-2 text-sm cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/40 text-gray-800 dark:text-gray-100"
                          >
                            <span className="font-medium">{c.nome}</span>
                            {c.cpf_cnpj && <span className="ml-2 text-xs text-gray-400">{c.cpf_cnpj}</span>}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                  {formState.cliente_id && (
                    <p className="text-xs text-emerald-600 dark:text-emerald-400">✓ Cliente vinculado (ID {formState.cliente_id})</p>
                  )}
                </div>

                <label className="space-y-1 text-sm">
                  <span className="font-medium text-gray-700 dark:text-gray-300">Validade</span>
                  <input
                    type="date"
                    value={formState.data_validade}
                    onChange={(event) =>
                      setFormState((previous) => ({
                        ...previous,
                        data_validade: event.target.value
                      }))
                    }
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </label>

                <label className="space-y-1 text-sm">
                  <span className="font-medium text-gray-700 dark:text-gray-300">Desconto geral (R$)</span>
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
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </label>
              </div>

              <label className="block space-y-1 text-sm">
                <span className="font-medium text-gray-700 dark:text-gray-300">Observação</span>
                <textarea
                  value={formState.observacao}
                  onChange={(event) =>
                    setFormState((previous) => ({
                      ...previous,
                      observacao: event.target.value
                    }))
                  }
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={2}
                  placeholder="Informações adicionais"
                />
              </label>

              <section className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-600 dark:text-gray-400">Itens do orçamento</h3>
                  <button
                    type="button"
                    onClick={addItem}
                    className="rounded border border-blue-200 dark:border-blue-700 px-2.5 py-1 text-xs font-semibold text-blue-700 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/40"
                  >
                    + Adicionar item
                  </button>
                </div>

                {formState.itens.map((item, index) => (
                  <div key={`item-${index}`} className="rounded-lg border border-gray-200 dark:border-gray-700 p-3 space-y-2">
                    {/* Linha 1: busca de produto + botão remover */}
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <input
                          value={produtoSearches[index] ?? ''}
                          onChange={(e) => {
                            const v = e.target.value
                            setProdutoSearches((prev) => prev.map((s, i) => i === index ? v : s))
                            updateItem(index, 'descricao', v)
                            setFormState((prev) => ({
                              ...prev,
                              itens: prev.itens.map((it, i) => i === index ? { ...it, produto_id: null } : it)
                            }))
                            setActiveProdutoIndex(index)
                            setShowProdutoSugestoes((prev) => prev.map((_, i) => i === index ? true : _))
                            buscarProdutos(v, index)
                          }}
                          onFocus={() => {
                            setActiveProdutoIndex(index)
                            if ((produtoSearches[index]?.length ?? 0) >= 1) {
                              setShowProdutoSugestoes((prev) => prev.map((_, i) => i === index ? true : _))
                              buscarProdutos(produtoSearches[index] ?? '', index)
                            }
                          }}
                          onBlur={() => setTimeout(() => {
                            setShowProdutoSugestoes((prev) => prev.map((_, i) => i === index ? false : _))
                          }, 150)}
                          placeholder="Buscar produto ou digitar descrição..."
                          className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        {showProdutoSugestoes[index] && activeProdutoIndex === index && produtoResults.length > 0 && (
                          <ul className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                            {produtoResults.map((p) => (
                              <li
                                key={p.id}
                                onMouseDown={() => selecionarProduto(index, p)}
                                className="px-3 py-2 text-sm cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/40 text-gray-800 dark:text-gray-100"
                              >
                                <span className="font-medium">{p.nome}</span>
                                <span className="ml-2 text-xs text-gray-400">{moneyFormatter.format(p.preco_unitario)}</span>
                                {p.unidade_medida && <span className="ml-1 text-xs text-gray-400">/ {p.unidade_medida}</span>}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                      <button
                        type="button"
                        onClick={() => removeItem(index)}
                        disabled={formState.itens.length === 1}
                        className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 text-sm text-gray-500 transition hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30"
                      >
                        −
                      </button>
                    </div>
                    {item.produto_id && (
                      <p className="text-xs text-emerald-600 dark:text-emerald-400">✓ Produto vinculado</p>
                    )}
                    {/* Linha 2: qtd, preço, desconto */}
                    <div className="grid grid-cols-3 gap-2">
                      <label className="space-y-1 text-xs text-gray-600 dark:text-gray-300">
                        <span>Quantidade</span>
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={item.quantidade}
                          onChange={(event) => updateItem(index, 'quantidade', event.target.value)}
                          placeholder="Qtd"
                          className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </label>
                      <label className="space-y-1 text-xs text-gray-600 dark:text-gray-300">
                        <span>Preço Unitário (R$)</span>
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={item.preco_unitario}
                          onChange={(event) => updateItem(index, 'preco_unitario', event.target.value)}
                          placeholder="Preço unitário"
                          className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </label>
                      <label className="space-y-1 text-xs text-gray-600 dark:text-gray-300">
                        <span>Desconto (%)</span>
                        <input
                          type="number"
                          min="0"
                          max="100"
                          step="0.01"
                          value={item.desconto}
                          onChange={(event) => updateItem(index, 'desconto', event.target.value)}
                          placeholder="Desc.%"
                          className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </label>
                    </div>
                  </div>
                ))}
              </section>

              <div className="rounded-lg bg-gray-50 dark:bg-gray-700 px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                Total estimado: <span className="font-semibold text-emerald-600">{moneyFormatter.format(totalPreview)}</span>
              </div>

              {formError && <p className="text-sm font-medium text-rose-600 dark:text-rose-400">{formError}</p>}

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700"
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
