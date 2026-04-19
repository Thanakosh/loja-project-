import { useMemo, useState } from 'react'
import { Pencil, Plus, Search } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import api from '../services/api'

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
  codigo_legado: '',
}

const removeNonDigits = (value: string) => value.replace(/\D/g, '')

const normalizeCpfCnpj = (value: string) => {
  const digits = removeNonDigits(value)
  if (!digits) return ''

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
  const payload: ClientePayload = { nome: formState.nome.trim() }
  const cpfCnpj = removeNonDigits(formState.cpf_cnpj)
  const telefone = formState.telefone.trim()
  const cidade = formState.cidade.trim()
  const uf = formState.uf.trim().toUpperCase()
  const codigoLegado = formState.codigo_legado.trim()

  if (cpfCnpj) payload.cpf_cnpj = cpfCnpj
  if (telefone) payload.telefone = telefone
  if (cidade) payload.cidade = cidade
  if (uf) payload.uf = uf
  if (codigoLegado) payload.codigo_legado = Number(codigoLegado)

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
          skip: page * PAGE_SIZE,
        },
      })
      return response.data as Cliente[]
    },
    placeholderData: (previousData) => previousData,
  })

  const clientes = clientesQuery.data ?? []

  const createMutation = useMutation({
    mutationFn: async (payload: ClientePayload) => {
      const response = await api.post('/clientes/', payload)
      return response.data as Cliente
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['clientes'] })
      closeModal()
    },
    onError: () => setFormError('Nao foi possivel criar o cliente. Verifique os dados e tente novamente.'),
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: ClientePayload }) => {
      const response = await api.put(`/clientes/${id}`, payload)
      return response.data as Cliente
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['clientes'] })
      closeModal()
    },
    onError: () => setFormError('Nao foi possivel atualizar o cliente. Verifique os dados e tente novamente.'),
  })

  const isSaving = createMutation.isPending || updateMutation.isPending

  const totalEstimado = useMemo(() => {
    if (clientes.length < PAGE_SIZE) return page * PAGE_SIZE + clientes.length
    return (page + 2) * PAGE_SIZE
  }, [clientes.length, page])

  const totalPages = Math.max(1, Math.ceil(totalEstimado / PAGE_SIZE))

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingCliente(null)
    setFormState(emptyFormState)
    setFormError('')
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
      codigo_legado: cliente.codigo_legado ? String(cliente.codigo_legado) : '',
    })
    setFormError('')
    setIsModalOpen(true)
  }

  const handleInputChange = (field: keyof FormState, value: string) => {
    if (field === 'cpf_cnpj') {
      setFormState((previous) => ({ ...previous, cpf_cnpj: normalizeCpfCnpj(value) }))
      return
    }
    if (field === 'codigo_legado') {
      setFormState((previous) => ({ ...previous, codigo_legado: removeNonDigits(value).slice(0, 10) }))
      return
    }
    if (field === 'uf') {
      setFormState((previous) => ({ ...previous, uf: value.toUpperCase().slice(0, 2) }))
      return
    }

    setFormState((previous) => ({ ...previous, [field]: value }))
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
      setFormError('CPF/CNPJ deve ter 11 ou 14 digitos.')
      return
    }

    const payload = normalizePayload(formState)

    if (modalMode === 'create') {
      createMutation.mutate(payload)
      return
    }

    if (!editingCliente) {
      setFormError('Cliente invalido para edicao.')
      return
    }

    updateMutation.mutate({ id: editingCliente.id, payload })
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">Clientes</h1>
          <p className="text-sm text-muted-foreground">Cadastre e mantenha os clientes para vendas, contas a receber e historico comercial.</p>
        </div>
        <Button type="button" onClick={openCreateModal}>
          <Plus className="size-4" />
          Novo cliente
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Busca</CardTitle>
          <CardDescription>Pesquise por nome ou CPF/CNPJ e navegue pelas paginas do cadastro.</CardDescription>
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
              <Input value={searchInput} onChange={(event) => setSearchInput(event.target.value)} placeholder="Buscar por nome ou CPF/CNPJ" className="pl-9" />
            </div>
            <Button type="submit" variant="outline">Buscar</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-1">
              <CardTitle>Lista de clientes</CardTitle>
              <CardDescription>{clientesQuery.isFetching && !clientesQuery.isLoading ? 'Atualizando resultados...' : 'Visao atual do cadastro.'}</CardDescription>
            </div>
            <div className="flex gap-2">
              <Badge variant="outline">Pagina {page + 1} de {totalPages}</Badge>
              <Badge variant="outline">{clientes.length} registros</Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead>CPF/CNPJ</TableHead>
                <TableHead>Telefone</TableHead>
                <TableHead>Cidade/UF</TableHead>
                <TableHead>Cod. legado</TableHead>
                <TableHead className="text-right">Acoes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {clientesQuery.isLoading ? (
                <TableRow><TableCell colSpan={6} className="py-8 text-center text-muted-foreground">Carregando...</TableCell></TableRow>
              ) : clientesQuery.isError ? (
                <TableRow><TableCell colSpan={6}><Alert variant="destructive"><AlertTitle>Erro ao carregar clientes</AlertTitle><AlertDescription>Tente novamente em alguns instantes.</AlertDescription></Alert></TableCell></TableRow>
              ) : clientes.length === 0 ? (
                <TableRow><TableCell colSpan={6} className="py-8 text-center text-muted-foreground">Nenhum cliente encontrado.</TableCell></TableRow>
              ) : (
                clientes.map((cliente) => (
                  <TableRow key={cliente.id}>
                    <TableCell className="font-medium">{cliente.nome}</TableCell>
                    <TableCell className="text-muted-foreground">{normalizeCpfCnpj(cliente.cpf_cnpj || '') || '-'}</TableCell>
                    <TableCell className="text-muted-foreground">{cliente.telefone || '-'}</TableCell>
                    <TableCell className="text-muted-foreground">{cliente.cidade || '-'} / {cliente.uf || '-'}</TableCell>
                    <TableCell className="text-muted-foreground">{cliente.codigo_legado || '-'}</TableCell>
                    <TableCell className="text-right">
                      <Button type="button" variant="outline" size="sm" onClick={() => openEditModal(cliente)}>
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
            <p className="text-sm text-muted-foreground">Pagina {page + 1} de {totalPages} - mostrando {clientes.length} registros</p>
            <div className="flex gap-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setPage((previous) => previous - 1)} disabled={page === 0 || clientesQuery.isFetching}>Anterior</Button>
              <Button type="button" variant="outline" size="sm" onClick={() => setPage((previous) => previous + 1)} disabled={clientes.length < PAGE_SIZE || clientesQuery.isFetching}>Proxima</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog open={isModalOpen} onOpenChange={(open) => { if (!open && !isSaving) closeModal() }}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>{modalMode === 'create' ? 'Novo cliente' : 'Editar cliente'}</DialogTitle>
            <DialogDescription>Dados usados em vendas, documentos e relacionamento comercial.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="cliente-nome">Nome *</Label>
              <Input id="cliente-nome" value={formState.nome} onChange={(event) => handleInputChange('nome', event.target.value)} placeholder="Nome do cliente" />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="cliente-cpf-cnpj">CPF/CNPJ</Label>
                <Input id="cliente-cpf-cnpj" value={formState.cpf_cnpj} onChange={(event) => handleInputChange('cpf_cnpj', event.target.value)} placeholder="000.000.000-00" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="cliente-telefone">Telefone</Label>
                <Input id="cliente-telefone" value={formState.telefone} onChange={(event) => handleInputChange('telefone', event.target.value)} placeholder="(00) 00000-0000" />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="cliente-cidade">Cidade</Label>
                <Input id="cliente-cidade" value={formState.cidade} onChange={(event) => handleInputChange('cidade', event.target.value)} placeholder="Cidade" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="cliente-uf">UF</Label>
                <Input id="cliente-uf" value={formState.uf} onChange={(event) => handleInputChange('uf', event.target.value)} placeholder="UF" />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="cliente-codigo-legado">Codigo legado</Label>
              <Input id="cliente-codigo-legado" value={formState.codigo_legado} onChange={(event) => handleInputChange('codigo_legado', event.target.value)} placeholder="Sera gerado automaticamente se vazio" disabled={modalMode === 'edit'} />
            </div>

            {formError && (
              <Alert variant="destructive">
                <AlertTitle>Falha ao salvar</AlertTitle>
                <AlertDescription>{formError}</AlertDescription>
              </Alert>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeModal} disabled={isSaving}>Cancelar</Button>
              <Button type="submit" disabled={isSaving}>{modalMode === 'create' ? 'Criar cliente' : 'Salvar alteracoes'}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default Clientes
