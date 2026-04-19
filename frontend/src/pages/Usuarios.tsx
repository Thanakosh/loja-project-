import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { AxiosError } from 'axios'
import { Pencil, Plus, ShieldCheck, Trash2, UserRound } from 'lucide-react'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'

import { MANAGEABLE_TABS, getTabLabel, type AppTabId } from '../config/appTabs'
import { useAuthContext, type AuthenticatedUser } from '../contexts/AuthContext'
import api from '../services/api'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

type ModalMode = 'create' | 'edit'
type Usuario = AuthenticatedUser

type PendingAction =
  | { type: 'toggle-status'; usuario: Usuario }
  | { type: 'delete'; usuario: Usuario }
  | null

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

const checkboxClassName =
  'h-4 w-4 rounded border border-border bg-background text-primary accent-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50'

const toFormState = (user: Usuario): UsuarioPayload => ({
  username: user.username ?? '',
  full_name: user.full_name ?? '',
  email: user.email,
  password: '',
  is_active: user.is_active,
  is_superuser: user.is_superuser,
  allowed_tabs: user.allowed_tabs ?? [],
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

const accessSummary = (usuario: Usuario) => {
  if (usuario.is_superuser) return 'Acesso total'
  if (!usuario.allowed_tabs || usuario.allowed_tabs.length === 0) return 'Somente dashboard'
  return usuario.allowed_tabs.map((tabId) => getTabLabel(tabId)).join(', ')
}

const Usuarios = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { logout, refreshUser, user: currentUser } = useAuthContext()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<ModalMode>('create')
  const [editingUserId, setEditingUserId] = useState<number | null>(null)
  const [form, setForm] = useState<UsuarioPayload>(emptyForm)
  const [pendingAction, setPendingAction] = useState<PendingAction>(null)

  const closeModal = () => {
    setIsModalOpen(false)
    setModalMode('create')
    setEditingUserId(null)
    setForm(emptyForm)
  }

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
    onError: (error: AxiosError<{ detail?: string }>) => toast.error(getErrorMessage(error)),
  })

  const updateMutation = useMutation({
    mutationFn: ({ userId, payload }: { userId: number; payload: UsuarioPayload }) => api.put(`/users/${userId}`, payload),
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
    onError: (error: AxiosError<{ detail?: string }>) => toast.error(getErrorMessage(error)),
  })

  const deleteMutation = useMutation({
    mutationFn: (userId: number) => api.delete(`/users/${userId}`),
    onSuccess: async () => {
      toast.success('Usuario excluido com sucesso.')
      await queryClient.invalidateQueries({ queryKey: ['usuarios'] })
    },
    onError: (error: AxiosError<{ detail?: string }>) => toast.error(getErrorMessage(error)),
  })

  const usuarios = data?.users ?? []
  const stats = {
    total: usuarios.length,
    ativos: usuarios.filter((usuario) => usuario.is_active).length,
    admins: usuarios.filter((usuario) => usuario.is_superuser).length,
  }

  const isSaving = createMutation.isPending || updateMutation.isPending
  const isBusy = isSaving || deleteMutation.isPending
  const isEditingSelf = modalMode === 'edit' && editingUserId === currentUser?.id

  const openCreateModal = () => {
    setModalMode('create')
    setEditingUserId(null)
    setForm(emptyForm)
    setIsModalOpen(true)
  }

  const openEditModal = (usuario: Usuario) => {
    setModalMode('edit')
    setEditingUserId(usuario.id)
    setForm(toFormState(usuario))
    setIsModalOpen(true)
  }

  const handleToggleTab = (tabId: AppTabId) => {
    setForm((currentForm) => {
      if (currentForm.allowed_tabs.includes(tabId)) {
        return { ...currentForm, allowed_tabs: currentForm.allowed_tabs.filter((item) => item !== tabId) }
      }
      return { ...currentForm, allowed_tabs: [...currentForm.allowed_tabs, tabId] }
    })
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

  const confirmPendingAction = () => {
    if (!pendingAction) return

    if (pendingAction.type === 'toggle-status') {
      const usuario = pendingAction.usuario
      updateMutation.mutate({
        userId: usuario.id,
        payload: {
          ...toFormState(usuario),
          is_active: !usuario.is_active,
          password: '',
        },
      })
      setPendingAction(null)
      return
    }

    deleteMutation.mutate(pendingAction.usuario.id, {
      onSettled: () => setPendingAction(null),
    })
  }

  return (
    <div className="space-y-6">
      <AlertDialog open={pendingAction !== null} onOpenChange={(open) => !open && setPendingAction(null)}>
        <AlertDialogContent size="default">
          <AlertDialogHeader>
            <AlertDialogTitle>
              {pendingAction?.type === 'delete' ? 'Excluir usuario' : 'Alterar status do usuario'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {pendingAction?.type === 'delete'
                ? `Excluir permanentemente ${pendingAction.usuario.username ?? pendingAction.usuario.email}? Essa acao nao pode ser desfeita.`
                : pendingAction
                  ? `${pendingAction.usuario.is_active ? 'Desativar' : 'Reativar'} ${pendingAction.usuario.username ?? pendingAction.usuario.email}?`
                  : 'Confirme a acao desejada.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isBusy}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              disabled={isBusy}
              variant={pendingAction?.type === 'delete' ? 'destructive' : 'default'}
              onClick={confirmPendingAction}
            >
              {pendingAction?.type === 'delete' ? 'Excluir' : 'Confirmar'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">Usuarios</h1>
          <p className="text-sm text-muted-foreground">
            Edite perfil, status de acesso e abas liberadas para cada conta.
          </p>
        </div>
        <Button type="button" onClick={openCreateModal}>
          <Plus className="size-4" />
          Novo usuario
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card size="sm">
          <CardHeader>
            <CardDescription>Total de contas</CardDescription>
            <CardTitle>{stats.total}</CardTitle>
          </CardHeader>
        </Card>
        <Card size="sm">
          <CardHeader>
            <CardDescription>Usuarios ativos</CardDescription>
            <CardTitle>{stats.ativos}</CardTitle>
          </CardHeader>
        </Card>
        <Card size="sm">
          <CardHeader>
            <CardDescription>Administradores</CardDescription>
            <CardTitle>{stats.admins}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-1">
              <CardTitle>Contas cadastradas</CardTitle>
              <CardDescription>Usuarios comuns recebem acesso por abas. Administradores mantem acesso total.</CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">{stats.total} usuarios</Badge>
              {stats.admins > 0 && <Badge variant="secondary">{stats.admins} admins</Badge>}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Usuario</TableHead>
                <TableHead>Nome</TableHead>
                <TableHead>E-mail</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Perfil</TableHead>
                <TableHead>Abas</TableHead>
                <TableHead className="text-right">Acoes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-10 text-center text-muted-foreground">
                    Carregando usuarios...
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={7}>
                    <Alert variant="destructive">
                      <AlertTitle>Erro ao carregar usuarios</AlertTitle>
                      <AlertDescription>Tente novamente em alguns instantes.</AlertDescription>
                    </Alert>
                  </TableCell>
                </TableRow>
              ) : usuarios.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-10 text-center text-muted-foreground">
                    Nenhum usuario cadastrado.
                  </TableCell>
                </TableRow>
              ) : (
                usuarios.map((usuario) => {
                  const isSelf = usuario.id === currentUser?.id

                  return (
                    <TableRow key={usuario.id}>
                      <TableCell>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-medium">{usuario.username ?? usuario.email}</span>
                          {isSelf && <Badge variant="secondary">Voce</Badge>}
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{usuario.full_name || '-'}</TableCell>
                      <TableCell className="text-muted-foreground">{usuario.email}</TableCell>
                      <TableCell>
                        <Badge
                          variant={usuario.is_active ? 'secondary' : 'outline'}
                          className={usuario.is_active ? 'bg-primary/10 text-primary' : 'text-muted-foreground'}
                        >
                          {usuario.is_active ? 'Ativo' : 'Inativo'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={usuario.is_superuser ? 'secondary' : 'outline'}>
                          {usuario.is_superuser ? 'Administrador' : 'Usuario'}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-sm text-muted-foreground">{accessSummary(usuario)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex flex-wrap justify-end gap-2">
                          <Button type="button" variant="outline" size="sm" onClick={() => openEditModal(usuario)}>
                            <Pencil className="size-3.5" />
                            Editar
                          </Button>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => setPendingAction({ type: 'toggle-status', usuario })}
                            disabled={isSelf || isBusy}
                          >
                            {usuario.is_active ? 'Desativar' : 'Reativar'}
                          </Button>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            className="border-destructive/30 text-destructive hover:bg-destructive/10 hover:text-destructive"
                            onClick={() => setPendingAction({ type: 'delete', usuario })}
                            disabled={isSelf || isBusy}
                          >
                            <Trash2 className="size-3.5" />
                            Excluir
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={isModalOpen} onOpenChange={(open) => !open && !isSaving && closeModal()}>
        <DialogContent
          className="max-h-[90vh] overflow-hidden p-0 sm:max-w-4xl"
          onEscapeKeyDown={(event) => {
            if (isSaving) event.preventDefault()
          }}
          onInteractOutside={(event) => {
            if (isSaving) event.preventDefault()
          }}
        >
          <DialogHeader className="border-b px-6 py-5">
            <DialogTitle>{modalMode === 'create' ? 'Novo usuario' : 'Editar usuario'}</DialogTitle>
            <DialogDescription>
              Administradores recebem acesso integral. Usuarios comuns acessam apenas as abas liberadas.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col">
            <div className="flex-1 space-y-5 overflow-y-auto px-6 py-5">
              {isEditingSelf && (
                <Alert>
                  <ShieldCheck className="size-4" />
                  <AlertTitle>Conta atual em edicao</AlertTitle>
                  <AlertDescription>
                    Alteracoes de e-mail ou senha podem exigir novo login para continuar.
                  </AlertDescription>
                </Alert>
              )}

              <Card size="sm">
                <CardHeader>
                  <CardTitle className="text-sm">Credenciais e perfil</CardTitle>
                  <CardDescription>Dados principais usados para autenticacao e identificacao.</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="usuario-username">Nome de usuario *</Label>
                    <Input
                      id="usuario-username"
                      value={form.username}
                      onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))}
                      placeholder="ex: joao.silva"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="usuario-email">E-mail *</Label>
                    <Input
                      id="usuario-email"
                      type="email"
                      value={form.email}
                      onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
                      placeholder="usuario@empresa.com"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="usuario-full-name">Nome completo</Label>
                    <Input
                      id="usuario-full-name"
                      value={form.full_name}
                      onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))}
                      placeholder="Nome exibido no sistema"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="usuario-password">{modalMode === 'create' ? 'Senha *' : 'Nova senha'}</Label>
                    <Input
                      id="usuario-password"
                      type="password"
                      minLength={modalMode === 'create' ? 6 : undefined}
                      value={form.password}
                      onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
                      placeholder={modalMode === 'create' ? 'Defina uma senha' : 'Preencha apenas para alterar'}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card size="sm">
                <CardHeader>
                  <CardTitle className="text-sm">Permissoes</CardTitle>
                  <CardDescription>Controle status da conta, perfil administrativo e abas acessiveis.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                    <label className="flex items-center gap-3 rounded-lg border border-border px-3 py-2 text-sm">
                      <input
                        type="checkbox"
                        checked={form.is_active}
                        onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
                        className={checkboxClassName}
                      />
                      Conta ativa
                    </label>
                    <label className="flex items-center gap-3 rounded-lg border border-border px-3 py-2 text-sm">
                      <input
                        type="checkbox"
                        checked={form.is_superuser}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            is_superuser: event.target.checked,
                            allowed_tabs: event.target.checked ? [] : current.allowed_tabs,
                          }))
                        }
                        className={checkboxClassName}
                        disabled={isEditingSelf}
                      />
                      Acesso administrativo total
                    </label>
                  </div>

                  <Separator />

                  {form.is_superuser ? (
                    <Alert>
                      <UserRound className="size-4" />
                      <AlertTitle>Acesso completo</AlertTitle>
                      <AlertDescription>Esta conta tera acesso liberado a todas as areas do sistema.</AlertDescription>
                    </Alert>
                  ) : (
                    <div className="space-y-3">
                      <div className="space-y-1">
                        <h3 className="text-sm font-medium">Abas liberadas</h3>
                        <p className="text-sm text-muted-foreground">
                          O dashboard permanece disponivel mesmo quando nenhuma aba adicional estiver marcada.
                        </p>
                      </div>
                      <div className="grid gap-2 md:grid-cols-2">
                        {MANAGEABLE_TABS.map((tab) => (
                          <label
                            key={tab.id}
                            className="flex items-center gap-3 rounded-lg border border-border px-3 py-2 text-sm"
                          >
                            <input
                              type="checkbox"
                              checked={form.allowed_tabs.includes(tab.id)}
                              onChange={() => handleToggleTab(tab.id)}
                              className={checkboxClassName}
                            />
                            {tab.label}
                          </label>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeModal} disabled={isSaving}>
                Cancelar
              </Button>
              <Button type="submit" disabled={isSaving}>
                {modalMode === 'create'
                  ? createMutation.isPending
                    ? 'Criando...'
                    : 'Criar usuario'
                  : updateMutation.isPending
                    ? 'Salvando...'
                    : 'Salvar alteracoes'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default Usuarios
