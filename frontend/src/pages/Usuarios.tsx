import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import type { AxiosError } from 'axios'
import { useNavigate } from 'react-router-dom'

import { MANAGEABLE_TABS, getTabLabel, type AppTabId } from '../config/appTabs'
import { useAuthContext, type AuthenticatedUser } from '../contexts/AuthContext'
import { useAccessibleModal } from '../hooks/useAccessibleModal'
import api from '../services/api'

type ModalMode = 'create' | 'edit'

type Usuario = AuthenticatedUser

interface UsuarioPayload {
  username: string
  full_name: string
  email: string
  password: string
  is_active: boolean
  is_superuser: boolean
  allowed_tabs: AppTabId[]
}

const emptyForm: UsuarioPayload = {
  username: '',
  full_name: '',
  email: '',
  password: '',
  is_active: true,
  is_superuser: false,
  allowed_tabs: [],
}

const toFormState = (user: Usuario): UsuarioPayload => ({
  username: user.username ?? '',
  full_name: user.full_name ?? '',
  email: user.email,
  password: '',
  is_active: user.is_active,
  is_superuser: user.is_superuser,
  allowed_tabs: user.allowed_tabs,
})

const buildPayload = (form: UsuarioPayload): UsuarioPayload => ({
  ...form,
  username: form.username.trim(),
  full_name: form.full_name.trim(),
  email: form.email.trim(),
  password: form.password.trim(),
  allowed_tabs: form.is_superuser ? [] : form.allowed_tabs,
})

const getErrorMessage = (error: AxiosError<{ detail?: string }>) =>
  error.response?.data?.detail ?? 'Nao foi possivel concluir a operacao.'

const Usuarios = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { logout, refreshUser, user: currentUser } = useAuthContext()

  const [showModal, setShowModal] = useState(false)
  const [modalMode, setModalMode] = useState<ModalMode>('create')
  const [editingUserId, setEditingUserId] = useState<number | null>(null)
  const [form, setForm] = useState<UsuarioPayload>(emptyForm)

  const closeModal = () => {
    setShowModal(false)
    setModalMode('create')
    setEditingUserId(null)
    setForm(emptyForm)
  }

  const modalRef = useAccessibleModal(showModal, closeModal)

  const { data, isLoading, isError } = useQuery<{ users: Usuario[]; total: number }>({
    queryKey: ['usuarios'],
    queryFn: () => api.get('/users/').then((response) => response.data),
  })

  const createMutation = useMutation({
    mutationFn: (payload: UsuarioPayload) => api.post('/users/register', payload),
    onSuccess: async () => {
      toast.success('Usuario criado com sucesso.')
      await queryClient.invalidateQueries({ queryKey: ['usuarios'] })
      closeModal()
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      toast.error(getErrorMessage(error))
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ userId, payload }: { userId: number; payload: UsuarioPayload }) =>
      api.put(`/users/${userId}`, payload),
    onSuccess: async (_response, variables) => {
      const editedOwnUser = variables.userId === currentUser?.id
      const credentialsChanged =
        editedOwnUser &&
        (variables.payload.password.length > 0 || variables.payload.email !== currentUser?.email)

      toast.success('Usuario atualizado com sucesso.')
      await queryClient.invalidateQueries({ queryKey: ['usuarios'] })

      if (editedOwnUser) {
        if (credentialsChanged) {
          toast.success('Entre novamente para continuar usando a conta atualizada.')
          await logout()
          navigate('/login', { replace: true })
          return
        }

        await refreshUser()
      }

      closeModal()
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      toast.error(getErrorMessage(error))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (userId: number) => api.delete(`/users/${userId}`),
    onSuccess: async () => {
      toast.success('Usuario excluido com sucesso.')
      await queryClient.invalidateQueries({ queryKey: ['usuarios'] })
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      toast.error(getErrorMessage(error))
    },
  })

  const openCreateModal = () => {
    setModalMode('create')
    setEditingUserId(null)
    setForm(emptyForm)
    setShowModal(true)
  }

  const openEditModal = (usuario: Usuario) => {
    setModalMode('edit')
    setEditingUserId(usuario.id)
    setForm(toFormState(usuario))
    setShowModal(true)
  }

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const payload = buildPayload(form)

    if (!payload.username) {
      toast.error('Nome de usuario e obrigatorio.')
      return
    }

    if (!payload.email) {
      toast.error('E-mail e obrigatorio.')
      return
    }

    if (modalMode === 'create' && !payload.password) {
      toast.error('Senha e obrigatoria no cadastro.')
      return
    }

    if (modalMode === 'create') {
      createMutation.mutate(payload)
      return
    }

    if (editingUserId === null) {
      toast.error('Nenhum usuario selecionado para edicao.')
      return
    }

    updateMutation.mutate({ userId: editingUserId, payload })
  }

  const handleToggleTab = (tabId: AppTabId) => {
    setForm((currentForm) => {
      if (currentForm.allowed_tabs.includes(tabId)) {
        return {
          ...currentForm,
          allowed_tabs: currentForm.allowed_tabs.filter((item) => item !== tabId),
        }
      }

      return {
        ...currentForm,
        allowed_tabs: [...currentForm.allowed_tabs, tabId],
      }
    })
  }

  const handleToggleActive = (usuario: Usuario) => {
    const actionLabel = usuario.is_active ? 'desativar' : 'reativar'
    const confirmed = window.confirm(`Deseja ${actionLabel} o usuario ${usuario.username ?? usuario.email}?`)
    if (!confirmed) {
      return
    }

    updateMutation.mutate({
      userId: usuario.id,
      payload: {
        ...toFormState(usuario),
        is_active: !usuario.is_active,
        password: '',
      },
    })
  }

  const handleDelete = (usuario: Usuario) => {
    const confirmed = window.confirm(
      `Excluir permanentemente o usuario ${usuario.username ?? usuario.email}? Essa acao nao pode ser desfeita.`,
    )
    if (!confirmed) {
      return
    }

    deleteMutation.mutate(usuario.id)
  }

  const usuarios = data?.users ?? []
  const isMutating = createMutation.isPending || updateMutation.isPending || deleteMutation.isPending
  const isEditingSelf = modalMode === 'edit' && editingUserId === currentUser?.id

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Usuarios</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Edite perfil, status e abas liberadas para cada conta.
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
        >
          + Novo usuario
        </button>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : isError ? (
          <div className="p-8 text-center text-red-500">Erro ao carregar usuarios.</div>
        ) : usuarios.length === 0 ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">Nenhum usuario cadastrado.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-700/50">
                  <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">#</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">Usuario</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">Nome</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">E-mail</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">Perfil</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">Abas</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">Acoes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {usuarios.map((usuario) => {
                  const isSelf = usuario.id === currentUser?.id
                  const accessSummary = usuario.is_superuser
                    ? 'Acesso total'
                    : usuario.allowed_tabs.length > 0
                      ? usuario.allowed_tabs.map((tabId) => getTabLabel(tabId)).join(', ')
                      : 'Somente dashboard'

                  return (
                    <tr key={usuario.id} className="transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/30">
                      <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{usuario.id}</td>
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">
                        <div className="flex items-center gap-2">
                          <span>{usuario.username ?? usuario.email}</span>
                          {isSelf ? (
                            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[11px] font-medium text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
                              Voce
                            </span>
                          ) : null}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{usuario.full_name ?? '-'}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{usuario.email}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                            usuario.is_active
                              ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400'
                              : 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400'
                          }`}
                        >
                          {usuario.is_active ? 'Ativo' : 'Inativo'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                            usuario.is_superuser
                              ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300'
                              : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
                          }`}
                        >
                          {usuario.is_superuser ? 'Admin' : 'Usuario'}
                        </span>
                      </td>
                      <td className="max-w-xs px-4 py-3 text-gray-600 dark:text-gray-300">{accessSummary}</td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-2">
                          <button
                            onClick={() => openEditModal(usuario)}
                            className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
                          >
                            Editar
                          </button>
                          <button
                            onClick={() => handleToggleActive(usuario)}
                            disabled={isSelf || isMutating}
                            className="rounded-lg border border-amber-300 px-3 py-1.5 text-xs font-medium text-amber-700 transition-colors hover:bg-amber-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-amber-700 dark:text-amber-300 dark:hover:bg-amber-900/30"
                          >
                            {usuario.is_active ? 'Desativar' : 'Reativar'}
                          </button>
                          <button
                            onClick={() => handleDelete(usuario)}
                            disabled={isSelf || isMutating}
                            className="rounded-lg border border-red-300 px-3 py-1.5 text-xs font-medium text-red-700 transition-colors hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-red-700 dark:text-red-300 dark:hover:bg-red-900/30"
                          >
                            Excluir
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
          role="dialog"
          aria-modal="true"
          onMouseDown={closeModal}
        >
          <div
            ref={modalRef}
            tabIndex={-1}
            onMouseDown={(event) => event.stopPropagation()}
            className="w-full max-w-2xl rounded-xl border border-gray-200 bg-white p-6 shadow-xl dark:border-gray-700 dark:bg-gray-800"
          >
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {modalMode === 'create' ? 'Novo usuario' : 'Editar usuario'}
                </h2>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  Admins tem acesso total. Usuarios comuns podem receber abas especificas.
                </p>
              </div>
              <button
                onClick={closeModal}
                aria-label="Fechar modal de usuario"
                className="text-2xl leading-none text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label htmlFor="usuario-username" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Nome de usuario
                  </label>
                  <input
                    id="usuario-username"
                    type="text"
                    value={form.username}
                    onChange={(event) => setForm({ ...form, username: event.target.value })}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="ex: joao.silva"
                    required
                  />
                </div>

                <div>
                  <label htmlFor="usuario-email" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    E-mail
                  </label>
                  <input
                    id="usuario-email"
                    type="email"
                    value={form.email}
                    onChange={(event) => setForm({ ...form, email: event.target.value })}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="usuario@empresa.com"
                    required
                  />
                </div>

                <div>
                  <label htmlFor="usuario-full-name" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Nome completo
                  </label>
                  <input
                    id="usuario-full-name"
                    type="text"
                    value={form.full_name}
                    onChange={(event) => setForm({ ...form, full_name: event.target.value })}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="Joao Silva"
                  />
                </div>

                <div>
                  <label htmlFor="usuario-password" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {modalMode === 'create' ? 'Senha' : 'Nova senha'}
                  </label>
                  <input
                    id="usuario-password"
                    type="password"
                    value={form.password}
                    onChange={(event) => setForm({ ...form, password: event.target.value })}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder={modalMode === 'create' ? 'Defina uma senha' : 'Preencha so se quiser trocar'}
                    minLength={modalMode === 'create' ? 6 : undefined}
                  />
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-5">
                <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    checked={form.is_active}
                    onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  Usuario ativo
                </label>

                <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    checked={form.is_superuser}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        is_superuser: event.target.checked,
                        allowed_tabs: event.target.checked ? [] : form.allowed_tabs,
                      })
                    }
                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    disabled={isEditingSelf}
                  />
                  Administrador (acesso total)
                </label>
              </div>

              <div className="rounded-xl border border-gray-200 p-4 dark:border-gray-700">
                <div className="mb-3">
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Abas liberadas</h3>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    O dashboard fica sempre disponivel. A aba Usuarios continua exclusiva de admins.
                  </p>
                </div>

                {form.is_superuser ? (
                  <div className="rounded-lg bg-blue-50 px-3 py-2 text-sm text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                    Este usuario tera acesso total a todas as areas do sistema.
                  </div>
                ) : (
                  <div className="grid gap-2 md:grid-cols-2">
                    {MANAGEABLE_TABS.map((tab) => (
                      <label
                        key={tab.id}
                        className="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-700 dark:border-gray-700 dark:text-gray-300"
                      >
                        <input
                          type="checkbox"
                          checked={form.allowed_tabs.includes(tab.id)}
                          onChange={() => handleToggleTab(tab.id)}
                          className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        {tab.label}
                      </label>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isMutating}
                  className="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {modalMode === 'create'
                    ? createMutation.isPending
                      ? 'Criando...'
                      : 'Criar usuario'
                    : updateMutation.isPending
                      ? 'Salvando...'
                      : 'Salvar alteracoes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default Usuarios
