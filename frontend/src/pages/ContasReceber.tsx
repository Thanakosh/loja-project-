import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import api from '../services/api'
import type {
    BaixaContaReceberPayload,
    ContaReceber,
    ContaReceberListResponse,
    ContaReceberResumo,
} from '../types/contasReceber'

export default function ContasReceber() {
    const queryClient = useQueryClient()
    const [page, setPage] = useState(1)
    const [pageSize] = useState(50)
    const [apenasEmAberto, setApenasEmAberto] = useState(false)
    const [vencidas, setVencidas] = useState(false)
    const [clienteId, setClienteId] = useState('')
    const [clienteNome, setClienteNome] = useState('')
    const [activeFilters, setActiveFilters] = useState({
        apenasEmAberto: false,
        vencidas: false,
        clienteId: '',
        clienteNome: '',
    })
    const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false)
    const [isBaixaModalOpen, setIsBaixaModalOpen] = useState(false)
    const [selectedConta, setSelectedConta] = useState<ContaReceber | null>(null)
    const [formData, setFormData] = useState({
        data_pagamento: new Date().toISOString().split('T')[0],
        valor_pago: 0,
        desconto: 0,
        juros: 0,
        historico: '',
    })

    const closeModals = () => {
        setIsDetailsModalOpen(false)
        setIsBaixaModalOpen(false)
        setSelectedConta(null)
    }

    const baixaMutation = useMutation({
        mutationFn: async ({ id, data }: { id: number; data: BaixaContaReceberPayload }) => {
            const response = await api.put(`/contas-receber/${id}/baixar`, data)
            return response.data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['contas-receber'] })
            queryClient.invalidateQueries({ queryKey: ['contas-receber-resumo'] })
            closeModals()
            toast.success('Conta baixada com sucesso!')
        },
        onError: (error) => {
            console.error('Erro ao baixar conta:', error)
            toast.error('Ocorreu um erro ao baixar a conta.')
        },
    })

    const openDetailsModal = (conta: ContaReceber) => {
        setSelectedConta(conta)
        setIsDetailsModalOpen(true)
        setIsBaixaModalOpen(false)
    }

    const openBaixaModal = (conta: ContaReceber) => {
        setSelectedConta(conta)
        setIsDetailsModalOpen(false)
        setFormData({
            data_pagamento: new Date().toISOString().split('T')[0],
            valor_pago: conta.saldo_em_aberto,
            desconto: 0,
            juros: 0,
            historico: '',
        })
        setIsBaixaModalOpen(true)
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
                historico: formData.historico || null,
            },
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
            if (activeFilters.clienteNome) params.append('cliente_nome', activeFilters.clienteNome)

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
            clienteNome,
        })
    }

    const formatCurrency = (value: number) =>
        new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)

    const formatDate = (dateString?: string) => {
        if (!dateString) return '-'
        const [year, month, day] = dateString.split('-')
        return `${day}/${month}/${year}`
    }

    const formatParcela = (conta: ContaReceber) => {
        const totalParcelas = conta.total_parcelas && conta.total_parcelas > 0
            ? conta.total_parcelas
            : conta.parcela

        return `${conta.parcela}/${totalParcelas}`
    }

    const formatCliente = (conta: ContaReceber) => {
        if (conta.cliente_nome && conta.cliente_id) {
            return `${conta.cliente_nome} (#${conta.cliente_id})`
        }
        if (conta.cliente_nome) return conta.cliente_nome
        if (conta.cliente_id) return `Cliente #${conta.cliente_id}`
        return '-'
    }

    const getStatusBadge = (conta: ContaReceber) => {
        if (conta.situacao === 'quitada') {
            return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">Quitada</span>
        }

        if (conta.situacao === 'parcial') {
            if (conta.data_vencimento) {
                const hoje = new Date()
                hoje.setHours(0, 0, 0, 0)
                const vencimento = new Date(conta.data_vencimento)
                if (vencimento < hoje) {
                    return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">Parcial vencida</span>
                }
            }
            return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-sky-100 text-sky-800 dark:bg-sky-900 dark:text-sky-200">Parcial</span>
        }

        if (conta.situacao === 'aberta') {
            if (conta.data_vencimento) {
                const hoje = new Date()
                hoje.setHours(0, 0, 0, 0)
                const vencimento = new Date(conta.data_vencimento)
                if (vencimento < hoje) {
                    return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">Vencido</span>
                }
            }
            return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">A vencer</span>
        }

        return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">Indefinido</span>
    }

    return (
        <div className="space-y-6 text-gray-900 dark:text-gray-100">
            <h1 className="text-2xl font-semibold">Contas a Receber</h1>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div className="rounded-lg border border-gray-200 bg-white p-4 shadow dark:border-gray-700 dark:bg-gray-800">
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total em Aberto</h3>
                    <p className="mt-1 text-2xl font-semibold text-blue-600 dark:text-blue-400">{formatCurrency(stats.totalEmAberto)}</p>
                </div>
                <div className="rounded-lg border border-gray-200 bg-white p-4 shadow dark:border-gray-700 dark:bg-gray-800">
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Vencido</h3>
                    <p className="mt-1 text-2xl font-semibold text-red-600 dark:text-red-400">{formatCurrency(stats.totalVencido)}</p>
                </div>
                <div className="rounded-lg border border-gray-200 bg-white p-4 shadow dark:border-gray-700 dark:bg-gray-800">
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Qtd em Aberto</h3>
                    <p className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">{stats.qtdEmAberto}</p>
                </div>
            </div>

            <div className="flex flex-col items-end gap-4 rounded-lg border border-gray-200 bg-white p-4 shadow dark:border-gray-700 dark:bg-gray-800 sm:flex-row">
                <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">ID do Cliente</label>
                    <input
                        type="number"
                        className="w-full rounded-md border border-gray-300 bg-white p-2 text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 sm:w-40"
                        placeholder="Ex: 123"
                        value={clienteId}
                        onChange={(e) => setClienteId(e.target.value)}
                    />
                </div>
                <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Nome do Cliente</label>
                    <input
                        type="text"
                        className="w-full rounded-md border border-gray-300 bg-white p-2 text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 sm:w-56"
                        placeholder="Ex: Maria"
                        value={clienteNome}
                        onChange={(e) => setClienteNome(e.target.value)}
                    />
                </div>
                <div className="flex h-10 items-center space-x-2">
                    <input
                        type="checkbox"
                        id="apenasEmAberto"
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600"
                        checked={apenasEmAberto}
                        onChange={(e) => setApenasEmAberto(e.target.checked)}
                    />
                    <label htmlFor="apenasEmAberto" className="text-sm">Apenas em aberto</label>
                </div>
                <div className="flex h-10 items-center space-x-2">
                    <input
                        type="checkbox"
                        id="vencidas"
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600"
                        checked={vencidas}
                        onChange={(e) => setVencidas(e.target.checked)}
                    />
                    <label htmlFor="vencidas" className="text-sm">Apenas vencidas</label>
                </div>
                <div className="sm:ml-auto">
                    <button
                        onClick={handleFilter}
                        className="rounded-md bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700"
                    >
                        Filtrar
                    </button>
                </div>
            </div>

            <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow dark:border-gray-700 dark:bg-gray-800">
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
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">Documento</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">Parcela</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">Cliente</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">Emissao</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">Vencimento</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">Valor</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">Pago acum.</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">Saldo</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">Status</th>
                                <th scope="col" className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">Acoes</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
                            {contas.map((conta) => (
                                <tr key={conta.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                                    <td className="whitespace-nowrap px-6 py-4 text-sm font-medium">{conta.documento}</td>
                                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{formatParcela(conta)}</td>
                                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{formatCliente(conta)}</td>
                                    <td className="whitespace-nowrap px-6 py-4 text-sm">{formatDate(conta.data_emissao)}</td>
                                    <td className="whitespace-nowrap px-6 py-4 text-sm">{formatDate(conta.data_vencimento)}</td>
                                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 dark:text-gray-100">{formatCurrency(conta.valor)}</td>
                                    <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-green-600 dark:text-green-400">{formatCurrency(conta.valor_pago)}</td>
                                    <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-amber-600 dark:text-amber-400">{formatCurrency(conta.saldo_em_aberto)}</td>
                                    <td className="whitespace-nowrap px-6 py-4">{getStatusBadge(conta)}</td>
                                    <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                                        <button
                                            onClick={() => openDetailsModal(conta)}
                                            className="mr-2 rounded bg-gray-100 px-3 py-1 text-xs text-gray-700 shadow-sm transition-colors hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"
                                        >
                                            Detalhes
                                        </button>
                                        {conta.em_aberto && (
                                            <button
                                                onClick={() => openBaixaModal(conta)}
                                                className="rounded bg-emerald-600 px-3 py-1 text-xs text-white shadow-sm transition-colors hover:bg-emerald-700"
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

            <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4 shadow dark:border-gray-700 dark:bg-gray-800">
                <button
                    className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                >
                    Anterior
                </button>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                    Mostrando pagina {contasResponse?.page ?? page} de {contasResponse?.pages ?? 1}
                </span>
                <button
                    className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
                    onClick={() => setPage(page + 1)}
                    disabled={!contasResponse || page >= contasResponse.pages}
                >
                    Proxima
                </button>
            </div>

            {isDetailsModalOpen && selectedConta && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                    <div className="mx-4 w-full max-w-2xl rounded-lg bg-white shadow-xl dark:bg-gray-800">
                        <div className="flex items-center justify-between border-b border-gray-200 p-4 dark:border-gray-700">
                            <div>
                                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                                    Detalhes da Conta
                                </h2>
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                    Documento {selectedConta.documento} - Parcela {formatParcela(selectedConta)}
                                </p>
                            </div>
                            <button
                                onClick={closeModals}
                                className="text-xl font-bold text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                            >
                                &times;
                            </button>
                        </div>

                        <div className="grid gap-4 p-4 md:grid-cols-2">
                            <div className="space-y-3 rounded-lg border border-gray-200 p-4 dark:border-gray-700">
                                <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Referencia</h3>
                                <div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Cliente</p>
                                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{formatCliente(selectedConta)}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Historico</p>
                                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{selectedConta.historico || 'Sem historico'}</p>
                                </div>
                            </div>

                            <div className="space-y-3 rounded-lg border border-gray-200 p-4 dark:border-gray-700">
                                <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Datas</h3>
                                <div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Emissao</p>
                                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{formatDate(selectedConta.data_emissao)}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Vencimento</p>
                                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{formatDate(selectedConta.data_vencimento)}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Pagamento</p>
                                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{formatDate(selectedConta.data_pagamento)}</p>
                                </div>
                            </div>

                            <div className="space-y-3 rounded-lg border border-gray-200 p-4 dark:border-gray-700">
                                <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Valores</h3>
                                <div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Valor original</p>
                                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{formatCurrency(selectedConta.valor)}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Pago acumulado</p>
                                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{formatCurrency(selectedConta.valor_pago)}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Saldo em aberto</p>
                                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{formatCurrency(selectedConta.saldo_em_aberto)}</p>
                                </div>
                            </div>

                            <div className="space-y-3 rounded-lg border border-gray-200 p-4 dark:border-gray-700">
                                <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Ajustes</h3>
                                <div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Desconto</p>
                                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{formatCurrency(selectedConta.desconto)}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Juros</p>
                                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{formatCurrency(selectedConta.juros)}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Status</p>
                                    <div className="pt-1">{getStatusBadge(selectedConta)}</div>
                                </div>
                            </div>
                        </div>

                        <div className="flex justify-end gap-3 border-t border-gray-200 p-4 dark:border-gray-700">
                            <button
                                type="button"
                                onClick={closeModals}
                                className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
                            >
                                Fechar
                            </button>
                            {selectedConta.em_aberto && (
                                <button
                                    type="button"
                                    onClick={() => openBaixaModal(selectedConta)}
                                    className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
                                >
                                    Baixar conta
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {isBaixaModalOpen && selectedConta && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                    <div className="mx-4 w-full max-w-md rounded-lg bg-white shadow-xl dark:bg-gray-800">
                        <div className="flex items-center justify-between border-b border-gray-200 p-4 dark:border-gray-700">
                            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                                Registrar recebimento: Doc {selectedConta.documento} / Parc {formatParcela(selectedConta)}
                            </h2>
                            <button
                                onClick={closeModals}
                                className="text-xl font-bold text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                            >
                                &times;
                            </button>
                        </div>

                        <form onSubmit={handleBaixaSubmit} className="space-y-4 p-4">
                            <div>
                                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Data Pagamento</label>
                                <input
                                    type="date"
                                    required
                                    className="w-full rounded-md border border-gray-300 bg-white p-2 text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                                    value={formData.data_pagamento}
                                    onChange={(e) => setFormData({ ...formData, data_pagamento: e.target.value })}
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Valor recebido agora</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        min="0"
                                        required
                                        className="w-full rounded-md border border-gray-300 bg-white p-2 text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                                        value={formData.valor_pago}
                                        onChange={(e) => setFormData({ ...formData, valor_pago: Number(e.target.value) })}
                                    />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Desconto</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        min="0"
                                        className="w-full rounded-md border border-gray-300 bg-white p-2 text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                                        value={formData.desconto}
                                        onChange={(e) => setFormData({ ...formData, desconto: Number(e.target.value) })}
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Juros</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        min="0"
                                        className="w-full rounded-md border border-gray-300 bg-white p-2 text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                                        value={formData.juros}
                                        onChange={(e) => setFormData({ ...formData, juros: Number(e.target.value) })}
                                    />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Historico</label>
                                    <input
                                        type="text"
                                        className="w-full rounded-md border border-gray-300 bg-white p-2 text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                                        placeholder="Opcional"
                                        value={formData.historico}
                                        onChange={(e) => setFormData({ ...formData, historico: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 border-t border-gray-200 pt-4 dark:border-gray-700">
                                <button
                                    type="button"
                                    onClick={closeModals}
                                    className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    disabled={baixaMutation.isPending}
                                    className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 hover:bg-emerald-700"
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
