import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import api from '../services/api'

interface Fornecedor {
  id: number
  nome: string
  cnpj: string
  email?: string | null
  telefone?: string | null
  contato?: string | null
}

interface FornecedorPayload {
  nome: string
  cnpj: string
  email?: string
  telefone?: string
  contato?: string
}

const PAGE_SIZE = 20

const removeNonDigits = (value: string) => value.replace(/\D/g, '')

const formatCnpj = (value: string) => {
  const digits = removeNonDigits(value).slice(0, 14)

  return digits
    .replace(/^(\d{2})(\d)/, '$1.$2')
    .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/\.(\d{3})(\d)/, '.$1/$2')
    .replace(/(\d{4})(\d)/, '$1-$2')
}

const normalizePayload = (formData: FormState): FornecedorPayload => {
  const payload: FornecedorPayload = {
    nome: formData.nome.trim(),
    cnpj: removeNonDigits(formData.cnpj)
  }

  const email = formData.email.trim()
  const telefone = formData.telefone.trim()
  const contato = formData.contato.trim()

  if (email) {
    payload.email = email
  }

  if (telefone) {
    payload.telefone = telefone
  }

  if (contato) {
    payload.contato = contato
  }

  return payload
}

type ModalMode = 'create' | 'edit'

interface FormState {
  nome: string
  cnpj: string
  email: string
  telefone: string
  contato: string
}

const emptyFormState: FormState = {
  nome: '',
  cnpj: '',
  email: '',
  telefone: '',
  contato: ''
}

const Fornecedores = () => {
  const queryClient = useQueryClient()
  const [searchInput, setSearchInput] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(0)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<ModalMode>('create')
  const [editingFornecedor, setEditingFornecedor] = useState<Fornecedor | null>(null)
  const [formState, setFormState] = useState<FormState>(emptyFormState)
  const [formError, setFormError] = useState('')

  const fornecedoresQuery = useQuery({
    queryKey: ['fornecedores', page, searchTerm],
    queryFn: async () => {
      const response = await api.get('/fornecedores/', {
        params: {
          skip: page * PAGE_SIZE,
          limit: PAGE_SIZE,
          search: searchTerm || undefined
        }
      })
      return response.data as Fornecedor[]
    },
    placeholderData: (previousData) => previousData
  })

  const fornecedores = fornecedoresQuery.data ?? []

  const createMutation = useMutation({
    mutationFn: async (payload: FornecedorPayload) => {
      const response = await api.post('/fornecedores/', payload)
      return response.data as Fornecedor
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fornecedores'] })
      closeModal()
    },
    onError: () => {
      setFormError('Não foi possível criar o fornecedor. Verifique os dados e tente novamente.')
    }
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: FornecedorPayload }) => {
      const response = await api.put(`/fornecedores/${id}`, payload)
      return response.data as Fornecedor
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fornecedores'] })
      closeModal()
    },
    onError: () => {
      setFormError('Não foi possível atualizar o fornecedor. Verifique os dados e tente novamente.')
    }
  })

  const isSaving = createMutation.isPending || updateMutation.isPending

  const totalEstimado = useMemo(() => {
    if (fornecedores.length < PAGE_SIZE) {
      return page * PAGE_SIZE + fornecedores.length
    }

    return (page + 2) * PAGE_SIZE
  }, [fornecedores.length, page])

  const totalPages = Math.max(1, Math.ceil(totalEstimado / PAGE_SIZE))

  const openCreateModal = () => {
    setModalMode('create')
    setEditingFornecedor(null)
    setFormState(emptyFormState)
    setFormError('')
    setIsModalOpen(true)
  }

  const openEditModal = (fornecedor: Fornecedor) => {
    setModalMode('edit')
    setEditingFornecedor(fornecedor)
    setFormState({
      nome: fornecedor.nome ?? '',
      cnpj: formatCnpj(fornecedor.cnpj ?? ''),
      email: fornecedor.email ?? '',
      telefone: fornecedor.telefone ?? '',
      contato: fornecedor.contato ?? ''
    })
    setFormError('')
    setIsModalOpen(true)
  }

  function closeModal() {
    setIsModalOpen(false)
    setEditingFornecedor(null)
    setFormError('')
    setFormState(emptyFormState)
  }

  const handleSearchSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setPage(0)
    setSearchTerm(searchInput.trim())
  }

  const handleInputChange = (field: keyof FormState, value: string) => {
    if (field === 'cnpj') {
      setFormState((previous) => ({
        ...previous,
        cnpj: formatCnpj(value)
      }))
      return
    }

    setFormState((previous) => ({
      ...previous,
      [field]: value
    }))
  }

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setFormError('')

    const cnpjDigits = removeNonDigits(formState.cnpj)

    if (!formState.nome.trim()) {
      setFormError('Informe o nome do fornecedor.')
      return
    }

    if (cnpjDigits.length !== 14) {
      setFormError('O CNPJ deve conter 14 dígitos.')
      return
    }

    const payload = normalizePayload(formState)

    if (modalMode === 'create') {
      createMutation.mutate(payload)
      return
    }

    if (!editingFornecedor) {
      setFormError('Fornecedor inválido para edição.')
      return
    }

    updateMutation.mutate({ id: editingFornecedor.id, payload })
  }

  return (
    <div className="container mx-auto">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Fornecedores</h1>
        <div className="flex flex-wrap gap-2">
          <form onSubmit={handleSearchSubmit} className="flex gap-2">
            <input
              type="text"
              value={searchInput}
              placeholder="Buscar por nome ou CNPJ"
              onChange={(event) => setSearchInput(event.target.value)}
              className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              className="rounded-lg bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700"
            >
              Buscar
            </button>
          </form>
          <button
            type="button"
            onClick={openCreateModal}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-white transition hover:bg-emerald-700"
          >
            + Novo Fornecedor
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg bg-white dark:bg-gray-800 shadow">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Nome</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">CNPJ</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Contato</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Ações</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-800">
            {fornecedoresQuery.isLoading ? (
              <tr>
                <td colSpan={4} className="px-6 py-4 text-center">Carregando...</td>
              </tr>
            ) : fornecedoresQuery.isError ? (
              <tr>
                <td colSpan={4} className="px-6 py-4 text-center text-red-600">Erro ao carregar fornecedores.</td>
              </tr>
            ) : fornecedores.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-4 text-center text-gray-500">Nenhum fornecedor encontrado.</td>
              </tr>
            ) : (
              fornecedores.map((fornecedor) => (
                <tr key={fornecedor.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{fornecedor.nome}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{formatCnpj(fornecedor.cnpj || '')}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {fornecedor.contato || fornecedor.telefone || fornecedor.email || '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    <button
                      type="button"
                      onClick={() => openEditModal(fornecedor)}
                      className="rounded border border-blue-600 px-3 py-1 text-blue-600 transition hover:bg-blue-50"
                    >
                      Editar
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <span className="text-sm text-gray-500">
          Página {page + 1} de {totalPages} — mostrando {fornecedores.length} registros
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setPage((current) => Math.max(0, current - 1))}
            disabled={page === 0 || fornecedoresQuery.isFetching}
            className="rounded border border-gray-300 dark:border-gray-600 px-3 py-1 text-sm text-gray-700 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40"
          >
            ← Anterior
          </button>
          <button
            type="button"
            onClick={() => setPage((current) => current + 1)}
            disabled={fornecedores.length < PAGE_SIZE || fornecedoresQuery.isFetching}
            className="rounded border border-gray-300 dark:border-gray-600 px-3 py-1 text-sm text-gray-700 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40"
          >
            Próxima →
          </button>
        </div>
      </div>

      {isModalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-3">
          <div className="w-full max-w-xl rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-6 shadow-2xl">
            <div className="mb-4 flex items-start justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                {modalMode === 'create' ? 'Novo Fornecedor' : 'Editar Fornecedor'}
              </h2>
              <button
                type="button"
                onClick={closeModal}
                className="text-gray-500 transition hover:text-gray-700 dark:text-gray-300"
                disabled={isSaving}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Nome *</label>
                <input
                  type="text"
                  value={formState.nome}
                  onChange={(event) => handleInputChange('nome', event.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Razão social ou nome fantasia"
                  required
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">CNPJ *</label>
                <input
                  type="text"
                  value={formState.cnpj}
                  onChange={(event) => handleInputChange('cnpj', event.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="00.000.000/0000-00"
                  maxLength={18}
                  required
                />
                <p className="mt-1 text-xs text-gray-500">Digite os 14 dígitos do CNPJ.</p>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Telefone</label>
                  <input
                    type="text"
                    value={formState.telefone}
                    onChange={(event) => handleInputChange('telefone', event.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="(00) 00000-0000"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Contato</label>
                  <input
                    type="text"
                    value={formState.contato}
                    onChange={(event) => handleInputChange('contato', event.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Nome do contato"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">E-mail</label>
                <input
                  type="email"
                  value={formState.email}
                  onChange={(event) => handleInputChange('email', event.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="contato@fornecedor.com.br"
                />
              </div>

              {formError ? <p className="text-sm font-medium text-red-600">{formError}</p> : null}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-gray-700 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700"
                  disabled={isSaving}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-70"
                  disabled={isSaving}
                >
                  {isSaving ? 'Salvando...' : modalMode === 'create' ? 'Criar fornecedor' : 'Salvar alterações'}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default Fornecedores
