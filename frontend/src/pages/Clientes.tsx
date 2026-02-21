import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import api from '../services/api'

interface Cliente {
  id: number
  nome: string
  cpf_cnpj?: string | null
  telefone?: string | null
  cidade?: string | null
  uf?: string | null
  codigo_legado?: number | null
}

interface ClientePayload {
  nome: string
  cpf_cnpj?: string
  telefone?: string
  cidade?: string
  uf?: string
  codigo_legado?: number
}

interface FormState {
  nome: string
  cpf_cnpj: string
  telefone: string
  cidade: string
  uf: string
  codigo_legado: string
}

type ModalMode = 'create' | 'edit'

const PAGE_SIZE = 50

const emptyFormState: FormState = {
  nome: '',
  cpf_cnpj: '',
  telefone: '',
  cidade: '',
  uf: '',
  codigo_legado: ''
}

const removeNonDigits = (value: string) => value.replace(/\D/g, '')

const normalizeCpfCnpj = (value: string) => {
  const digits = removeNonDigits(value)
  if (!digits) {
    return ''
  }

  if (digits.length <= 11) {
    return digits
      .slice(0, 11)
      .replace(/^(\d{3})(\d)/, '$1.$2')
      .replace(/^(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
      .replace(/\.(\d{3})(\d)/, '.$1-$2')
  }

  return digits
    .slice(0, 14)
    .replace(/^(\d{2})(\d)/, '$1.$2')
    .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/\.(\d{3})(\d)/, '.$1/$2')
    .replace(/(\d{4})(\d)/, '$1-$2')
}

const normalizePayload = (formState: FormState): ClientePayload => {
  const payload: ClientePayload = {
    nome: formState.nome.trim()
  }

  const cpfCnpj = removeNonDigits(formState.cpf_cnpj)
  const telefone = formState.telefone.trim()
  const cidade = formState.cidade.trim()
  const uf = formState.uf.trim().toUpperCase()
  const codigoLegado = formState.codigo_legado.trim()

  if (cpfCnpj) {
    payload.cpf_cnpj = cpfCnpj
  }

  if (telefone) {
    payload.telefone = telefone
  }

  if (cidade) {
    payload.cidade = cidade
  }

  if (uf) {
    payload.uf = uf
  }

  if (codigoLegado) {
    payload.codigo_legado = Number(codigoLegado)
  }

  return payload
}

const Clientes = () => {
  const queryClient = useQueryClient()
  const [searchInput, setSearchInput] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(0)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<ModalMode>('create')
  const [editingCliente, setEditingCliente] = useState<Cliente | null>(null)
  const [formState, setFormState] = useState<FormState>(emptyFormState)
  const [formError, setFormError] = useState('')

  const clientesQuery = useQuery({
    queryKey: ['clientes', page, searchTerm],
    queryFn: async () => {
      const response = await api.get('/clientes/', {
        params: {
          search: searchTerm || undefined,
          limit: PAGE_SIZE,
          skip: page * PAGE_SIZE
        }
      })
      return response.data as Cliente[]
    },
    placeholderData: (previousData) => previousData
  })

  const clientes = clientesQuery.data ?? []

  const createMutation = useMutation({
    mutationFn: async (payload: ClientePayload) => {
      const response = await api.post('/clientes/', payload)
      return response.data as Cliente
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clientes'] })
      closeModal()
    },
    onError: () => {
      setFormError('Não foi possível criar o cliente. Verifique os dados e tente novamente.')
    }
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: ClientePayload }) => {
      const response = await api.put(`/clientes/${id}`, payload)
      return response.data as Cliente
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clientes'] })
      closeModal()
    },
    onError: () => {
      setFormError('Não foi possível atualizar o cliente. Verifique os dados e tente novamente.')
    }
  })

  const isSaving = createMutation.isPending || updateMutation.isPending

  const totalEstimado = useMemo(() => {
    if (clientes.length < PAGE_SIZE) {
      return page * PAGE_SIZE + clientes.length
    }
    return (page + 2) * PAGE_SIZE
  }, [clientes.length, page])

  const totalPages = Math.max(1, Math.ceil(totalEstimado / PAGE_SIZE))

  const handleSearchSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setPage(0)
    setSearchTerm(searchInput.trim())
  }

  const openCreateModal = () => {
    setModalMode('create')
    setEditingCliente(null)
    setFormState(emptyFormState)
    setFormError('')
    setIsModalOpen(true)
  }

  const openEditModal = (cliente: Cliente) => {
    setModalMode('edit')
    setEditingCliente(cliente)
    setFormState({
      nome: cliente.nome ?? '',
      cpf_cnpj: normalizeCpfCnpj(cliente.cpf_cnpj ?? ''),
      telefone: cliente.telefone ?? '',
      cidade: cliente.cidade ?? '',
      uf: (cliente.uf ?? '').toUpperCase(),
      codigo_legado: cliente.codigo_legado ? String(cliente.codigo_legado) : ''
    })
    setFormError('')
    setIsModalOpen(true)
  }

  function closeModal() {
    setIsModalOpen(false)
    setEditingCliente(null)
    setFormState(emptyFormState)
    setFormError('')
  }

  const handleInputChange = (field: keyof FormState, value: string) => {
    if (field === 'cpf_cnpj') {
      setFormState((previous) => ({
        ...previous,
        cpf_cnpj: normalizeCpfCnpj(value)
      }))
      return
    }

    if (field === 'codigo_legado') {
      setFormState((previous) => ({
        ...previous,
        codigo_legado: removeNonDigits(value).slice(0, 10)
      }))
      return
    }

    if (field === 'uf') {
      setFormState((previous) => ({
        ...previous,
        uf: value.toUpperCase().slice(0, 2)
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

    if (!formState.nome.trim()) {
      setFormError('Informe o nome do cliente.')
      return
    }

    const cpfCnpjDigits = removeNonDigits(formState.cpf_cnpj)
    if (cpfCnpjDigits && cpfCnpjDigits.length !== 11 && cpfCnpjDigits.length !== 14) {
      setFormError('CPF/CNPJ deve ter 11 ou 14 dígitos.')
      return
    }

    const payload = normalizePayload(formState)

    if (modalMode === 'create') {
      createMutation.mutate(payload)
      return
    }

    if (!editingCliente) {
      setFormError('Cliente inválido para edição.')
      return
    }

    updateMutation.mutate({ id: editingCliente.id, payload })
  }

  return (
    <div className="container mx-auto">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Clientes</h1>
        <div className="flex flex-wrap gap-2">
          <form onSubmit={handleSearchSubmit} className="flex gap-2">
            <input
              type="text"
              placeholder="Buscar por nome ou CPF/CNPJ"
              className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
          <button
            type="button"
            onClick={openCreateModal}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-white transition hover:bg-emerald-700"
          >
            + Novo Cliente
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg bg-white dark:bg-gray-800 shadow">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Nome</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">CPF/CNPJ</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Telefone</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Cidade/UF</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Cód. Legado</th>
              <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-800">
            {clientesQuery.isLoading ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center">Carregando...</td>
              </tr>
            ) : clientesQuery.isError ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-red-600">Erro ao carregar clientes.</td>
              </tr>
            ) : clientes.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">Nenhum cliente encontrado.</td>
              </tr>
            ) : (
              clientes.map((cliente) => (
                <tr key={cliente.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{cliente.nome}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{normalizeCpfCnpj(cliente.cpf_cnpj || '') || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{cliente.telefone || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{cliente.cidade || ''}/{cliente.uf || ''}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{cliente.codigo_legado || '-'}</td>
                  <td className="px-6 py-4 text-right text-sm">
                    <button
                      type="button"
                      onClick={() => openEditModal(cliente)}
                      className="rounded border border-gray-300 dark:border-gray-600 px-3 py-1 text-gray-700 transition hover:bg-gray-100 dark:hover:bg-gray-700"
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
          Página {page + 1} de {totalPages} — mostrando {clientes.length} registros
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage((previous) => previous - 1)}
            disabled={page === 0 || clientesQuery.isFetching}
            className="rounded border border-gray-300 dark:border-gray-600 px-3 py-1 text-sm text-gray-700 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40"
          >
            ← Anterior
          </button>
          <button
            onClick={() => setPage((previous) => previous + 1)}
            disabled={clientes.length < PAGE_SIZE || clientesQuery.isFetching}
            className="rounded border border-gray-300 dark:border-gray-600 px-3 py-1 text-sm text-gray-700 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40"
          >
            Próxima →
          </button>
        </div>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="w-full max-w-xl rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-xl">
            <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
              <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                {modalMode === 'create' ? 'Novo cliente' : 'Editar cliente'}
              </h2>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 px-6 py-5">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="cliente-nome">
                  Nome *
                </label>
                <input
                  id="cliente-nome"
                  type="text"
                  value={formState.nome}
                  onChange={(event) => handleInputChange('nome', event.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Nome do cliente"
                />
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="cliente-cpf-cnpj">
                    CPF/CNPJ
                  </label>
                  <input
                    id="cliente-cpf-cnpj"
                    type="text"
                    value={formState.cpf_cnpj}
                    onChange={(event) => handleInputChange('cpf_cnpj', event.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="000.000.000-00"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="cliente-telefone">
                    Telefone
                  </label>
                  <input
                    id="cliente-telefone"
                    type="text"
                    value={formState.telefone}
                    onChange={(event) => handleInputChange('telefone', event.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="(00) 00000-0000"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div className="md:col-span-2">
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="cliente-cidade">
                    Cidade
                  </label>
                  <input
                    id="cliente-cidade"
                    type="text"
                    value={formState.cidade}
                    onChange={(event) => handleInputChange('cidade', event.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Cidade"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="cliente-uf">
                    UF
                  </label>
                  <input
                    id="cliente-uf"
                    type="text"
                    value={formState.uf}
                    onChange={(event) => handleInputChange('uf', event.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="UF"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="cliente-codigo-legado">
                  Código legado
                </label>
                <input
                  id="cliente-codigo-legado"
                  type="text"
                  value={formState.codigo_legado}
                  onChange={(event) => handleInputChange('codigo_legado', event.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Será gerado automaticamente se vazio"
                  disabled={modalMode === 'edit'}
                />
              </div>

              {formError && (
                <div className="rounded-md border border-red-200 dark:border-red-700 bg-red-50 px-3 py-2 text-sm text-red-700">
                  {formError}
                </div>
              )}

              <div className="flex justify-end gap-3 border-t border-gray-200 dark:border-gray-700 pt-4">
                <button
                  type="button"
                  onClick={closeModal}
                  className="rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-gray-700 dark:text-gray-100 transition hover:bg-gray-100 dark:hover:bg-gray-700"
                  disabled={isSaving}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700 disabled:opacity-60"
                  disabled={isSaving}
                >
                  {isSaving ? 'Salvando...' : modalMode === 'create' ? 'Criar cliente' : 'Salvar alterações'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Clientes
