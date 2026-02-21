import { useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import api from '../services/api'
import OrcamentoModal from '../components/orcamentos/OrcamentoModal'
import ConverterOrcamentoModal from '../components/orcamentos/ConverterOrcamentoModal'

interface OrcamentoItem {
  produto_id: number | null
  descricao: string
  quantidade: number
  preco_unitario: number
  desconto: number
  preco_total: number
}

interface Orcamento {
  id: number
  cliente_id: number | null
  cliente_nome: string | null
  desconto_geral: number
  observacao: string | null
  data_validade: string | null
  status: number
  data_criacao: string
  venda_id: number | null
  criado_por: number | null
  total: number
  itens: OrcamentoItem[]
}

const PAGE_SIZE = 50

const statusLabels: Record<number, { text: string; color: string }> = {
  1: { text: 'Aberto', color: 'bg-indigo-100 text-indigo-700' },
  2: { text: 'Aprovado', color: 'bg-emerald-100 text-emerald-700' },
  3: { text: 'Convertido', color: 'bg-blue-100 text-blue-700' },
  4: { text: 'Cancelado', color: 'bg-rose-100 text-rose-700' }
}

const moneyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL'
})

const Orcamentos = () => {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(0)
  const [filterStatus, setFilterStatus] = useState<number | ''>('')

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingOrcamento, setEditingOrcamento] = useState<Orcamento | null>(null)

  const [isConverterOpen, setIsConverterOpen] = useState(false)
  const [convertingOrcamento, setConvertingOrcamento] = useState<Orcamento | null>(null)

  const cancelMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/orcamento/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orcamentos'] })
    }
  })

  const orcamentosQuery = useQuery({
    queryKey: ['orcamentos', page, filterStatus],
    queryFn: async () => {
      const response = await api.get('/orcamento/', {
        params: {
          page: page + 1,
          page_size: PAGE_SIZE,
          status: filterStatus || undefined
        }
      })
      return (response.data?.items ?? response.data) as Orcamento[] // Suporte caso o backend retorne direto ou paginado com items
    },
    placeholderData: (previousData) => previousData
  })

  // Dependendo de paginação vs array direto do backend
  const orcamentos = Array.isArray(orcamentosQuery.data)
    ? orcamentosQuery.data
    : ((orcamentosQuery.data as unknown) as { items?: Orcamento[] })?.items ?? []

  // Estimar total (simplificado se backend não envia total de pgs ou limit/offset diferente)
  const totalEstimado = useMemo(() => {
    if (orcamentos.length < PAGE_SIZE) {
      return page * PAGE_SIZE + orcamentos.length
    }
    return (page + 2) * PAGE_SIZE
  }, [orcamentos.length, page])

  const totalPages = Math.max(1, Math.ceil(totalEstimado / PAGE_SIZE))

  const handleFilterSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setPage(0)
  }

  const openCreateModal = () => {
    setEditingOrcamento(null)
    setIsModalOpen(true)
  }

  const openEditModal = (orcamento: Orcamento) => {
    setEditingOrcamento(orcamento)
    setIsModalOpen(true)
  }

  function closeModal() {
    setIsModalOpen(false)
    setEditingOrcamento(null)
  }

  const openConverterModal = (orcamento: Orcamento) => {
    setConvertingOrcamento(orcamento)
    setIsConverterOpen(true)
  }

  const handleCancelClick = (id: number) => {
    if (confirm('Tem certeza que deseja cancelar este orçamento? A ação não pode ser desfeita.')) {
      cancelMutation.mutate(id)
    }
  }

  const getStatusBadge = (statusId: number) => {
    const status = statusLabels[statusId] || { text: 'Desconhecido', color: 'bg-gray-100 text-gray-700' }
    return (
      <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${status.color}`}>
        {status.text}
      </span>
    )
  }

  return (
    <div className="container mx-auto">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-800">Orçamentos</h1>
          <p className="text-sm text-gray-500">Gerencie orçamentos e conversões para vendas.</p>
        </div>

        <div className="flex flex-wrap gap-2">
          <form onSubmit={handleFilterSubmit} className="flex gap-2">
            <select
              value={filterStatus}
              onChange={(event) => {
                setFilterStatus(event.target.value ? Number(event.target.value) : '')
                setPage(0)
              }}
              className="rounded-lg border px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos os status</option>
              {Object.entries(statusLabels).map(([val, label]) => (
                <option key={val} value={val}>{label.text}</option>
              ))}
            </select>
          </form>

          <button
            type="button"
            onClick={openCreateModal}
            className="rounded-lg bg-emerald-600 px-4 py-2 font-medium text-white transition hover:bg-emerald-700"
          >
            + Novo Orçamento
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg bg-white shadow">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">ID / Data</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Cliente</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Validade</th>
              <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Total</th>
              <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">Status</th>
              <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {orcamentosQuery.isLoading ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center">Carregando...</td>
              </tr>
            ) : orcamentosQuery.isError ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-red-600">Erro ao carregar orçamentos.</td>
              </tr>
            ) : orcamentos.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">Nenhum orçamento encontrado.</td>
              </tr>
            ) : (
              orcamentos.map((orcamento) => (
                <tr key={orcamento.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">#{orcamento.id}</div>
                    <div className="text-xs text-gray-500">
                      {new Date(orcamento.data_criacao).toLocaleDateString('pt-BR')}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">
                      {orcamento.cliente_nome ?? 'Sem nome'}
                    </div>
                    {orcamento.cliente_id && (
                      <div className="text-xs text-gray-500">Cód: {orcamento.cliente_id}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {orcamento.data_validade
                      ? new Date(orcamento.data_validade + 'T12:00:00Z').toLocaleDateString('pt-BR')
                      : '-'}
                  </td>
                  <td className="px-6 py-4 text-right text-sm font-medium text-gray-900">
                    {moneyFormatter.format(orcamento.total)}
                  </td>
                  <td className="px-6 py-4 text-center">
                    {getStatusBadge(orcamento.status)}
                  </td>
                  <td className="px-6 py-4 text-right text-sm">
                    <button
                      type="button"
                      onClick={() => openEditModal(orcamento)}
                      className="rounded border border-gray-300 px-3 py-1 text-gray-700 transition hover:bg-gray-100"
                    >
                      {orcamento.status === 1 ? 'Editar' : 'Detalhes'}
                    </button>
                    {(orcamento.status === 1 || orcamento.status === 2) && (
                      <button
                        type="button"
                        onClick={() => openConverterModal(orcamento)}
                        className="ml-2 rounded border border-blue-200 bg-blue-50 px-3 py-1 text-blue-700 transition hover:bg-blue-100 hover:border-blue-300 font-medium"
                      >
                        Converter em Venda
                      </button>
                    )}
                    {orcamento.status === 1 && (
                      <button
                        type="button"
                        onClick={() => handleCancelClick(orcamento.id)}
                        disabled={cancelMutation.isPending}
                        className="ml-2 rounded border border-rose-200 px-3 py-1 text-rose-700 transition hover:bg-rose-50"
                      >
                        Cancelar
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <span className="text-sm text-gray-500">
          Página {page + 1} de {totalPages} — mostrando {orcamentos.length} registros nesta página
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage((previous) => Math.max(0, previous - 1))}
            disabled={page === 0 || orcamentosQuery.isFetching}
            className="rounded border px-3 py-1 text-sm hover:bg-gray-50 disabled:opacity-40"
          >
            ← Anterior
          </button>
          <button
            onClick={() => setPage((previous) => previous + 1)}
            disabled={orcamentos.length < PAGE_SIZE || orcamentosQuery.isFetching}
            className="rounded border px-3 py-1 text-sm hover:bg-gray-50 disabled:opacity-40"
          >
            Próxima →
          </button>
        </div>
      </div>

      {isModalOpen && (
        <OrcamentoModal
          isOpen={isModalOpen}
          onClose={closeModal}
          orcamentoToEdit={editingOrcamento}
        />
      )}

      {isConverterOpen && (
        <ConverterOrcamentoModal
          isOpen={isConverterOpen}
          onClose={() => {
            setIsConverterOpen(false)
            setConvertingOrcamento(null)
          }}
          orcamento={convertingOrcamento}
        />
      )}
    </div>
  )
}

export default Orcamentos
