import { useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { isAxiosError } from 'axios'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { FileText, Plus } from 'lucide-react'
import toast from 'react-hot-toast'

import api from '../services/api'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

type StatusOrcamento = 'aberto' | 'aprovado' | 'cancelado' | 'convertido'

interface ClienteSugestao {
  id: number
  nome: string
  cpf_cnpj?: string | null
}

interface ProdutoSugestao {
  id: number
  nome: string
  preco_unitario: number
  preco_liquido: number
  unidade_medida?: string | null
}

const FormaPagamento = {
  DINHEIRO: 1,
  CARTAO_DEBITO: 2,
  CARTAO_CREDITO: 3,
  PIX: 4,
  BOLETO: 5,
  PRAZO: 6,
} as const

type FormaPagamentoValue = typeof FormaPagamento[keyof typeof FormaPagamento]

const formaPagamentoLabel: Record<FormaPagamentoValue, string> = {
  1: 'Dinheiro',
  2: 'Cartao Debito',
  3: 'Cartao Credito',
  4: 'PIX',
  5: 'Boleto',
  6: 'A prazo',
}

interface Orcamento {
  id: number
  cliente_id?: number | null
  cliente_nome?: string | null
  status: StatusOrcamento
  desconto_geral: number
  observacao?: string | null
  data_criacao: string
  data_validade?: string | null
  venda_id?: number | null
  itens: Array<{
    id: number
    descricao: string
    quantidade: number
    preco_unitario: number
    desconto: number
    preco_total: number
  }>
  total: number
}

interface OrcamentoListResponse {
  items: Orcamento[]
  total: number
  page: number
  pages: number
}

interface ItemFormState {
  produto_id: number | null
  descricao: string
  quantidade: string
  preco_unitario: string
  desconto: string
}

interface OrcamentoFormState {
  cliente_id: number | null
  cliente_nome: string
  desconto_geral: string
  data_validade: string
  observacao: string
  itens: ItemFormState[]
}

const PAGE_SIZE = 20
const moneyFormatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const textareaClassName =
  'flex min-h-24 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm transition-colors outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'

const statusLabel: Record<StatusOrcamento, string> = {
  aberto: 'Aberto',
  aprovado: 'Aprovado',
  cancelado: 'Cancelado',
  convertido: 'Convertido',
}

const statusBadgeClass: Record<StatusOrcamento, string> = {
  aberto: 'bg-sky-500/10 text-sky-700 dark:text-sky-300',
  aprovado: 'bg-primary/10 text-primary',
  cancelado: 'bg-destructive/10 text-destructive',
  convertido: 'bg-violet-500/10 text-violet-700 dark:text-violet-300',
}

const createEmptyItem = (): ItemFormState => ({
  produto_id: null,
  descricao: '',
  quantidade: '1',
  preco_unitario: '',
  desconto: '0',
})

const createInitialForm = (): OrcamentoFormState => ({
  cliente_id: null,
  cliente_nome: '',
  desconto_geral: '0',
  data_validade: '',
  observacao: '',
  itens: [createEmptyItem()],
})

const Orcamentos = () => {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<'todos' | StatusOrcamento>('todos')
  const [page, setPage] = useState(1)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [formState, setFormState] = useState<OrcamentoFormState>(createInitialForm)
  const [formError, setFormError] = useState('')
  const [clienteSearch, setClienteSearch] = useState('')
  const [showClienteSugestoes, setShowClienteSugestoes] = useState(false)
  const clienteRef = useRef<HTMLDivElement>(null)
  const [produtoSearches, setProdutoSearches] = useState<string[]>([''])
  const [showProdutoSugestoes, setShowProdutoSugestoes] = useState<boolean[]>([false])
  const [activeProdutoIndex, setActiveProdutoIndex] = useState<number | null>(null)
  const [produtoResults, setProdutoResults] = useState<ProdutoSugestao[]>([])
  const produtoSearchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [downloadingPdfId, setDownloadingPdfId] = useState<number | null>(null)
  const [convertModal, setConvertModal] = useState<{ orcamentoId: number } | null>(null)
  const [convertError, setConvertError] = useState('')
  const [convertForm, setConvertForm] = useState<{ forma_pagamento: FormaPagamentoValue; parcelas: number }>({
    forma_pagamento: FormaPagamento.PIX,
    parcelas: 1,
  })

  const clientesQuery = useQuery({
    queryKey: ['clientes-sugestao', clienteSearch],
    queryFn: async () => (await api.get('/clientes/', { params: { search: clienteSearch, limit: 8 } })).data as ClienteSugestao[],
    enabled: isCreateModalOpen && clienteSearch.length >= 1,
  })

  const orcamentosQuery = useQuery({
    queryKey: ['orcamentos', statusFilter, page],
    queryFn: async () =>
      (await api.get('/orcamentos/', { params: { page, page_size: PAGE_SIZE, status: statusFilter === 'todos' ? undefined : statusFilter } })).data as OrcamentoListResponse,
    placeholderData: (previousData) => previousData,
  })

  const createMutation = useMutation({
    mutationFn: async (payload: unknown) => (await api.post('/orcamentos/', payload)).data as Orcamento,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orcamentos'] })
      setIsCreateModalOpen(false)
      setFormState(createInitialForm())
      setFormError('')
      toast.success('Orcamento criado com sucesso!')
    },
    onError: () => setFormError('Nao foi possivel criar o orcamento. Revise os dados e tente novamente.'),
  })

  const cancelMutation = useMutation({
    mutationFn: async (orcamentoId: number) => {
      await api.delete(`/orcamentos/${orcamentoId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orcamentos'] })
      toast.success('Orcamento cancelado com sucesso!')
    },
  })

  const convertMutation = useMutation({
    mutationFn: async ({ orcamentoId, forma_pagamento, parcelas }: { orcamentoId: number; forma_pagamento: FormaPagamentoValue; parcelas: number }) => {
      await api.post(`/orcamentos/${orcamentoId}/converter`, { forma_pagamento, parcelas })
    },
    onError: (error) => {
      let message = 'Nao foi possivel converter o orcamento. Tente novamente.'
      if (isAxiosError(error)) {
        const apiData = error.response?.data as { message?: unknown; detail?: unknown; details?: { produto_nome?: string; disponivel?: number; solicitado?: number } } | undefined
        const detail = apiData?.message ?? apiData?.detail
        if (typeof detail === 'string') {
          if (apiData?.details?.produto_nome) {
            message = `${detail}: ${apiData.details.produto_nome} (disponivel: ${apiData.details.disponivel ?? 0}, solicitado: ${apiData.details.solicitado ?? 0}).`
          } else {
            message = detail
          }
        } else if (Array.isArray(detail)) {
          message =
            detail
              .map((item) => (typeof item === 'string' ? item : (item as { msg?: string })?.msg))
              .filter(Boolean)
              .join(' | ') || 'Nao foi possivel converter o orcamento.'
        }
      }
      setConvertError(message)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orcamentos'] })
      setConvertModal(null)
      setConvertError('')
      toast.success('Orcamento convertido em venda com sucesso!')
    },
  })

  const orcamentos = orcamentosQuery.data?.items ?? []
  const totalPages = Math.max(1, orcamentosQuery.data?.pages ?? 1)
  const totalPreview = useMemo(() => Math.max(0, formState.itens.reduce((total, item) => total + (Number(item.quantidade) || 0) * (Number(item.preco_unitario) || 0) * (1 - (Number(item.desconto) || 0) / 100), 0) - (Number(formState.desconto_geral) || 0)), [formState])

  const buscarProdutos = (search: string, index: number) => {
    if (produtoSearchTimeout.current) clearTimeout(produtoSearchTimeout.current)
    if (!search.trim()) {
      setProdutoResults([])
      return
    }
    produtoSearchTimeout.current = setTimeout(async () => {
      try {
        const response = await api.get('/produtos/', { params: { search: search.trim(), page_size: 8 } })
        setActiveProdutoIndex((current) => {
          if (current === index) setProdutoResults(response.data.items ?? [])
          return current
        })
      } catch {
        setProdutoResults([])
      }
    }, 250)
  }

  const handleOpenModal = () => {
    setFormState(createInitialForm())
    setFormError('')
    setClienteSearch('')
    setShowClienteSugestoes(false)
    setProdutoSearches([''])
    setShowProdutoSugestoes([false])
    setProdutoResults([])
    setActiveProdutoIndex(null)
    setIsCreateModalOpen(true)
  }

  const closeCreateModal = () => {
    if (!createMutation.isPending) setIsCreateModalOpen(false)
  }

  const closeConvertModal = () => {
    if (!convertMutation.isPending) {
      setConvertModal(null)
      setConvertError('')
    }
  }

  const handleCreateSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setFormError('')
    if (!formState.cliente_nome.trim()) return setFormError('Informe o nome do cliente para criar o orcamento.')
    if (formState.itens.some((item) => !item.descricao.trim())) return setFormError('Todos os itens precisam ter descricao.')
    createMutation.mutate({
      cliente_id: formState.cliente_id || null,
      cliente_nome: formState.cliente_nome.trim(),
      desconto_geral: Number(formState.desconto_geral) || 0,
      observacao: formState.observacao.trim() || null,
      data_validade: formState.data_validade || null,
      itens: formState.itens.map((item) => ({
        produto_id: item.produto_id || null,
        descricao: item.descricao.trim(),
        quantidade: Number(item.quantidade) || 0,
        preco_unitario: Number(item.preco_unitario) || 0,
        desconto: Number(item.desconto) || 0,
      })),
    })
  }

  const updateItem = (index: number, field: keyof ItemFormState, value: string) => {
    setFormState((previous) => ({ ...previous, itens: previous.itens.map((item, itemIndex) => (itemIndex === index ? { ...item, [field]: value } : item)) }))
  }

  const addItem = () => {
    setFormState((previous) => ({ ...previous, itens: [...previous.itens, createEmptyItem()] }))
    setProdutoSearches((prev) => [...prev, ''])
    setShowProdutoSugestoes((prev) => [...prev, false])
  }

  const removeItem = (index: number) => {
    if (formState.itens.length === 1) return
    setFormState((previous) => ({ ...previous, itens: previous.itens.filter((_, itemIndex) => itemIndex !== index) }))
    setProdutoSearches((prev) => prev.filter((_, itemIndex) => itemIndex !== index))
    setShowProdutoSugestoes((prev) => prev.filter((_, itemIndex) => itemIndex !== index))
  }

  const selecionarCliente = (cliente: ClienteSugestao) => {
    setFormState((prev) => ({ ...prev, cliente_id: cliente.id, cliente_nome: cliente.nome }))
    setClienteSearch(cliente.nome)
    setShowClienteSugestoes(false)
  }

  const selecionarProduto = (index: number, produto: ProdutoSugestao) => {
    setFormState((prev) => ({ ...prev, itens: prev.itens.map((item, itemIndex) => (itemIndex === index ? { ...item, produto_id: produto.id, descricao: produto.nome, preco_unitario: String(produto.preco_unitario) } : item)) }))
    setProdutoSearches((prev) => prev.map((search, itemIndex) => (itemIndex === index ? produto.nome : search)))
    setShowProdutoSugestoes((prev) => prev.map((current, itemIndex) => (itemIndex === index ? false : current)))
    setActiveProdutoIndex(null)
  }

  const handleExportarPdf = async (orcamento: Orcamento) => {
    setDownloadingPdfId(orcamento.id)
    try {
      const response = await api.get(`/orcamentos/${orcamento.id}/pdf`, { responseType: 'blob' })
      const url = URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
      const link = document.createElement('a')
      link.href = url
      link.download = `orcamento-${String(orcamento.id).padStart(5, '0')}.pdf`
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch {
      toast.error('Erro ao gerar PDF. Tente novamente.')
    } finally {
      setDownloadingPdfId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">Orcamentos</h1>
          <p className="text-sm text-muted-foreground">Gerencie propostas comerciais e converta em venda quando necessario.</p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <Select
            value={statusFilter}
            onValueChange={(value) => {
              setStatusFilter(value as 'todos' | StatusOrcamento)
              setPage(1)
            }}
          >
            <SelectTrigger className="w-full sm:w-[220px]">
              <SelectValue placeholder="Todos os status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="todos">Todos os status</SelectItem>
              <SelectItem value="aberto">Abertos</SelectItem>
              <SelectItem value="aprovado">Aprovados</SelectItem>
              <SelectItem value="cancelado">Cancelados</SelectItem>
              <SelectItem value="convertido">Convertidos</SelectItem>
            </SelectContent>
          </Select>
          <Button type="button" onClick={handleOpenModal}>
            <Plus className="size-4" />
            Novo orcamento
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-1">
              <CardTitle>Lista de orcamentos</CardTitle>
              <CardDescription>Propostas abertas, aprovadas, canceladas ou ja convertidas em venda.</CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">{orcamentosQuery.data?.total ?? 0} registros</Badge>
              <Badge variant="secondary">Pagina {page} de {totalPages}</Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Cliente</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Criacao</TableHead>
                <TableHead>Total</TableHead>
                <TableHead className="text-right">Acoes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {orcamentosQuery.isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="py-10 text-center text-muted-foreground">Carregando orcamentos...</TableCell>
                </TableRow>
              ) : orcamentosQuery.isError ? (
                <TableRow>
                  <TableCell colSpan={6}>
                    <Alert variant="destructive">
                      <AlertTitle>Erro ao buscar orcamentos</AlertTitle>
                      <AlertDescription>Tente novamente em alguns instantes.</AlertDescription>
                    </Alert>
                  </TableCell>
                </TableRow>
              ) : orcamentos.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="py-10 text-center text-muted-foreground">Nenhum orcamento encontrado para o filtro selecionado.</TableCell>
                </TableRow>
              ) : (
                orcamentos.map((orcamento) => (
                  <TableRow key={orcamento.id}>
                    <TableCell className="text-muted-foreground">#{orcamento.id}</TableCell>
                    <TableCell className="font-medium">{orcamento.cliente_nome ?? 'Cliente nao informado'}</TableCell>
                    <TableCell>
                      <Badge variant="secondary" className={statusBadgeClass[orcamento.status]}>
                        {statusLabel[orcamento.status]}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{new Date(orcamento.data_criacao).toLocaleDateString('pt-BR')}</TableCell>
                    <TableCell className="font-medium text-primary">{moneyFormatter.format(orcamento.total)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex flex-wrap justify-end gap-2">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => cancelMutation.mutate(orcamento.id)}
                          disabled={orcamento.status !== 'aberto' || cancelMutation.isPending}
                          className="border-destructive/30 text-destructive hover:bg-destructive/10 hover:text-destructive"
                        >
                          Cancelar
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setConvertForm({ forma_pagamento: FormaPagamento.PIX, parcelas: 1 })
                            setConvertError('')
                            setConvertModal({ orcamentoId: orcamento.id })
                          }}
                          disabled={(orcamento.status !== 'aberto' && orcamento.status !== 'aprovado') || convertMutation.isPending}
                        >
                          Converter
                        </Button>
                        <Button type="button" variant="outline" size="sm" onClick={() => void handleExportarPdf(orcamento)} disabled={downloadingPdfId === orcamento.id}>
                          <FileText className="size-3.5" />
                          {downloadingPdfId === orcamento.id ? 'Gerando...' : 'PDF'}
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>

          <Separator />

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-end">
            <Button type="button" variant="outline" size="sm" onClick={() => setPage((previous) => Math.max(1, previous - 1))} disabled={page === 1}>
              Anterior
            </Button>
            <span className="text-sm text-muted-foreground">Pagina {page} de {totalPages}</span>
            <Button type="button" variant="outline" size="sm" onClick={() => setPage((previous) => Math.min(totalPages, previous + 1))} disabled={page >= totalPages}>
              Proxima
            </Button>
          </div>
        </CardContent>
      </Card>
      <Dialog open={Boolean(convertModal)} onOpenChange={(open) => !open && closeConvertModal()}>
        <DialogContent className="p-0 sm:max-w-md" showCloseButton={false}>
          <DialogHeader className="border-b px-6 py-5">
            <DialogTitle>Converter em venda</DialogTitle>
            <DialogDescription>Defina a forma de pagamento antes da conversao.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 px-6 py-5">
            <div className="space-y-2">
              <Label htmlFor="orcamento-conversao-forma-pagamento">Forma de pagamento</Label>
              <Select
                value={String(convertForm.forma_pagamento)}
                onValueChange={(value) => setConvertForm((prev) => ({ ...prev, forma_pagamento: Number(value) as FormaPagamentoValue }))}
              >
                <SelectTrigger id="orcamento-conversao-forma-pagamento" className="w-full">
                  <SelectValue placeholder="Selecione a forma" />
                </SelectTrigger>
                <SelectContent>
                  {(Object.entries(FormaPagamento) as [string, FormaPagamentoValue][]).map(([, value]) => (
                    <SelectItem key={value} value={String(value)}>
                      {formaPagamentoLabel[value]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {convertForm.forma_pagamento === FormaPagamento.PRAZO && (
              <div className="space-y-2">
                <Label htmlFor="orcamento-conversao-parcelas">Numero de parcelas</Label>
                <Input
                  id="orcamento-conversao-parcelas"
                  type="number"
                  min={1}
                  max={48}
                  value={convertForm.parcelas}
                  onChange={(event) => setConvertForm((prev) => ({ ...prev, parcelas: Math.max(1, Number(event.target.value)) }))}
                />
              </div>
            )}
            {convertError && (
              <Alert variant="destructive">
                <AlertTitle>Falha na conversao</AlertTitle>
                <AlertDescription>{convertError}</AlertDescription>
              </Alert>
            )}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={closeConvertModal}>
              Cancelar
            </Button>
            <Button
              type="button"
              onClick={() => convertModal && convertMutation.mutate({ orcamentoId: convertModal.orcamentoId, ...convertForm })}
              disabled={convertMutation.isPending}
            >
              {convertMutation.isPending ? 'Convertendo...' : 'Confirmar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog open={isCreateModalOpen} onOpenChange={(open) => !open && closeCreateModal()}>
        <DialogContent className="max-h-[92vh] overflow-hidden p-0 sm:max-w-4xl" showCloseButton={false}>
          <DialogHeader className="border-b px-6 py-5">
            <DialogTitle>Novo orcamento</DialogTitle>
            <DialogDescription>Monte a proposta comercial, selecione cliente e adicione os itens desejados.</DialogDescription>
          </DialogHeader>

          <form onSubmit={handleCreateSubmit} className="flex min-h-0 flex-1 flex-col">
            <div className="space-y-5 overflow-y-auto px-6 py-5">
              <Card size="sm">
                <CardHeader>
                  <CardTitle className="text-sm">Cabecalho</CardTitle>
                  <CardDescription>Cliente, validade e dados gerais da proposta.</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2" ref={clienteRef}>
                    <Label htmlFor="orcamento-cliente">Cliente</Label>
                    <div className="relative">
                      <Input
                        id="orcamento-cliente"
                        value={clienteSearch}
                        onChange={(event) => {
                          const value = event.target.value
                          setClienteSearch(value)
                          setFormState((prev) => ({ ...prev, cliente_id: null, cliente_nome: value }))
                          setShowClienteSugestoes(true)
                        }}
                        onFocus={() => {
                          if (clienteSearch) setShowClienteSugestoes(true)
                        }}
                        onBlur={() => setTimeout(() => setShowClienteSugestoes(false), 150)}
                        placeholder="Digite para buscar cliente..."
                      />
                      {showClienteSugestoes && clientesQuery.data && clientesQuery.data.length > 0 && (
                        <ul className="absolute z-50 mt-1 max-h-48 w-full overflow-y-auto rounded-lg border border-border bg-popover shadow-lg">
                          {clientesQuery.data.map((cliente) => (
                            <li key={cliente.id} onMouseDown={() => selecionarCliente(cliente)} className="cursor-pointer px-3 py-2 text-sm hover:bg-muted">
                              <span className="font-medium">{cliente.nome}</span>
                              {cliente.cpf_cnpj && <span className="ml-2 text-xs text-muted-foreground">{cliente.cpf_cnpj}</span>}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                    {formState.cliente_id && <p className="text-xs text-primary">Cliente vinculado (ID {formState.cliente_id})</p>}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="orcamento-validade">Validade</Label>
                    <Input
                      id="orcamento-validade"
                      type="date"
                      value={formState.data_validade}
                      onChange={(event) => setFormState((previous) => ({ ...previous, data_validade: event.target.value }))}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="orcamento-desconto-geral">Desconto geral (R$)</Label>
                    <Input
                      id="orcamento-desconto-geral"
                      type="number"
                      min="0"
                      step="0.01"
                      value={formState.desconto_geral}
                      onChange={(event) => setFormState((previous) => ({ ...previous, desconto_geral: event.target.value }))}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card size="sm">
                <CardHeader>
                  <CardTitle className="text-sm">Observacao</CardTitle>
                </CardHeader>
                <CardContent>
                  <textarea
                    id="orcamento-observacao"
                    value={formState.observacao}
                    onChange={(event) => setFormState((previous) => ({ ...previous, observacao: event.target.value }))}
                    className={textareaClassName}
                    rows={3}
                    placeholder="Informacoes adicionais"
                  />
                </CardContent>
              </Card>

              <Card size="sm">
                <CardHeader className="gap-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-sm">Itens do orcamento</CardTitle>
                      <CardDescription>Busque produtos existentes ou informe a descricao manualmente.</CardDescription>
                    </div>
                    <Button type="button" variant="outline" size="sm" onClick={addItem}>
                      Adicionar item
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {formState.itens.map((item, index) => (
                    <Card size="sm" key={`item-${index}`}>
                      <CardContent className="space-y-3">
                        <div className="flex gap-2">
                          <div className="relative flex-1">
                            <Input
                              id={`orcamento-item-descricao-${index}`}
                              value={produtoSearches[index] ?? ''}
                              onChange={(event) => {
                                const value = event.target.value
                                setProdutoSearches((prev) => prev.map((search, itemIndex) => (itemIndex === index ? value : search)))
                                updateItem(index, 'descricao', value)
                                setFormState((prev) => ({
                                  ...prev,
                                  itens: prev.itens.map((currentItem, itemIndex) => (itemIndex === index ? { ...currentItem, produto_id: null } : currentItem)),
                                }))
                                setActiveProdutoIndex(index)
                                setShowProdutoSugestoes((prev) => prev.map((current, itemIndex) => (itemIndex === index ? true : current)))
                                buscarProdutos(value, index)
                              }}
                              onFocus={() => {
                                setActiveProdutoIndex(index)
                                if ((produtoSearches[index]?.length ?? 0) >= 1) {
                                  setShowProdutoSugestoes((prev) => prev.map((current, itemIndex) => (itemIndex === index ? true : current)))
                                  buscarProdutos(produtoSearches[index] ?? '', index)
                                }
                              }}
                              onBlur={() => setTimeout(() => setShowProdutoSugestoes((prev) => prev.map((current, itemIndex) => (itemIndex === index ? false : current))), 150)}
                              placeholder="Buscar produto ou digitar descricao..."
                            />
                            {showProdutoSugestoes[index] && activeProdutoIndex === index && produtoResults.length > 0 && (
                              <ul className="absolute z-50 mt-1 max-h-48 w-full overflow-y-auto rounded-lg border border-border bg-popover shadow-lg">
                                {produtoResults.map((produto) => (
                                  <li key={produto.id} onMouseDown={() => selecionarProduto(index, produto)} className="cursor-pointer px-3 py-2 text-sm hover:bg-muted">
                                    <span className="font-medium">{produto.nome}</span>
                                    <span className="ml-2 text-xs text-muted-foreground">{moneyFormatter.format(produto.preco_unitario)}</span>
                                    {produto.unidade_medida && <span className="ml-1 text-xs text-muted-foreground">/ {produto.unidade_medida}</span>}
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                          <Button type="button" variant="outline" size="sm" onClick={() => removeItem(index)} disabled={formState.itens.length === 1} aria-label={`Remover item ${index + 1} do orcamento`}>
                            Remover
                          </Button>
                        </div>
                        {item.produto_id && <p className="text-xs text-primary">Produto vinculado</p>}
                        <div className="grid gap-3 sm:grid-cols-3">
                          <div className="space-y-2">
                            <Label htmlFor={`orcamento-item-quantidade-${index}`}>Quantidade</Label>
                            <Input id={`orcamento-item-quantidade-${index}`} type="number" min="0" step="0.01" value={item.quantidade} onChange={(event) => updateItem(index, 'quantidade', event.target.value)} placeholder="Qtd" />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor={`orcamento-item-preco-${index}`}>Preco unitario (R$)</Label>
                            <Input id={`orcamento-item-preco-${index}`} type="number" min="0" step="0.01" value={item.preco_unitario} onChange={(event) => updateItem(index, 'preco_unitario', event.target.value)} placeholder="Preco unitario" />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor={`orcamento-item-desconto-${index}`}>Desconto (%)</Label>
                            <Input id={`orcamento-item-desconto-${index}`} type="number" min="0" max="100" step="0.01" value={item.desconto} onChange={(event) => updateItem(index, 'desconto', event.target.value)} placeholder="Desconto" />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </CardContent>
              </Card>

              <Card size="sm">
                <CardContent className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Total estimado</span>
                  <strong className="text-primary">{moneyFormatter.format(totalPreview)}</strong>
                </CardContent>
              </Card>

              {formError && (
                <Alert variant="destructive">
                  <AlertTitle>Falha ao salvar</AlertTitle>
                  <AlertDescription>{formError}</AlertDescription>
                </Alert>
              )}
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeCreateModal}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Salvando...' : 'Salvar orcamento'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default Orcamentos
