import { useState, useEffect, useCallback } from 'react'
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

    const fetchVendas = useCallback(async () => {
        setLoading(true)
        try {
            const params: Record<string, unknown> = { limit: 50 };
            if (startDate) params.start_date = startDate;
            if (endDate) params.end_date = endDate;

            const response = await api.get('/vendas', { params })
            setVendas(response.data)
        } catch (error) {
            console.error('Erro ao buscar vendas', error)
        } finally {
            setLoading(false)
        }
    }, [startDate, endDate])

    useEffect(() => {
        fetchVendas()
    }, [fetchVendas])

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
                                    <td className="px-6 py-4 text-sm text-blue-600 cursor-pointer hover:underline">
                                        Ver Detalhes
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

export default Vendas
