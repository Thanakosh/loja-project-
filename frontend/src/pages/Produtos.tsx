import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import api from '../services/api'

interface Produto {
  id: number
  nome: string
  descricao?: string | null
  fornecedor: string
  preco_unitario: number
  preco_liquido: number
  codigo_ncm?: string | null
  unidade?: string | null
  estoque_atual: number
  estoque_baixo: boolean
  estoque_minimo: number
  ativo: boolean
  data_emissao?: string | null
  numero_nota?: string | null
  cnpj_fornecedor?: string | null
}

interface ProdutoFormPayload {
  nome: string
  fornecedor: string
  preco_unitario: number
  preco_liquido: number
  estoque_minimo: number
  quantidade_inicial?: number
  unidade?: string
  codigo_ncm?: string
  descricao?: string
}

interface ProdutoListResponse {
  items: Produto[]
  total: number
  page: number
  pages: number
}

interface FormState {
  nome: string
  fornecedor: string
  preco_unitario: string
  preco_liquido: string
  estoque_minimo: string
  quantidade_inicial: string
  unidade: string
  codigo_ncm: string
  descricao: string
}

interface FormErrors {
  nome?: string
  fornecedor?: string
  preco_unitario?: string
  preco_liquido?: string
}

type ModalMode = 'create' | 'edit'

const PAGE_SIZE = 50

const moneyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL'
})

const emptyFormState: FormState = {
  nome: '',
  fornecedor: '',
  preco_unitario: '',
  preco_liquido: '',
  estoque_minimo: '0',
  quantidade_inicial: '0',
  unidade: '',
  codigo_ncm: '',
  descricao: ''
}

const Produtos = () => {
  const queryClient = useQueryClient()
  const [searchInput, setSearchInput] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(1)
  const [incluirInativos, setIncluirInativos] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<ModalMode>('create')
  const [editingProduto, setEditingProduto] = useState<Produto | null>(null)
  const [formState, setFormState] = useState<FormState>(emptyFormState)
  const [formErrors, setFormErrors] = useState<FormErrors>({})
  const [formError, setFormError] = useState('')

  const produtosQuery = useQuery({
    queryKey: ['produtos', page, searchTerm, incluirInativos],
    queryFn: async () => {
      const response = await api.get('/produtos/', {
        params: {
          page,
          page_size: PAGE_SIZE,
          incluir_inativos: incluirInativos,
          search: searchTerm || undefined
        }
      })
      return response.data as ProdutoListResponse
    },
    placeholderData: (previousData) => previousData
  })

  const produtos = produtosQuery.data?.items ?? []
  const totalPages = Math.max(1, produtosQuery.data?.pages ?? 1)

  const createMutation = useMutation({
    mutationFn: async (payload: ProdutoFormPayload) => {
      const response = await api.post('/produtos/', payload)
      return response.data as Produto
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['produtos'] })
      closeModal()
    },
    onError: () => {
      setFormError('Não foi possível criar o produto. Verifique os dados e tente novamente.')
    }
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: ProdutoFormPayload }) => {
      const response = await api.put(`/produtos/${id}`, payload)
      return response.data as Produto
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['produtos'] })
      closeModal()
    },
    onError: () => {
      setFormError('Não foi possível atualizar o produto. Verifique os dados e tente novamente.')
    }
  })

  const deactivateMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/produtos/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['produtos'] })
    }
  })

  const reactivateMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.post(`/produtos/${id}/reativar`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['produtos'] })
    }
  })

  const isSaving = createMutation.isPending || updateMutation.isPending

  const openCreateModal = () => {
    setModalMode('create')
    setEditingProduto(null)
    setFormState(emptyFormState)
    setFormErrors({})
    setFormError('')
    setIsModalOpen(true)
  }

  const openEditModal = (produto: Produto) => {
    setModalMode('edit')
    setEditingProduto(produto)
    setFormState({
      nome: produto.nome ?? '',
      fornecedor: produto.fornecedor ?? '',
      preco_unitario: String(produto.preco_unitario ?? ''),
      preco_liquido: String(produto.preco_liquido ?? ''),
      estoque_minimo: String(produto.estoque_minimo ?? 0),
      quantidade_inicial: '0',
      unidade: produto.unidade ?? '',
      codigo_ncm: produto.codigo_ncm ?? '',
      descricao: produto.descricao ?? ''
    })
    setFormErrors({})
    setFormError('')
    setIsModalOpen(true)
  }

  function closeModal() {
    setIsModalOpen(false)
    setEditingProduto(null)
    setFormState(emptyFormState)
    setFormErrors({})
    setFormError('')
  }

  const handleSearchSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setPage(1)
    setSearchTerm(searchInput.trim())
  }

  const handleInputChange = (field: keyof FormState, value: string) => {
    setFormState((previous) => ({
      ...previous,
      [field]: value
    }))

    if (field in formErrors) {
      setFormErrors((previous) => ({
        ...previous,
        [field]: undefined
      }))
    }
  }

  const validateForm = () => {
    const errors: FormErrors = {}

    if (!formState.nome.trim()) {
      errors.nome = 'Nome é obrigatório.'
    }

    if (!formState.fornecedor.trim()) {
      errors.fornecedor = 'Fornecedor é obrigatório.'
    }

    const precoUnitario = Number(formState.preco_unitario)
    if (!formState.preco_unitario || Number.isNaN(precoUnitario) || precoUnitario <= 0) {
      errors.preco_unitario = 'Preço unitário deve ser maior que zero.'
    }

    const precoLiquido = Number(formState.preco_liquido)
    if (!formState.preco_liquido || Number.isNaN(precoLiquido) || precoLiquido <= 0) {
      errors.preco_liquido = 'Preço líquido deve ser maior que zero.'
    }

    setFormErrors(errors)

    return Object.keys(errors).length === 0
  }

  const buildPayload = (): ProdutoFormPayload => {
    const payload: ProdutoFormPayload = {
      nome: formState.nome.trim(),
      fornecedor: formState.fornecedor.trim(),
      preco_unitario: Number(formState.preco_unitario),
      preco_liquido: Number(formState.preco_liquido),
      estoque_minimo: Math.max(0, Number(formState.estoque_minimo) || 0)
    }

    if (modalMode === 'create') {
      payload.quantidade_inicial = Math.max(0, Number(formState.quantidade_inicial) || 0)
    }

    const unidade = formState.unidade.trim()
    const codigoNcm = formState.codigo_ncm.trim()
    const descricao = formState.descricao.trim()

    if (unidade) {
      payload.unidade = unidade
    }

    if (codigoNcm) {
      payload.codigo_ncm = codigoNcm
    }

    if (descricao) {
      payload.descricao = descricao
    }

    return payload
  }

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setFormError('')

    if (!validateForm()) {
      return
    }

    const payload = buildPayload()

    if (modalMode === 'create') {
      createMutation.mutate(payload)
      return
    }

    if (!editingProduto) {
      setFormError('Produto inválido para edição.')
      return
    }

    updateMutation.mutate({ id: editingProduto.id, payload })
  }

  const handleToggleStatus = (produto: Produto) => {
    if (produto.ativo) {
      const confirmed = window.confirm(`Deseja desativar o produto "${produto.nome}"?`)
      if (!confirmed) {
        return
      }
      deactivateMutation.mutate(produto.id)
      return
    }

    reactivateMutation.mutate(produto.id)
  }

  return (
    <div className="container mx-auto">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-gray-800">Produtos</h1>
        <div className="flex flex-wrap items-center gap-2">
          <form onSubmit={handleSearchSubmit} className="flex gap-2">
            <input
              type="text"
              placeholder="Buscar por nome"
              className="rounded-lg border px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
            />
            <button
              type="submit"
              className="rounded-lg bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700"
            >
              Buscar
            </button>
          </form>

          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={incluirInativos}
              onChange={(event) => {
                setPage(1)
                setIncluirInativos(event.target.checked)
              }}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Mostrar inativos
          </label>

          <button
            type="button"
            onClick={openCreateModal}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-white transition hover:bg-emerald-700"
          >
            + Novo Produto
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg bg-white shadow">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Nome</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Fornecedor</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Preço Unitário</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Estoque Atual</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Estoque Mín.</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Status</th>
              <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Ações</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-200 bg-white">
            {produtosQuery.isLoading ? (
              <tr>
                <td colSpan={7} className="px-6 py-4 text-center">Carregando...</td>
              </tr>
            ) : produtosQuery.isError ? (
              <tr>
                <td colSpan={7} className="px-6 py-4 text-center text-red-600">Erro ao carregar produtos.</td>
              </tr>
            ) : produtos.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-4 text-center text-gray-500">Nenhum produto encontrado.</td>
              </tr>
            ) : (
              produtos.map((produto) => (
                <tr key={produto.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{produto.nome}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{produto.fornecedor}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{moneyFormatter.format(produto.preco_unitario)}</td>
                  <td className={`px-6 py-4 text-sm ${produto.estoque_baixo ? 'font-semibold text-red-600' : 'text-gray-500'}`}>
                    {produto.estoque_atual}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{produto.estoque_minimo}</td>
                  <td className="px-6 py-4 text-sm">
                    <span
                      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${
                        produto.ativo ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {produto.ativo ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right text-sm">
                    <div className="flex justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => openEditModal(produto)}
                        className="rounded border border-gray-300 px-3 py-1 text-gray-700 transition hover:bg-gray-100"
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => handleToggleStatus(produto)}
                        disabled={deactivateMutation.isPending || reactivateMutation.isPending}
                        className="rounded border border-gray-300 px-3 py-1 text-gray-700 transition hover:bg-gray-100 disabled:opacity-60"
                      >
                        {produto.ativo ? 'Desativar' : 'Reativar'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <span className="text-sm text-gray-500">
          Página {produtosQuery.data?.page ?? page} de {totalPages} — mostrando {produtos.length} registros
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setPage((previous) => Math.max(1, previous - 1))}
            disabled={page <= 1 || produtosQuery.isFetching}
            className="rounded border px-3 py-1 text-sm hover:bg-gray-50 disabled:opacity-40"
          >
            ← Anterior
          </button>
          <button
            type="button"
            onClick={() => setPage((previous) => previous + 1)}
            disabled={page >= totalPages || produtosQuery.isFetching}
            className="rounded border px-3 py-1 text-sm hover:bg-gray-50 disabled:opacity-40"
          >
            Próxima →
          </button>
        </div>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="w-full max-w-2xl rounded-lg bg-white shadow-xl">
            <div className="border-b px-6 py-4">
              <h2 className="text-lg font-semibold text-gray-800">
                {modalMode === 'create' ? 'Novo produto' : 'Editar produto'}
              </h2>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 px-6 py-5">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="produto-nome">
                    Nome *
                  </label>
                  <input
                    id="produto-nome"
                    type="text"
                    value={formState.nome}
                    onChange={(event) => handleInputChange('nome', event.target.value)}
                    className="w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Nome do produto"
                  />
                  {formErrors.nome && <p className="mt-1 text-xs text-red-600">{formErrors.nome}</p>}
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="produto-fornecedor">
                    Fornecedor *
                  </label>
                  <input
                    id="produto-fornecedor"
                    type="text"
                    value={formState.fornecedor}
                    onChange={(event) => handleInputChange('fornecedor', event.target.value)}
                    className="w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Nome do fornecedor"
                  />
                  {formErrors.fornecedor && <p className="mt-1 text-xs text-red-600">{formErrors.fornecedor}</p>}
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="produto-preco-unitario">
                    Preço Unitário *
                  </label>
                  <input
                    id="produto-preco-unitario"
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={formState.preco_unitario}
                    onChange={(event) => handleInputChange('preco_unitario', event.target.value)}
                    className="w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {formErrors.preco_unitario && <p className="mt-1 text-xs text-red-600">{formErrors.preco_unitario}</p>}
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="produto-preco-liquido">
                    Preço Líquido *
                  </label>
                  <input
                    id="produto-preco-liquido"
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={formState.preco_liquido}
                    onChange={(event) => handleInputChange('preco_liquido', event.target.value)}
                    className="w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {formErrors.preco_liquido && <p className="mt-1 text-xs text-red-600">{formErrors.preco_liquido}</p>}
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="produto-estoque-minimo">
                    Estoque Mínimo
                  </label>
                  <input
                    id="produto-estoque-minimo"
                    type="number"
                    min="0"
                    step="1"
                    value={formState.estoque_minimo}
                    onChange={(event) => handleInputChange('estoque_minimo', event.target.value)}
                    className="w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {modalMode === 'create' && (
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="produto-estoque-inicial">
                    Estoque Inicial
                  </label>
                  <input
                    id="produto-estoque-inicial"
                    type="number"
                    min="0"
                    step="1"
                    value={formState.quantidade_inicial}
                    onChange={(event) => handleInputChange('quantidade_inicial', event.target.value)}
                    className="w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">Será registrado como entrada de estoque</p>
                </div>
              )}

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="produto-unidade">
                    Unidade
                  </label>
                  <input
                    id="produto-unidade"
                    type="text"
                    value={formState.unidade}
                    onChange={(event) => handleInputChange('unidade', event.target.value)}
                    className="w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="UN, KG, CX"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="produto-codigo-ncm">
                    Código NCM
                  </label>
                  <input
                    id="produto-codigo-ncm"
                    type="text"
                    value={formState.codigo_ncm}
                    onChange={(event) => handleInputChange('codigo_ncm', event.target.value)}
                    className="w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Opcional"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="produto-descricao">
                  Descrição
                </label>
                <textarea
                  id="produto-descricao"
                  value={formState.descricao}
                  onChange={(event) => handleInputChange('descricao', event.target.value)}
                  className="min-h-24 w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Descrição do produto"
                />
              </div>

              {formError && (
                <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                  {formError}
                </div>
              )}

              <div className="flex justify-end gap-3 border-t pt-4">
                <button
                  type="button"
                  onClick={closeModal}
                  className="rounded-lg border px-4 py-2 text-gray-700 transition hover:bg-gray-100"
                  disabled={isSaving}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700 disabled:opacity-60"
                  disabled={isSaving}
                >
                  {isSaving ? 'Salvando...' : modalMode === 'create' ? 'Criar produto' : 'Salvar alterações'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Produtos
