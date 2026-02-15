import { useState, useEffect } from 'react'
import api from '../services/api'

interface Produto {
  id: number
  nome: string
  codigo_barras: string
  preco_unitario: number
  unidade: string
  estoque_atual?: number // Assuming the API returns this
}

interface Movimentacao {
  id: number
  data: string
  tipo: string
  entrada: number
  saida: number
  saldo_final: number
  historico: string
}

const PAGE_SIZE = 50

const Estoque = () => {
  const [produtos, setProdutos] = useState<Produto[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [selectedProduto, setSelectedProduto] = useState<Produto | null>(null)
  const [movimentacoes, setMovimentacoes] = useState<Movimentacao[]>([])
  const [loadingMov, setLoadingMov] = useState(false)

  const fetchProdutos = async (newPage = 1) => {
    setLoading(true)
    try {
      const response = await api.get('/produtos', { params: { page: newPage, page_size: PAGE_SIZE, incluir_inativos: true } })
      const data = response.data
      setProdutos(data.items ?? data)
      if (data.pages) setTotalPages(data.pages)
    } catch (error) {
      console.error('Erro ao buscar produtos', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchKardex = async (produtoId: number) => {
    setLoadingMov(true)
    try {
      const response = await api.get(`/movimentacao/produto/${produtoId}`)
      setMovimentacoes(response.data)
    } catch (error) {
      console.error('Erro ao buscar kardex', error)
    } finally {
      setLoadingMov(false)
    }
  }

  useEffect(() => {
    fetchProdutos(page)
  }, [page])

  const handleOpenKardex = (produto: Produto) => {
    setSelectedProduto(produto)
    fetchKardex(produto.id)
  }

  return (
    <div className="container mx-auto relative">
      <h1 className="text-2xl font-semibold text-gray-800 mb-6">Estoque</h1>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Produto</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Código</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unidade</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Saldo Atual</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr><td colSpan={5} className="px-6 py-4 text-center">Carregando...</td></tr>
            ) : (
              produtos.map((produto) => (
                <tr key={produto.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{produto.nome}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{produto.codigo_barras || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{produto.unidade}</td>
                  <td className="px-6 py-4 text-sm font-bold text-blue-600">{produto.estoque_atual ?? 'N/A'}</td>
                  <td className="px-6 py-4 text-sm">
                    <button
                      onClick={() => handleOpenKardex(produto)}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Ver Kardex
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Paginação */}
      <div className="flex items-center justify-between mt-4">
        <span className="text-sm text-gray-500">
          Página {page} de {totalPages} — mostrando {produtos.length} registros
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(p => p - 1)}
            disabled={page === 1 || loading}
            className="px-3 py-1 rounded border text-sm disabled:opacity-40 hover:bg-gray-50"
          >
            ← Anterior
          </button>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={page >= totalPages || loading}
            className="px-3 py-1 rounded border text-sm disabled:opacity-40 hover:bg-gray-50"
          >
            Próxima →
          </button>
        </div>
      </div>

      {/* Modal Kardex */}
      {selectedProduto && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-xl font-bold text-gray-800">
                Kardex: {selectedProduto.nome}
              </h2>
              <button
                onClick={() => setSelectedProduto(null)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ×
              </button>
            </div>

            <div className="p-6 overflow-y-auto flex-1">
              {loadingMov ? (
                <p className="text-center">Carregando movimentações...</p>
              ) : movimentacoes.length === 0 ? (
                <p className="text-center text-gray-500">Nenhuma movimentação encontrada.</p>
              ) : (
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Data</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Histórico</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-green-600 uppercase">Entrada</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-red-600 uppercase">Saída</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-blue-600 uppercase">Saldo</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {movimentacoes.map((mov) => (
                      <tr key={mov.id}>
                        <td className="px-4 py-2 text-sm text-gray-600">{new Date(mov.data).toLocaleDateString()}</td>
                        <td className="px-4 py-2 text-sm text-gray-600">{mov.historico}</td>
                        <td className="px-4 py-2 text-sm text-right text-green-600 font-medium">
                          {mov.entrada > 0 ? `+${mov.entrada}` : '-'}
                        </td>
                        <td className="px-4 py-2 text-sm text-right text-red-600 font-medium">
                          {mov.saida > 0 ? `-${mov.saida}` : '-'}
                        </td>
                        <td className="px-4 py-2 text-sm text-right font-bold text-gray-800">
                          {mov.saldo_final}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="p-4 border-t border-gray-200 bg-gray-50 text-right">
              <button
                onClick={() => setSelectedProduto(null)}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition"
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

export default Estoque
