import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import api from '../services/api'

interface ContaReceber {
    id: number
    cliente_id?: number
    documento: number
    parcela: number
    data_emissao?: string
    data_vencimento?: string
    data_pagamento?: string
    valor: number
    valor_pago: number
    desconto: number
    juros: number
    historico?: string
    em_aberto: boolean
}


interface ContaReceberResumo {
    total_em_aberto: number
    total_vencido: number
    quantidade_em_aberto: number
}

interface ContaReceberListResponse {
    items: ContaReceber[]
    total: number
    page: number
    page_size: number
    pages: number
}

export default function ContasReceber() {
    const queryClient = useQueryClient()
    const [page, setPage] = useState(1)
    const [pageSize] = useState(50)
    const [apenasEmAberto, setApenasEmAberto] = useState(false)
    const [vencidas, setVencidas] = useState(false)
    const [clienteId, setClienteId] = useState('')

    // Filters to send to API
    const [activeFilters, setActiveFilters] = useState({
        apenasEmAberto: false,
        vencidas: false,
        clienteId: '',
    })

    // Modal State
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [selectedConta, setSelectedConta] = useState<ContaReceber | null>(null)
    const [formData, setFormData] = useState({
        data_pagamento: new Date().toISOString().split('T')[0],
        valor_pago: 0,
        desconto: 0,
        juros: 0,
        historico: ''
    })

    const baixaMutation = useMutation({
        mutationFn: async ({ id, data }: { id: number, data: { data_pagamento: string; valor_pago: number; desconto: number; juros: number; historico: string | null } }) => {
            const response = await api.put(`/contas-receber/${id}/baixar`, data)
            return response.data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['contas-receber'] })
            queryClient.invalidateQueries({ queryKey: ['contas-receber-resumo'] })
            setIsModalOpen(false)
            setSelectedConta(null)
            toast.success('Conta baixada com sucesso!')
        },
        onError: (error) => {
            console.error('Erro ao baixar conta:', error)
            toast.error('Ocorreu um erro ao baixar a conta.')
        }
    })

    const openBaixaModal = (conta: ContaReceber) => {
        setSelectedConta(conta)
        setFormData({
            data_pagamento: new Date().toISOString().split('T')[0],
            valor_pago: conta.valor - conta.valor_pago,
            desconto: 0,
            juros: 0,
            historico: ''
        })
        setIsModalOpen(true)
    }

    const handleBaixaSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (!selectedConta) return

        baixaMutation.mutate({
            id: selectedConta.id,
            data: {
                data_pagamento: formData.data_pagamento,
                valor_pago: Number(formData.valor_pago),
                desconto: Number(formData.desconto),
                juros: Number(formData.juros),
                historico: formData.historico || null
            }
        })
    }

    const { data: contasResponse, isLoading, isError } = useQuery<ContaReceberListResponse>({
        queryKey: ['contas-receber', page, pageSize, activeFilters],
        queryFn: async () => {
            const params = new URLSearchParams()
            params.append('page', page.toString())
            params.append('page_size', pageSize.toString())
            if (activeFilters.apenasEmAberto) params.append('apenas_em_aberto', 'true')
            if (activeFilters.vencidas) params.append('vencidas', 'true')
            if (activeFilters.clienteId) params.append('cliente_id', activeFilters.clienteId)

            const response = await api.get(`/contas-receber/?${params.toString()}`)
            return response.data
        },
    })

    const { data: resumo } = useQuery<ContaReceberResumo>({
        queryKey: ['contas-receber-resumo'],
        queryFn: async () => {
            const response = await api.get('/contas-receber/resumo')
            return response.data
        },
    })

    const stats = {
        totalEmAberto: resumo?.total_em_aberto ?? 0,
        totalVencido: resumo?.total_vencido ?? 0,
        qtdEmAberto: resumo?.quantidade_em_aberto ?? 0,
    }

    const contas = contasResponse?.items ?? []

    const handleFilter = () => {
        setPage(1)
        setActiveFilters({
            apenasEmAberto,
            vencidas,
            clienteId,
        })
    }

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
    }

    const formatDate = (dateString?: string) => {
        if (!dateString) return '-'
        const [year, month, day] = dateString.split('-')
        return `${day}/${month}/${year}`
    }

    const getStatusBadge = (conta: ContaReceber) => {
        if (conta.data_pagamento) {
            return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">Pago</span>
        }

        if (conta.em_aberto) {
            if (conta.data_vencimento) {
                const hoje = new Date()
                hoje.setHours(0, 0, 0, 0)
                const ven = new Date(conta.data_vencimento)
                if (ven < hoje) {
                    return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">Vencido</span>
                }
            }
            return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">A vencer</span>
        }

        return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">Resolvido</span>
    }

    return (
        <div className="space-y-6 text-gray-900 dark:text-gray-100">
            <h1 className="text-2xl font-semibold">Contas a Receber</h1>

            {/* Resumo */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow border border-gray-200 dark:border-gray-700">
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total em Aberto</h3>
                    <p className="mt-1 text-2xl font-semibold text-blue-600 dark:text-blue-400">{formatCurrency(stats.totalEmAberto)}</p>
                </div>
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow border border-gray-200 dark:border-gray-700">
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Vencido</h3>
                    <p className="mt-1 text-2xl font-semibold text-red-600 dark:text-red-400">{formatCurrency(stats.totalVencido)}</p>
                </div>
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow border border-gray-200 dark:border-gray-700">
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Qtd em Aberto</h3>
                    <p className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">{stats.qtdEmAberto}</p>
                </div>
            </div>

            {/* Filtros */}
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow border border-gray-200 dark:border-gray-700 flex flex-col sm:flex-row gap-4 items-end">
                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">ID do Cliente</label>
                    <input
                        type="number"
                        className="w-full sm:w-40 border border-gray-300 dark:border-gray-600 rounded-md p-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        placeholder="Ex: 123"
                        value={clienteId}
                        onChange={(e) => setClienteId(e.target.value)}
                    />
                </div>
                <div className="flex items-center space-x-2 h-10">
                    <input
                        type="checkbox"
                        id="apenasEmAberto"
                        className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                        checked={apenasEmAberto}
                        onChange={(e) => setApenasEmAberto(e.target.checked)}
                    />
                    <label htmlFor="apenasEmAberto" className="text-sm">Apenas em aberto</label>
                </div>
                <div className="flex items-center space-x-2 h-10">
                    <input
                        type="checkbox"
                        id="vencidas"
                        className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                        checked={vencidas}
                        onChange={(e) => setVencidas(e.target.checked)}
                    />
                    <label htmlFor="vencidas" className="text-sm">Apenas vencidas</label>
                </div>
                <div className="sm:ml-auto">
                    <button
                        onClick={handleFilter}
                        className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md font-medium transition-colors"
                    >
                        Filtrar
                    </button>
                </div>
            </div>

            {/* Tabela */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg border border-gray-200 dark:border-gray-700 overflow-x-auto">
                {isLoading ? (
                    <div className="p-4 text-center">Carregando contas...</div>
                ) : isError ? (
                    <div className="p-4 text-center text-red-500">Erro ao carregar contas a receber.</div>
                ) : contas.length === 0 ? (
                    <div className="p-4 text-center text-gray-500 dark:text-gray-400">Nenhuma conta encontrada.</div>
                ) : (
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead className="bg-gray-50 dark:bg-gray-700">
                            <tr>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Doc/Parcela</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Cliente (ID)</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Emissão</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Vencimento</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Valor</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Paga</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Status</th>
                                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Ações</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                            {(contasResponse?.items ?? []).map((conta) => (
                                <tr key={conta.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        {conta.documento} / {conta.parcela}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                        {conta.cliente_id || '-'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                        {formatDate(conta.data_emissao)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                        {formatDate(conta.data_vencimento)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                                        {formatCurrency(conta.valor)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 dark:text-green-400 font-medium">
                                        {formatCurrency(conta.valor_pago)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        {getStatusBadge(conta)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        {conta.em_aberto && (
                                            <button
                                                onClick={() => openBaixaModal(conta)}
                                                className="text-white bg-emerald-600 hover:bg-emerald-700 px-3 py-1 rounded shadow-sm transition-colors text-xs"
                                            >
                                                Baixar
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Paginação */}
            <div className="flex justify-between items-center bg-white dark:bg-gray-800 p-4 rounded-lg shadow border border-gray-200 dark:border-gray-700">
                <button
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-gray-700 dark:text-gray-200 transition-colors"
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                >
                    Anterior
                </button>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                    Mostrando página {contasResponse?.page ?? page} de {contasResponse?.pages ?? 1}
                </span>
                <button
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-gray-700 dark:text-gray-200 transition-colors"
                    onClick={() => setPage(page + 1)}
                    disabled={!contasResponse || page >= contasResponse.pages}
                >
                    Próxima
                </button>
            </div>

            {/* Modal Baixar Conta */}
            {isModalOpen && selectedConta && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
                    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4">
                        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                                Baixar Conta: Doc {selectedConta.documento} / Parc {selectedConta.parcela}
                            </h2>
                            <button
                                onClick={() => setIsModalOpen(false)}
                                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 text-xl font-bold"
                            >
                                &times;
                            </button>
                        </div>

                        <form onSubmit={handleBaixaSubmit} className="p-4 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data Pagamento</label>
                                <input
                                    type="date"
                                    required
                                    className="w-full border border-gray-300 dark:border-gray-600 rounded-md p-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                    value={formData.data_pagamento}
                                    onChange={e => setFormData({ ...formData, data_pagamento: e.target.value })}
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Valor Pago</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        min="0"
                                        required
                                        className="w-full border border-gray-300 dark:border-gray-600 rounded-md p-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                        value={formData.valor_pago}
                                        onChange={e => setFormData({ ...formData, valor_pago: Number(e.target.value) })}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Desconto</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        min="0"
                                        className="w-full border border-gray-300 dark:border-gray-600 rounded-md p-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                        value={formData.desconto}
                                        onChange={e => setFormData({ ...formData, desconto: Number(e.target.value) })}
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Juros</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        min="0"
                                        className="w-full border border-gray-300 dark:border-gray-600 rounded-md p-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                        value={formData.juros}
                                        onChange={e => setFormData({ ...formData, juros: Number(e.target.value) })}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Histórico</label>
                                    <input
                                        type="text"
                                        className="w-full border border-gray-300 dark:border-gray-600 rounded-md p-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                        placeholder="Opcional"
                                        value={formData.historico}
                                        onChange={e => setFormData({ ...formData, historico: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    disabled={baixaMutation.isPending}
                                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-sm font-medium disabled:opacity-50"
                                >
                                    {baixaMutation.isPending ? 'Salvando...' : 'Confirmar Baixa'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

        </div>
    )
}
