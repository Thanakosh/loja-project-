import { useState, useEffect, useCallback } from 'react'
import api from '../services/api'

interface VendaItem {
    id: number
    nome_produto: string
    quantidade: number
    preco_unitario: number
    preco_total: number
    unidade?: string
    desconto?: number
}

interface Venda {
    id: number
    numero_legado: number
    data: string
    total: number
    desconto: number
    forma_pagamento: number
    cancelada: boolean
    observacao?: string
    cliente_id?: number
    itens: VendaItem[]
}

const PAYMENT_LABELS: Record<number, string> = {
    1: 'Dinheiro',
    2: 'Débito',
    3: 'Crédito',
    4: 'PIX',
    5: 'Boleto',
    6: 'A Prazo',
}

const LIMIT = 10

const Vendas = () => {
    const [vendas, setVendas] = useState<Venda[]>([])
    const [loading, setLoading] = useState(true)
    const [startDate, setStartDate] = useState('')
    const [endDate, setEndDate] = useState('')
    const [appliedStartDate, setAppliedStartDate] = useState('')
    const [appliedEndDate, setAppliedEndDate] = useState('')
    const [selectedVenda, setSelectedVenda] = useState<Venda | null>(null)
    const [modalLoading, setModalLoading] = useState(false)
    const [skip, setSkip] = useState(0)
    const [hasNextPage, setHasNextPage] = useState(false)

    const fetchVendas = useCallback(async (currentSkip: number, currentStartDate: string, currentEndDate: string) => {
        setLoading(true)
        try {
            const params: Record<string, string | number> = { limit: LIMIT, skip: currentSkip }
            if (currentStartDate) params.start_date = currentStartDate
            if (currentEndDate) params.end_date = currentEndDate

            const response = await api.get('/vendas', { params })
            setVendas(response.data)
            setHasNextPage(response.data.length === LIMIT)
        } catch (error) {
            console.error('Erro ao buscar vendas', error)
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchVendas(skip, appliedStartDate, appliedEndDate)
    }, [appliedEndDate, appliedStartDate, fetchVendas, skip])

    const handleFilter = (e: React.FormEvent) => {
        e.preventDefault()
        setAppliedStartDate(startDate)
        setAppliedEndDate(endDate)
        setSkip(0)
    }

    const handleOpenDetails = async (vendaId: number) => {
        setModalLoading(true)
        try {
            const response = await api.get(`/vendas/${vendaId}`)
            setSelectedVenda(response.data)
        } catch (error) {
            console.error('Erro ao carregar detalhes da venda', error)
        } finally {
            setModalLoading(false)
        }
    }

    const handleCancelVenda = async () => {
        if (!selectedVenda || selectedVenda.cancelada) {
            return
        }

        if (!window.confirm(`Tem certeza que deseja cancelar a venda #${selectedVenda.numero_legado}?`)) {
            return
        }

        try {
            await api.post(`/pdv/venda/${selectedVenda.id}/cancelar`)
            setSelectedVenda(null)
            fetchVendas(skip, appliedStartDate, appliedEndDate)
        } catch (error) {
            console.error('Erro ao cancelar venda', error)
            window.alert('Não foi possível cancelar a venda. Tente novamente.')
        }
    }

    return (
        <div className="container mx-auto">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Histórico de Vendas</h1>
                <form onSubmit={handleFilter} className="flex gap-2 items-end">
                    <div>
                        <label className="block text-xs text-gray-500 dark:text-gray-400">De</label>
                        <input
                            type="date"
                            className="px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="block text-xs text-gray-500 dark:text-gray-400">Até</label>
                        <input
                            type="date"
                            className="px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                        />
                    </div>
                    <button
                        type="submit"
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                    >
                        Filtrar
                    </button>
                </form>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Data</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Número</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Pagamento</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Status</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Total</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Itens</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Ações</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                        {loading ? (
                            <tr>
                                <td colSpan={7} className="px-6 py-4 text-center text-gray-800 dark:text-gray-100">Carregando...</td>
                            </tr>
                        ) : vendas.length === 0 ? (
                            <tr>
                                <td colSpan={7} className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">Nenhuma venda encontrada no período.</td>
                            </tr>
                        ) : (
                            vendas.map((venda) => (
                                <tr key={venda.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">{new Date(venda.data).toLocaleDateString()}</td>
                                    <td className="px-6 py-4 text-sm text-gray-500">{venda.numero_legado}</td>
                                    <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-300">{PAYMENT_LABELS[venda.forma_pagamento] ?? 'Não informado'}</td>
                                    <td className="px-6 py-4 text-sm">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${venda.cancelada ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300' : 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'}`}>
                                            {venda.cancelada ? 'Cancelada' : 'Ativa'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm font-medium text-green-600">
                                        {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(venda.total)}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-300">{venda.itens.length} itens</td>
                                    <td
                                        className="px-6 py-4 text-sm text-blue-600 cursor-pointer hover:underline"
                                        onClick={() => handleOpenDetails(venda.id)}
                                    >
                                        Ver Detalhes
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            <div className="mt-4 flex items-center justify-between">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                    Exibindo {vendas.length} registro(s) na página {Math.floor(skip / LIMIT) + 1}
                </p>
                <div className="flex gap-2">
                    <button
                        type="button"
                        className="px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100 disabled:opacity-50"
                        onClick={() => setSkip((prev) => Math.max(prev - LIMIT, 0))}
                        disabled={loading || skip === 0}
                    >
                        Anterior
                    </button>
                    <button
                        type="button"
                        className="px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100 disabled:opacity-50"
                        onClick={() => setSkip((prev) => prev + LIMIT)}
                        disabled={loading || !hasNextPage}
                    >
                        Próxima
                    </button>
                </div>
            </div>

            {/* Modal de Detalhes da Venda */}
            {selectedVenda && (
                <div className="fixed inset-0 bg-black/50 flex justify-center items-center z-50">
                    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 w-11/12 max-w-2xl max-h-[90vh] overflow-y-auto">
                        <div className="flex justify-between items-center mb-6 border-b pb-3">
                            <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100">
                                Detalhes da Venda {selectedVenda.numero_legado ? `#${selectedVenda.numero_legado}` : `(ID: ${selectedVenda.id})`}
                            </h2>
                            <button onClick={() => setSelectedVenda(null)} className="text-gray-500 hover:text-gray-700 dark:text-gray-300">
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <div className="mb-6 grid grid-cols-2 gap-4">
                            <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded">
                                <p className="text-xs text-gray-500 uppercase tracking-wide">Data da Venda</p>
                                <p className="font-medium text-gray-900 dark:text-gray-100">{new Date(selectedVenda.data).toLocaleString()}</p>
                            </div>
                            <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded">
                                <p className="text-xs text-gray-500 uppercase tracking-wide">Total</p>
                                <p className="font-medium text-green-600 text-lg">{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(selectedVenda.total)}</p>
                            </div>
                            <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded">
                                <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Forma de Pagamento</p>
                                <p className="font-medium text-gray-900 dark:text-gray-100">{PAYMENT_LABELS[selectedVenda.forma_pagamento] ?? 'Não informado'}</p>
                            </div>
                            <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded">
                                <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Status</p>
                                <p className={`font-medium ${selectedVenda.cancelada ? 'text-red-600 dark:text-red-300' : 'text-green-600 dark:text-green-300'}`}>
                                    {selectedVenda.cancelada ? 'Cancelada' : 'Ativa'}
                                </p>
                            </div>
                            {selectedVenda.desconto > 0 && (
                                <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded">
                                    <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Desconto</p>
                                    <p className="font-medium text-gray-900 dark:text-gray-100">
                                        {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(selectedVenda.desconto)}
                                    </p>
                                </div>
                            )}
                            {selectedVenda.observacao && (
                                <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded md:col-span-2">
                                    <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Observação</p>
                                    <p className="font-medium text-gray-900 dark:text-gray-100">{selectedVenda.observacao}</p>
                                </div>
                            )}
                        </div>

                        <h3 className="font-semibold text-gray-800 dark:text-gray-100 mb-3">Itens da Venda</h3>
                        <div className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
                            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                                <thead className="bg-gray-50 dark:bg-gray-700">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Produto</th>
                                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Qtd</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Preço Un.</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Subtotal</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                    {selectedVenda.itens && selectedVenda.itens.length > 0 ? (
                                        selectedVenda.itens.map((item, idx) => (
                                            <tr key={item.id || idx} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                                                <td className="px-4 py-3 text-sm text-gray-900">{item.nome_produto}</td>
                                                <td className="px-4 py-3 text-sm text-gray-500 text-center">{item.quantidade}</td>
                                                <td className="px-4 py-3 text-sm text-gray-500 text-right">{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.preco_unitario)}</td>
                                                <td className="px-4 py-3 text-sm text-gray-900 font-medium text-right">{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.preco_total)}</td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan={4} className="px-4 py-6 text-sm text-center text-gray-500 dark:text-gray-400">Nenhum item registrado nesta venda.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>

                        <div className="mt-6 flex justify-between">
                            {!selectedVenda.cancelada && (
                                <button
                                    onClick={handleCancelVenda}
                                    className="px-6 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition"
                                >
                                    Cancelar Venda
                                </button>
                            )}
                            <button
                                onClick={() => setSelectedVenda(null)}
                                className="px-6 py-2 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100 font-medium rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition"
                            >
                                Fechar
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {modalLoading && (
                <div className="fixed inset-0 bg-black/40 z-40 flex items-center justify-center">
                    <div className="px-4 py-2 rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100">Carregando detalhes...</div>
                </div>
            )}
        </div>
    )
}

export default Vendas
