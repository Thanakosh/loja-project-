import { useMemo, useState } from 'react'
import { Pencil, Plus, Search } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import api from '../services/api'
import type { Fornecedor, FornecedorPayload } from '../types/fornecedores'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
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

type ModalMode = 'create' | 'edit'

interface FormState {
  nome: string
  cnpj: string
  email: string
  telefone: string
  contato: string
  endereco: string
  cidade: string
  uf: string
  cep: string
}

const emptyFormState: FormState = {
  nome: '',
  cnpj: '',
  email: '',
  telefone: '',
  contato: '',
  endereco: '',
  cidade: '',
  uf: '',
  cep: '',
}

const normalizePayload = (formData: FormState): FornecedorPayload => {
  const payload: FornecedorPayload = {
    razao_social: formData.nome.trim(),
    cnpj: removeNonDigits(formData.cnpj),
  }

  const email = formData.email.trim()
  const telefone = formData.telefone.trim()
  const nomeFantasia = formData.contato.trim()
  const endereco = formData.endereco.trim()
  const cidade = formData.cidade.trim()
  const uf = formData.uf.trim().toUpperCase()
  const cep = formData.cep.trim()

  if (email) payload.email = email
  if (telefone) payload.telefone = telefone
  if (nomeFantasia) payload.nome_fantasia = nomeFantasia
  if (endereco) payload.endereco = endereco
  if (cidade) payload.cidade = cidade
  if (uf) payload.uf = uf
  if (cep) payload.cep = cep

  return payload
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
          search: searchTerm || undefined,
        },
      })
      return response.data as Fornecedor[]
    },
    placeholderData: (previousData) => previousData,
  })

  const fornecedores = fornecedoresQuery.data ?? []

  const createMutation = useMutation({
    mutationFn: async (payload: FornecedorPayload) => {
      const response = await api.post('/fornecedores/', payload)
      return response.data as Fornecedor
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['fornecedores'] })
      closeModal()
      toast.success('Fornecedor criado com sucesso!')
    },
    onError: () => setFormError('Nao foi possivel criar o fornecedor. Verifique os dados e tente novamente.'),
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: FornecedorPayload }) => {
      const response = await api.put(`/fornecedores/${id}`, payload)
      return response.data as Fornecedor
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['fornecedores'] })
      closeModal()
      toast.success('Fornecedor atualizado com sucesso!')
    },
    onError: () => setFormError('Nao foi possivel atualizar o fornecedor. Verifique os dados e tente novamente.'),
  })

  const isSaving = createMutation.isPending || updateMutation.isPending

  const totalEstimado = useMemo(() => {
    if (fornecedores.length < PAGE_SIZE) return page * PAGE_SIZE + fornecedores.length
    return (page + 2) * PAGE_SIZE
  }, [fornecedores.length, page])

  const totalPages = Math.max(1, Math.ceil(totalEstimado / PAGE_SIZE))

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingFornecedor(null)
    setFormError('')
    setFormState(emptyFormState)
  }

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
      nome: fornecedor.razao_social ?? fornecedor.nome_fantasia ?? '',
      cnpj: formatCnpj(fornecedor.cnpj ?? ''),
      email: fornecedor.email ?? '',
      telefone: fornecedor.telefone ?? '',
      contato: fornecedor.nome_fantasia ?? '',
      endereco: fornecedor.endereco ?? '',
      cidade: fornecedor.cidade ?? '',
      uf: fornecedor.uf ?? '',
      cep: fornecedor.cep ?? '',
    })
    setFormError('')
    setIsModalOpen(true)
  }

  const handleInputChange = (field: keyof FormState, value: string) => {
    if (field === 'cnpj') {
      setFormState((previous) => ({ ...previous, cnpj: formatCnpj(value) }))
      return
    }
    if (field === 'uf') {
      setFormState((previous) => ({ ...previous, uf: value.slice(0, 2).toUpperCase() }))
      return
    }
    setFormState((previous) => ({ ...previous, [field]: value }))
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
      setFormError('O CNPJ deve conter 14 digitos.')
      return
    }

    const payload = normalizePayload(formState)

    if (modalMode === 'create') {
      createMutation.mutate(payload)
      return
    }

    if (!editingFornecedor) {
      setFormError('Fornecedor invalido para edicao.')
      return
    }

    updateMutation.mutate({ id: editingFornecedor.id, payload })
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">Fornecedores</h1>
          <p className="text-sm text-muted-foreground">Mantenha os parceiros comerciais usados em importacao, compras e auditoria fiscal.</p>
        </div>
        <Button type="button" onClick={openCreateModal}>
          <Plus className="size-4" />
          Novo fornecedor
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Busca</CardTitle>
          <CardDescription>Procure por razao social, nome fantasia ou CNPJ.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto]">
          <form
            onSubmit={(event) => {
              event.preventDefault()
              setPage(0)
              setSearchTerm(searchInput.trim())
            }}
            className="contents"
          >
            <div className="relative">
              <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input value={searchInput} onChange={(event) => setSearchInput(event.target.value)} placeholder="Buscar por nome ou CNPJ" className="pl-9" />
            </div>
            <Button type="submit" variant="outline">Buscar</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-1">
              <CardTitle>Lista de fornecedores</CardTitle>
              <CardDescription>{fornecedoresQuery.isFetching && !fornecedoresQuery.isLoading ? 'Atualizando resultados...' : 'Cadastro usado em compras e importacao de notas.'}</CardDescription>
            </div>
            <div className="flex gap-2">
              <Badge variant="outline">Pagina {page + 1} de {totalPages}</Badge>
              <Badge variant="outline">{fornecedores.length} registros</Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Razao social</TableHead>
                <TableHead>CNPJ</TableHead>
                <TableHead>Nome fantasia</TableHead>
                <TableHead className="text-right">Acoes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {fornecedoresQuery.isLoading ? (
                <TableRow><TableCell colSpan={4} className="py-8 text-center text-muted-foreground">Carregando...</TableCell></TableRow>
              ) : fornecedoresQuery.isError ? (
                <TableRow><TableCell colSpan={4}><Alert variant="destructive"><AlertTitle>Erro ao carregar fornecedores</AlertTitle><AlertDescription>Tente novamente em alguns instantes.</AlertDescription></Alert></TableCell></TableRow>
              ) : fornecedores.length === 0 ? (
                <TableRow><TableCell colSpan={4} className="py-8 text-center text-muted-foreground">Nenhum fornecedor encontrado.</TableCell></TableRow>
              ) : (
                fornecedores.map((fornecedor) => (
                  <TableRow key={fornecedor.id}>
                    <TableCell className="font-medium">{fornecedor.razao_social || fornecedor.nome_fantasia || '-'}</TableCell>
                    <TableCell className="text-muted-foreground">{formatCnpj(fornecedor.cnpj || '')}</TableCell>
                    <TableCell className="text-muted-foreground">{fornecedor.nome_fantasia || '-'}</TableCell>
                    <TableCell className="text-right">
                      <Button type="button" variant="outline" size="sm" onClick={() => openEditModal(fornecedor)}>
                        <Pencil className="size-3.5" />
                        Editar
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>

          <Separator />

          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-muted-foreground">Pagina {page + 1} de {totalPages} - mostrando {fornecedores.length} registros</p>
            <div className="flex gap-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setPage((current) => Math.max(0, current - 1))} disabled={page === 0 || fornecedoresQuery.isFetching}>Anterior</Button>
              <Button type="button" variant="outline" size="sm" onClick={() => setPage((current) => current + 1)} disabled={fornecedores.length < PAGE_SIZE || fornecedoresQuery.isFetching}>Proxima</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog open={isModalOpen} onOpenChange={(open) => { if (!open && !isSaving) closeModal() }}>
        <DialogContent className="sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>{modalMode === 'create' ? 'Novo fornecedor' : 'Editar fornecedor'}</DialogTitle>
            <DialogDescription>Cadastro comercial e fiscal do parceiro para compras e importacao.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="fornecedor-nome">Razao social *</Label>
              <Input id="fornecedor-nome" value={formState.nome} onChange={(event) => handleInputChange('nome', event.target.value)} placeholder="Razao social" required />
            </div>

            <div className="space-y-2">
              <Label htmlFor="fornecedor-cnpj">CNPJ *</Label>
              <Input id="fornecedor-cnpj" value={formState.cnpj} onChange={(event) => handleInputChange('cnpj', event.target.value)} placeholder="00.000.000/0000-00" maxLength={18} required />
              <p className="text-xs text-muted-foreground">Digite os 14 digitos do CNPJ.</p>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="fornecedor-telefone">Telefone</Label>
                <Input id="fornecedor-telefone" value={formState.telefone} onChange={(event) => handleInputChange('telefone', event.target.value)} placeholder="(00) 00000-0000" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="fornecedor-contato">Nome fantasia</Label>
                <Input id="fornecedor-contato" value={formState.contato} onChange={(event) => handleInputChange('contato', event.target.value)} placeholder="Nome fantasia" />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="fornecedor-email">E-mail</Label>
              <Input id="fornecedor-email" type="email" value={formState.email} onChange={(event) => handleInputChange('email', event.target.value)} placeholder="contato@fornecedor.com.br" />
            </div>

            <div className="space-y-2">
              <Label htmlFor="fornecedor-endereco">Endereco</Label>
              <Input id="fornecedor-endereco" value={formState.endereco} onChange={(event) => handleInputChange('endereco', event.target.value)} placeholder="Rua, numero" />
            </div>

            <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_100px_140px]">
              <div className="space-y-2">
                <Label htmlFor="fornecedor-cidade">Cidade</Label>
                <Input id="fornecedor-cidade" value={formState.cidade} onChange={(event) => handleInputChange('cidade', event.target.value)} placeholder="Cidade" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="fornecedor-uf">UF</Label>
                <Input id="fornecedor-uf" value={formState.uf} onChange={(event) => handleInputChange('uf', event.target.value)} placeholder="UF" maxLength={2} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="fornecedor-cep">CEP</Label>
                <Input id="fornecedor-cep" value={formState.cep} onChange={(event) => handleInputChange('cep', event.target.value)} placeholder="00000000" />
              </div>
            </div>

            {formError && (
              <Alert variant="destructive">
                <AlertTitle>Falha ao salvar</AlertTitle>
                <AlertDescription>{formError}</AlertDescription>
              </Alert>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeModal} disabled={isSaving}>Cancelar</Button>
              <Button type="submit" disabled={isSaving}>{modalMode === 'create' ? 'Criar fornecedor' : 'Salvar alteracoes'}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default Fornecedores
