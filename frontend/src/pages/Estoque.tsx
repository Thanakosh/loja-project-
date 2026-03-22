import axios from 'axios'
import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import { useAccessibleModal } from '../hooks/useAccessibleModal'
import { API_BASE_URL } from '../config/api'
import api from '../services/api'
import { getToken } from '../utils/auth'

const apiV2 = axios.create({ baseURL: `${API_BASE_URL}/api/v2` })
apiV2.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

interface Produto {
  id: number
  nome: string
  codigo_barras: string
  preco_unitario: number
  unidade: string
  estoque_atual?: number
}

interface Movimentacao {
  id: number
  produto_id: number
  tipo: 'entrada' | 'saida' | 'ajuste' | 'devolucao'
  quantidade: number
  motivo: string | null
  usuario_id: number | null
  data_transacao: string
}

interface NovaMovimentacao {
  produto_id: number
  tipo: 'entrada' | 'saida' | 'ajuste' | 'devolucao'
  quantidade: number
  motivo: string
}

const PAGE_SIZE = 50

const inputCls = 'w-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 p-2'

const Estoque = () => {
  const [produtos, setProdutos] = useState<Produto[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [searchInput, setSearchInput] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [kardexProduto, setKardexProduto] = useState<Produto | null>(null)
  const [selectedProduto, setSelectedProduto] = useState<Produto | null>(null)
  const [movimentacoes, setMovimentacoes] = useState<Movimentacao[]>([])
  const [loadingMov, setLoadingMov] = useState(false)
  const [isNovaMovOpen, setIsNovaMovOpen] = useState(false)
  const [novaMov, setNovaMov] = useState<NovaMovimentacao>({ produto_id: 0, tipo: 'entrada', quantidade: 0, motivo: '' })
  const [submittingMov, setSubmittingMov] = useState(false)

  const handleCloseNovaMov = () => {
    setIsNovaMovOpen(false)
    setSelectedProduto(null)
  }

  const closeKardex = () => {
    setKardexProduto(null)
    setMovimentacoes([])
  }

  const kardexModalRef = useAccessibleModal(Boolean(kardexProduto), closeKardex)
  const novaMovModalRef = useAccessibleModal(isNovaMovOpen, handleCloseNovaMov)

  const fetchProdutos = useCallback(async (newPage = 1, search = searchTerm) => {
    setLoading(true)
    try {
      const response = await api.get('/produtos', { params: { page: newPage, page_size: PAGE_SIZE, incluir_inativos: true, search: search || undefined } })
      const data = response.data
      setProdutos(data.items ?? data)
      if (data.pages) setTotalPages(data.pages)
    } catch (error) {
      console.error('Erro ao buscar produtos', error)
    } finally {
      setLoading(false)
    }
  }, [searchTerm])

  const fetchKardex = async (produtoId: number) => {
    setLoadingMov(true)
    try {
      const response = await apiV2.get(`/estoque/historico/${produtoId}`)
      const data = response.data
      setMovimentacoes(Array.isArray(data) ? data : (data.items ?? []))
    } catch (error) {
      console.error('Erro ao buscar kardex', error)
    } finally {
      setLoadingMov(false)
    }
  }

  useEffect(() => { fetchProdutos(page, searchTerm) }, [page, searchTerm, fetchProdutos])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault(); setPage(1); setSearchTerm(searchInput.trim())
  }

  useEffect(() => {
    const normalizedSearch = searchInput.trim()
    const timeoutId = setTimeout(() => {
      if (normalizedSearch !== searchTerm) {
        setPage(1)
        setSearchTerm(normalizedSearch)
      }
    }, 300)

    return () => clearTimeout(timeoutId)
  }, [searchInput, searchTerm])

  const handleOpenKardex = (produto: Produto) => {
    setKardexProduto(produto)
    fetchKardex(produto.id)
  }

  const handleOpenNovaMov = (produto: Produto) => {
    setNovaMov({ produto_id: produto.id, tipo: 'entrada', quantidade: 0, motivo: '' })
    setSelectedProduto(produto); setIsNovaMovOpen(true)
  }

  const handleSubmitMov = async (e: React.FormEvent) => {
    e.preventDefault()
    if (novaMov.quantidade <= 0) {
      toast.error('A quantidade deve ser maior que zero.')
      return
    }
    setSubmittingMov(true)
    try {
      await apiV2.post('/estoque/transacao', novaMov)
      toast.success('Movimentação registrada com sucesso!')
      fetchProdutos(page)
      if (kardexProduto && kardexProduto.id === novaMov.produto_id) fetchKardex(novaMov.produto_id)
      setIsNovaMovOpen(false)
      setSelectedProduto(null)
    } catch (error) {
      console.error('Erro ao registrar movimentação', error)
      toast.error('Erro ao registrar movimentação. Verifique os dados.')
    } finally {
      setSubmittingMov(false)
    }
  }

  return (
    <div className="container mx-auto relative">
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Estoque</h1>
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <input
            type="text"
            placeholder="Buscar por nome"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700">
            Buscar
          </button>
          {searchTerm && (
            <button type="button" onClick={() => { setSearchInput(''); setSearchTerm(''); setPage(1) }}
              className="rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-gray-600 dark:text-gray-300 transition hover:bg-gray-100 dark:hover:bg-gray-700">
              Limpar
            </button>
          )}
        </form>
      </div>

      {/* Tabela */}
      <div className="overflow-x-auto rounded-lg bg-white shadow dark:bg-gray-800">
        <table className="min-w-[760px] divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              {['Produto', 'Código', 'Unidade', 'Saldo Atual', 'Ações'].map(h => (
                <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {loading ? (
              <tr><td colSpan={5} className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">Carregando...</td></tr>
            ) : produtos.length === 0 ? (
              <tr><td colSpan={5} className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">Nenhum produto encontrado.</td></tr>
            ) : (
              produtos.map((produto) => (
                <tr key={produto.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900 dark:text-gray-100">{produto.nome}</td>
                  <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{produto.codigo_barras || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{produto.unidade}</td>
                  <td className="px-6 py-4 text-sm font-bold text-blue-600 dark:text-blue-400">{produto.estoque_atual ?? 'N/A'}</td>
                  <td className="px-6 py-4 text-sm">
                    <div className="flex gap-3">
                      <button onClick={() => handleOpenNovaMov(produto)} aria-label={`Ajustar estoque de ${produto.nome}`} className="text-emerald-600 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 font-medium">
                        Ajustar
                      </button>
                      <span className="text-gray-300 dark:text-gray-600">|</span>
                      <button onClick={() => handleOpenKardex(produto)} aria-label={`Ver kardex de ${produto.nome}`} className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium">
                        Ver Kardex
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Paginação */}
      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <span className="text-sm text-gray-500 dark:text-gray-400">
          Página {page} de {totalPages} — mostrando {produtos.length} registros
        </span>
        <div className="flex gap-2">
          <button onClick={() => setPage(p => p - 1)} disabled={page === 1 || loading}
            className="px-3 py-1 rounded border border-gray-300 dark:border-gray-600 text-sm text-gray-700 dark:text-gray-300 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-700">
            ← Anterior
          </button>
          <button onClick={() => setPage(p => p + 1)} disabled={page >= totalPages || loading}
            className="px-3 py-1 rounded border border-gray-300 dark:border-gray-600 text-sm text-gray-700 dark:text-gray-300 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-700">
            Próxima →
          </button>
        </div>
      </div>

      {/* Modal Kardex */}
      {kardexProduto && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="estoque-kardex-title"
          onMouseDown={closeKardex}
        >
          <div
            ref={kardexModalRef}
            tabIndex={-1}
            onMouseDown={(event) => event.stopPropagation()}
            className="flex max-h-[90vh] w-full max-w-4xl flex-col rounded-lg bg-white shadow-xl dark:bg-gray-800"
          >
            <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
              <h2 id="estoque-kardex-title" className="text-xl font-bold text-gray-800 dark:text-gray-100">Kardex: {kardexProduto.nome}</h2>
              <div className="flex gap-2">
                <button onClick={() => handleOpenNovaMov(kardexProduto)}
                  className="px-3 py-1 bg-emerald-600 text-white rounded hover:bg-emerald-700 transition font-medium mr-2">
                  + Novo Lançamento
                </button>
                <button onClick={closeKardex}
                  aria-label="Fechar modal de kardex"
                  className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 text-2xl leading-none">
                  ×
                </button>
              </div>
            </div>

            <div className="p-6 overflow-y-auto flex-1">
              {loadingMov ? (
                <p className="text-center text-gray-500 dark:text-gray-400">Carregando movimentações...</p>
              ) : movimentacoes.length === 0 ? (
                <p className="text-center text-gray-500 dark:text-gray-400">Nenhuma movimentação encontrada.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-[720px] divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Data</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Tipo</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Motivo</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-green-600 dark:text-green-400 uppercase">Entrada</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-red-600 dark:text-red-400 uppercase">Saída</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {movimentacoes.map((mov) => {
                      const isEntrada = mov.quantidade > 0
                      return (
                        <tr key={mov.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                          <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-300">
                            {new Date(mov.data_transacao).toLocaleString('pt-BR')}
                          </td>
                          <td className="px-4 py-2 text-sm">
                            <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${mov.tipo === 'entrada' || mov.tipo === 'devolucao'
                                ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400'
                                : mov.tipo === 'saida'
                                  ? 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400'
                                  : 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-400'
                              }`}>
                              {mov.tipo.charAt(0).toUpperCase() + mov.tipo.slice(1)}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-300">{mov.motivo ?? '-'}</td>
                          <td className="px-4 py-2 text-sm text-right text-green-600 dark:text-green-400 font-medium">
                            {isEntrada ? `+${mov.quantidade}` : '-'}
                          </td>
                          <td className="px-4 py-2 text-sm text-right text-red-600 dark:text-red-400 font-medium">
                            {!isEntrada ? `${mov.quantidade}` : '-'}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/30 text-right">
              <button onClick={closeKardex}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition">
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Nova Movimentação */}
      {isNovaMovOpen && selectedProduto && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black bg-opacity-60 p-4"
          role="dialog"
          aria-modal="true"
          aria-label="Lancar movimentacao de estoque"
          onMouseDown={handleCloseNovaMov}
        >
          <div
            ref={novaMovModalRef}
            tabIndex={-1}
            onMouseDown={(event) => event.stopPropagation()}
            className="w-full max-w-md rounded-lg bg-white shadow-2xl dark:bg-gray-800"
          >
            <div className="p-5 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-bold text-gray-800 dark:text-gray-100">Lançar Movimentação</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{selectedProduto.nome}</p>
            </div>

            <form onSubmit={handleSubmitMov} className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo de Movimentação</label>
                <select value={novaMov.tipo} onChange={(e) => setNovaMov({ ...novaMov, tipo: e.target.value as NovaMovimentacao['tipo'] })}
                  className={inputCls} required>
                  <option value="entrada">Entrada</option>
                  <option value="saida">Saída</option>
                  <option value="ajuste">Ajuste de Saldo</option>
                  <option value="devolucao">Devolução</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Quantidade</label>
                <input type="number" min="1" step="1" value={novaMov.quantidade || ''}
                  onChange={(e) => setNovaMov({ ...novaMov, quantidade: parseInt(e.target.value) || 0 })}
                  className={inputCls} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Motivo / Observação</label>
                <textarea value={novaMov.motivo} onChange={(e) => setNovaMov({ ...novaMov, motivo: e.target.value })}
                  className={inputCls} rows={3}
                  placeholder="Ex: Nota fiscal 123, Ajuste contábil, Produto danificado..." />
              </div>

              <div className="pt-4 flex justify-end gap-3 border-t border-gray-200 dark:border-gray-700">
                <button type="button" onClick={handleCloseNovaMov} disabled={submittingMov}
                  className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition">
                  Cancelar
                </button>
                <button type="submit" disabled={submittingMov}
                  className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition disabled:opacity-50">
                  {submittingMov ? 'Salvando...' : 'Confirmar Lançamento'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Estoque
