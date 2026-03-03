import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import type { AxiosError } from 'axios'

import api from '../services/api'

interface Usuario {
  id: number
  username: string | null
  full_name: string | null
  email: string
  is_active: boolean
  is_superuser: boolean
}

interface UsuarioPayload {
  username: string
  full_name: string
  email: string
  password: string
  is_superuser: boolean
}

const emptyForm: UsuarioPayload = {
  username: '',
  full_name: '',
  email: '',
  password: '',
  is_superuser: false,
}

const Usuarios = () => {
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState<UsuarioPayload>(emptyForm)

  const { data, isLoading, isError } = useQuery<{ users: Usuario[]; total: number }>({
    queryKey: ['usuarios'],
    queryFn: () => api.get('/users/').then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: (payload: UsuarioPayload) => api.post('/users/register', payload),
    onSuccess: () => {
      toast.success('Usuário criado com sucesso!')
      queryClient.invalidateQueries({ queryKey: ['usuarios'] })
      setShowModal(false)
      setForm(emptyForm)
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      const detail = error?.response?.data?.detail
      toast.error(detail ?? 'Erro ao criar usuário.')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.username.trim()) {
      toast.error('Nome de usuário é obrigatório.')
      return
    }
    createMutation.mutate(form)
  }

  const usuarios = data?.users ?? []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Usuários</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Gerencie os usuários do sistema
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
        >
          + Novo Usuário
        </button>
      </div>

      {/* Tabela */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden border border-gray-200 dark:border-gray-700">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : isError ? (
          <div className="p-8 text-center text-red-500">Erro ao carregar usuários.</div>
        ) : usuarios.length === 0 ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">Nenhum usuário cadastrado.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
                  <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">#</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Usuário</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Nome completo</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">E-mail</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Status</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Perfil</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {usuarios.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{u.id}</td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">
                      {u.username ?? <span className="text-gray-400 italic text-xs">sem username</span>}
                    </td>
                    <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{u.full_name ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{u.email}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          u.is_active
                            ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400'
                            : 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400'
                        }`}
                      >
                        {u.is_active ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          u.is_superuser
                            ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-400'
                            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                        }`}
                      >
                        {u.is_superuser ? 'Admin' : 'Usuário'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal Criar Usuário */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="w-full max-w-md bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Novo Usuário</h2>
              <button
                onClick={() => { setShowModal(false); setForm(emptyForm) }}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-2xl leading-none"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nome de usuário <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-white text-sm outline-none focus:ring-2 focus:ring-blue-500 placeholder:text-gray-400"
                  placeholder="ex: joao.silva"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nome completo
                </label>
                <input
                  type="text"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-white text-sm outline-none focus:ring-2 focus:ring-blue-500 placeholder:text-gray-400"
                  placeholder="João Silva"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  E-mail <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-white text-sm outline-none focus:ring-2 focus:ring-blue-500 placeholder:text-gray-400"
                  placeholder="joao@empresa.com"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Senha <span className="text-red-500">*</span>
                </label>
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-white text-sm outline-none focus:ring-2 focus:ring-blue-500 placeholder:text-gray-400"
                  placeholder="••••••••"
                  required
                  minLength={6}
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  id="is_superuser"
                  type="checkbox"
                  checked={form.is_superuser}
                  onChange={(e) => setForm({ ...form, is_superuser: e.target.checked })}
                  className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="is_superuser" className="text-sm text-gray-700 dark:text-gray-300">
                  Administrador (acesso total)
                </label>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => { setShowModal(false); setForm(emptyForm) }}
                  className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="flex-1 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
                >
                  {createMutation.isPending ? 'Criando...' : 'Criar usuário'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Usuarios
