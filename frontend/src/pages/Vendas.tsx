import { useState, useEffect } from 'react'
import api from '../services/api'

interface VendaItem {
    id: number
    nome_produto: string
    quantidade: number
    preco_unitario: number
    preco_total: number
}

interface Venda {
    id: number
    numero_legado: number
    data: string
    total: number
    cliente_id: number
    itens: VendaItem[]
}

const Vendas = () => {
    const [vendas, setVendas] = useState<Venda[]>([])
    const [loading, setLoading] = useState(true)
    const [startDate, setStartDate] = useState('')
    const [endDate, setEndDate] = useState('')
    const [selectedVenda, setSelectedVenda] = useState<Venda | null>(null)

    const fetchVendas = async () => {
        setLoading(true)
        try {
            const params: any = { limit: 50 };
            if (startDate) params.start_date = startDate;
            if (endDate) params.end_date = endDate;

            const response = await api.get('/vendas', { params })
            setVendas(response.data)
        } catch (error) {
            console.error('Erro ao buscar vendas', error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchVendas()
    }, [])

    const handleFilter = (e: React.FormEvent) => {
        e.preventDefault()
        fetchVendas()
    }

    return (
        <div className="container mx-auto">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-semibold text-gray-800">Histórico de Vendas</h1>
                <form onSubmit={handleFilter} className="flex gap-2 items-end">
                    <div>
                        <label className="block text-xs text-gray-500">De</label>
                        <input
                            type="date"
                            className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="block text-xs text-gray-500">Até</label>
                        <input
                            type="date"
                            className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
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

            <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Número</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Itens</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {loading ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-4 text-center">Carregando...</td>
                            </tr>
                        ) : vendas.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">Nenhuma venda encontrada no período.</td>
                            </tr>
                        ) : (
                            vendas.map((venda) => (
                                <tr key={venda.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 text-sm text-gray-900">{new Date(venda.data).toLocaleDateString()}</td>
                                    <td className="px-6 py-4 text-sm text-gray-500">{venda.numero_legado}</td>
                                    <td className="px-6 py-4 text-sm font-medium text-green-600">
                                        {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(venda.total)}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500">{venda.itens.length} itens</td>
                                    <td
                                        className="px-6 py-4 text-sm text-blue-600 cursor-pointer hover:underline"
                                        onClick={() => setSelectedVenda(venda)}
                                    >
                                        Ver Detalhes
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Modal de Detalhes da Venda */}
            {selectedVenda && (
                <div className="fixed inset-0 bg-black/50 flex justify-center items-center z-50">
                    <div className="bg-white rounded-lg p-6 w-11/12 max-w-2xl max-h-[90vh] overflow-y-auto">
                        <div className="flex justify-between items-center mb-6 border-b pb-3">
                            <h2 className="text-xl font-semibold text-gray-800">
                                Detalhes da Venda {selectedVenda.numero_legado ? `#${selectedVenda.numero_legado}` : `(ID: ${selectedVenda.id})`}
                            </h2>
                            <button onClick={() => setSelectedVenda(null)} className="text-gray-500 hover:text-gray-700">
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <div className="mb-6 grid grid-cols-2 gap-4">
                            <div className="bg-gray-50 p-3 rounded">
                                <p className="text-xs text-gray-500 uppercase tracking-wide">Data da Venda</p>
                                <p className="font-medium text-gray-900">{new Date(selectedVenda.data).toLocaleString()}</p>
                            </div>
                            <div className="bg-gray-50 p-3 rounded">
                                <p className="text-xs text-gray-500 uppercase tracking-wide">Total</p>
                                <p className="font-medium text-green-600 text-lg">{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(selectedVenda.total)}</p>
                            </div>
                        </div>

                        <h3 className="font-semibold text-gray-800 mb-3">Itens da Venda</h3>
                        <div className="bg-white border rounded-lg overflow-hidden">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Produto</th>
                                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Qtd</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Preço Un.</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Subtotal</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200">
                                    {selectedVenda.itens && selectedVenda.itens.length > 0 ? (
                                        selectedVenda.itens.map((item, idx) => (
                                            <tr key={item.id || idx} className="hover:bg-gray-50">
                                                <td className="px-4 py-3 text-sm text-gray-900">{item.nome_produto}</td>
                                                <td className="px-4 py-3 text-sm text-gray-500 text-center">{item.quantidade}</td>
                                                <td className="px-4 py-3 text-sm text-gray-500 text-right">{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.preco_unitario)}</td>
                                                <td className="px-4 py-3 text-sm text-gray-900 font-medium text-right">{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.preco_total)}</td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan={4} className="px-4 py-6 text-sm text-center text-gray-500">Nenhum item registrado nesta venda.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>

                        <div className="mt-6 flex justify-end">
                            <button
                                onClick={() => setSelectedVenda(null)}
                                className="px-6 py-2 bg-gray-100 text-gray-800 font-medium rounded-lg hover:bg-gray-200 transition"
                            >
                                Fechar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default Vendas
