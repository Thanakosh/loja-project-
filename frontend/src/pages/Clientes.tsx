import { useState, useEffect } from 'react'
import api from '../services/api'

interface Cliente {
  id: number
  nome: string
  cpf_cnpj: string
  telefone: string
  cidade: string
  uf: string
  codigo_legado?: number
}

const PAGE_SIZE = 50

const Clientes = () => {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(0)
  const [total, setTotal] = useState(0)

  const fetchClientes = async (search = '', newPage = 0) => {
    setLoading(true)
    try {
      const response = await api.get('/clientes', {
        params: { search, limit: PAGE_SIZE, skip: newPage * PAGE_SIZE }
      })
      setClientes(response.data)
      // API não retorna total, então desabilita próxima página se vier menos que PAGE_SIZE
      setTotal(response.data.length < PAGE_SIZE ? newPage * PAGE_SIZE + response.data.length : (newPage + 2) * PAGE_SIZE)
    } catch (error) {
      console.error('Erro ao buscar clientes', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchClientes(searchTerm, page)
  }, [page])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(0)
    fetchClientes(searchTerm, 0)
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="container mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-800">Clientes</h1>
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            placeholder="Buscar por nome ou CPF..."
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Buscar
          </button>
        </form>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">CPF/CNPJ</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Telefone</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cidade/UF</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cód. Legado</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center">Carregando...</td>
              </tr>
            ) : clientes.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">Nenhum cliente encontrado.</td>
              </tr>
            ) : (
              clientes.map((cliente) => (
                <tr key={cliente.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{cliente.nome}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{cliente.cpf_cnpj || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{cliente.telefone || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{cliente.cidade || ''}/{cliente.uf || ''}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{cliente.codigo_legado || '-'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Paginação */}
      <div className="flex items-center justify-between mt-4">
        <span className="text-sm text-gray-500">
          Página {page + 1} — mostrando {clientes.length} registros
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(p => p - 1)}
            disabled={page === 0 || loading}
            className="px-3 py-1 rounded border text-sm disabled:opacity-40 hover:bg-gray-50"
          >
            ← Anterior
          </button>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={clientes.length < PAGE_SIZE || loading}
            className="px-3 py-1 rounded border text-sm disabled:opacity-40 hover:bg-gray-50"
          >
            Próxima →
          </button>
        </div>
      </div>
    </div>
  )
}

export default Clientes
