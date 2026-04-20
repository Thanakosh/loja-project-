import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import api from '../services/api'
import type {
  BaixaContaReceberPayload,
  ContaReceber,
  ContaReceberListResponse,
  ContaReceberResumo,
} from '../types/contasReceber'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const checkboxClassName =
  'h-4 w-4 rounded border border-border bg-background text-primary accent-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50'

export default function ContasReceber() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [pageSize] = useState(50)
  const [apenasEmAberto, setApenasEmAberto] = useState(false)
  const [vencidas, setVencidas] = useState(false)
  const [clienteId, setClienteId] = useState('')
  const [clienteNome, setClienteNome] = useState('')
  const [activeFilters, setActiveFilters] = useState({
    apenasEmAberto: false,
    vencidas: false,
    clienteId: '',
    clienteNome: '',
  })
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false)
  const [isBaixaModalOpen, setIsBaixaModalOpen] = useState(false)
  const [selectedConta, setSelectedConta] = useState<ContaReceber | null>(null)
  const [formData, setFormData] = useState({
    data_pagamento: new Date().toISOString().split('T')[0],
    valor_pago: 0,
    desconto: 0,
    juros: 0,
    historico: '',
  })

  const closeModals = () => {
    setIsDetailsModalOpen(false)
    setIsBaixaModalOpen(false)
    setSelectedConta(null)
  }

  const baixaMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: BaixaContaReceberPayload }) => {
      const response = await api.put(`/contas-receber/${id}/baixar`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contas-receber'] })
      queryClient.invalidateQueries({ queryKey: ['contas-receber-resumo'] })
      closeModals()
      toast.success('Conta baixada com sucesso!')
    },
    onError: (error) => {
      console.error('Erro ao baixar conta:', error)
      toast.error('Ocorreu um erro ao baixar a conta.')
    },
  })

  const { data: contasResponse, isLoading, isError } = useQuery<ContaReceberListResponse>({
    queryKey: ['contas-receber', page, pageSize, activeFilters],
    queryFn: async () => {
      const params = new URLSearchParams()
      params.append('page', page.toString())
      params.append('page_size', pageSize.toString())
      if (activeFilters.apenasEmAberto) params.append('apenas_em_aberto', 'true')
      if (activeFilters.vencidas) params.append('vencidas', 'true')
      if (activeFilters.clienteId) params.append('cliente_id', activeFilters.clienteId)
      if (activeFilters.clienteNome) params.append('cliente_nome', activeFilters.clienteNome)

      const response = await api.get(`/contas-receber/?${params.toString()}`)
      return response.data
    },
  })

  const { data: resumo } = useQuery<ContaReceberResumo>({
    queryKey: ['contas-receber-resumo'],
    queryFn: async () => {
      const response = await api.get('/contas-receber/resumo')
      return response.data
    },
  })

  const stats = {
    totalEmAberto: resumo?.total_em_aberto ?? 0,
    totalVencido: resumo?.total_vencido ?? 0,
    qtdEmAberto: resumo?.quantidade_em_aberto ?? 0,
  }

  const contas = contasResponse?.items ?? []

  const handleFilter = () => {
    setPage(1)
    setActiveFilters({ apenasEmAberto, vencidas, clienteId, clienteNome })
  }

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-'
    const [year, month, day] = dateString.split('-')
    return `${day}/${month}/${year}`
  }

  const formatParcela = (conta: ContaReceber) => {
    const totalParcelas = conta.total_parcelas && conta.total_parcelas > 0 ? conta.total_parcelas : conta.parcela
    return `${conta.parcela}/${totalParcelas}`
  }

  const formatCliente = (conta: ContaReceber) => {
    if (conta.cliente_nome && conta.cliente_id) return `${conta.cliente_nome} (#${conta.cliente_id})`
    if (conta.cliente_nome) return conta.cliente_nome
    if (conta.cliente_id) return `Cliente #${conta.cliente_id}`
    return '-'
  }

  const getStatusConfig = (conta: ContaReceber) => {
    if (conta.situacao === 'quitada') return { label: 'Quitada', className: 'bg-primary/10 text-primary' }

    if (conta.situacao === 'parcial') {
      if (conta.data_vencimento) {
        const hoje = new Date()
        hoje.setHours(0, 0, 0, 0)
        const vencimento = new Date(conta.data_vencimento)
        if (vencimento < hoje) return { label: 'Parcial vencida', className: 'bg-amber-500/10 text-amber-700 dark:text-amber-300' }
      }
      return { label: 'Parcial', className: 'bg-sky-500/10 text-sky-700 dark:text-sky-300' }
    }

    if (conta.situacao === 'aberta') {
      if (conta.data_vencimento) {
        const hoje = new Date()
        hoje.setHours(0, 0, 0, 0)
        const vencimento = new Date(conta.data_vencimento)
        if (vencimento < hoje) return { label: 'Vencido', className: 'bg-destructive/10 text-destructive' }
      }
      return { label: 'A vencer', className: 'bg-amber-500/10 text-amber-700 dark:text-amber-300' }
    }

    return { label: 'Indefinido', className: 'text-muted-foreground' }
  }

  const summaryBadges = useMemo(() => {
    const badges: string[] = []
    if (activeFilters.apenasEmAberto) badges.push('Apenas em aberto')
    if (activeFilters.vencidas) badges.push('Apenas vencidas')
    if (activeFilters.clienteId) badges.push(`Cliente ID: ${activeFilters.clienteId}`)
    if (activeFilters.clienteNome) badges.push(`Cliente: ${activeFilters.clienteNome}`)
    return badges
  }, [activeFilters])

  const openDetailsModal = (conta: ContaReceber) => {
    setSelectedConta(conta)
    setIsDetailsModalOpen(true)
    setIsBaixaModalOpen(false)
  }

  const openBaixaModal = (conta: ContaReceber) => {
    setSelectedConta(conta)
    setIsDetailsModalOpen(false)
    setFormData({
      data_pagamento: new Date().toISOString().split('T')[0],
      valor_pago: conta.saldo_em_aberto,
      desconto: 0,
      juros: 0,
      historico: '',
    })
    setIsBaixaModalOpen(true)
  }

  const handleBaixaSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    if (!selectedConta) return

    baixaMutation.mutate({
      id: selectedConta.id,
      data: {
        data_pagamento: formData.data_pagamento,
        valor_pago: Number(formData.valor_pago),
        desconto: Number(formData.desconto),
        juros: Number(formData.juros),
        historico: formData.historico || null,
      },
    })
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold">Contas a receber</h1>
        <p className="text-sm text-muted-foreground">Acompanhe titulos em aberto, parcelas vencidas e baixas realizadas.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card size="sm">
          <CardHeader>
            <CardDescription>Total em aberto</CardDescription>
            <CardTitle>{formatCurrency(stats.totalEmAberto)}</CardTitle>
          </CardHeader>
        </Card>
        <Card size="sm">
          <CardHeader>
            <CardDescription>Total vencido</CardDescription>
            <CardTitle>{formatCurrency(stats.totalVencido)}</CardTitle>
          </CardHeader>
        </Card>
        <Card size="sm">
          <CardHeader>
            <CardDescription>Qtd em aberto</CardDescription>
            <CardTitle>{stats.qtdEmAberto}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-1">
              <CardTitle>Filtros</CardTitle>
              <CardDescription>Refine a busca por cliente e status financeiro.</CardDescription>
            </div>
            {summaryBadges.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {summaryBadges.map((badge) => (
                  <Badge key={badge} variant="secondary">{badge}</Badge>
                ))}
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-[180px_220px_auto_auto_auto]">
            <div className="space-y-2">
              <Label htmlFor="contas-cliente-id">ID do cliente</Label>
              <Input id="contas-cliente-id" type="number" placeholder="Ex: 123" value={clienteId} onChange={(event) => setClienteId(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="contas-cliente-nome">Nome do cliente</Label>
              <Input id="contas-cliente-nome" placeholder="Ex: Maria" value={clienteNome} onChange={(event) => setClienteNome(event.target.value)} />
            </div>
            <label className="flex items-center gap-3 rounded-lg border border-border px-3 py-2 text-sm">
              <input type="checkbox" checked={apenasEmAberto} onChange={(event) => setApenasEmAberto(event.target.checked)} className={checkboxClassName} />
              Apenas em aberto
            </label>
            <label className="flex items-center gap-3 rounded-lg border border-border px-3 py-2 text-sm">
              <input type="checkbox" checked={vencidas} onChange={(event) => setVencidas(event.target.checked)} className={checkboxClassName} />
              Apenas vencidas
            </label>
            <div className="flex items-end">
              <Button type="button" onClick={handleFilter}>Filtrar</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-1">
              <CardTitle>Titulos encontrados</CardTitle>
              <CardDescription>Documentos, parcelas, saldos e acoes de baixa disponiveis.</CardDescription>
            </div>
            <Badge variant="outline">Pagina {contasResponse?.page ?? page} de {contasResponse?.pages ?? 1}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Documento</TableHead>
                <TableHead>Parcela</TableHead>
                <TableHead>Cliente</TableHead>
                <TableHead>Emissao</TableHead>
                <TableHead>Vencimento</TableHead>
                <TableHead>Valor</TableHead>
                <TableHead>Pago acum.</TableHead>
                <TableHead>Saldo</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Acoes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={10} className="py-10 text-center text-muted-foreground">Carregando contas...</TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={10}>
                    <Alert variant="destructive">
                      <AlertTitle>Erro ao carregar contas a receber</AlertTitle>
                      <AlertDescription>Tente novamente em alguns instantes.</AlertDescription>
                    </Alert>
                  </TableCell>
                </TableRow>
              ) : contas.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} className="py-10 text-center text-muted-foreground">Nenhuma conta encontrada.</TableCell>
                </TableRow>
              ) : (
                contas.map((conta) => {
                  const status = getStatusConfig(conta)

                  return (
                    <TableRow key={conta.id}>
                      <TableCell className="font-medium">{conta.documento}</TableCell>
                      <TableCell className="text-muted-foreground">{formatParcela(conta)}</TableCell>
                      <TableCell className="text-muted-foreground">{formatCliente(conta)}</TableCell>
                      <TableCell>{formatDate(conta.data_emissao)}</TableCell>
                      <TableCell>{formatDate(conta.data_vencimento)}</TableCell>
                      <TableCell>{formatCurrency(conta.valor)}</TableCell>
                      <TableCell className="text-primary">{formatCurrency(conta.valor_pago)}</TableCell>
                      <TableCell className="text-amber-700 dark:text-amber-300">{formatCurrency(conta.saldo_em_aberto)}</TableCell>
                      <TableCell>
                        <Badge variant="secondary" className={status.className}>{status.label}</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex flex-wrap justify-end gap-2">
                          <Button type="button" variant="outline" size="sm" onClick={() => openDetailsModal(conta)}>Detalhes</Button>
                          {conta.em_aberto && (
                            <Button type="button" size="sm" onClick={() => openBaixaModal(conta)}>Baixar</Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>

          <Separator />

          <div className="flex items-center justify-between">
            <Button type="button" variant="outline" size="sm" onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}>
              Anterior
            </Button>
            <span className="text-sm text-muted-foreground">
              Mostrando pagina {contasResponse?.page ?? page} de {contasResponse?.pages ?? 1}
            </span>
            <Button type="button" variant="outline" size="sm" onClick={() => setPage(page + 1)} disabled={!contasResponse || page >= contasResponse.pages}>
              Proxima
            </Button>
          </div>
        </CardContent>
      </Card>

      <Dialog open={isDetailsModalOpen && selectedConta !== null} onOpenChange={(open) => !open && closeModals()}>
        <DialogContent className="max-h-[90vh] overflow-hidden p-0 sm:max-w-4xl" showCloseButton={false}>
          <DialogHeader className="border-b px-6 py-5">
            <DialogTitle>Detalhes da conta</DialogTitle>
            <DialogDescription>
              Documento {selectedConta?.documento} - Parcela {selectedConta ? formatParcela(selectedConta) : '-'}
            </DialogDescription>
          </DialogHeader>

          {selectedConta && (
            <>
              <div className="grid gap-4 overflow-y-auto px-6 py-5 md:grid-cols-2">
                <Card size="sm">
                  <CardHeader>
                    <CardTitle className="text-sm">Referencia</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <p className="text-xs text-muted-foreground">Cliente</p>
                      <p className="text-sm font-medium">{formatCliente(selectedConta)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Historico</p>
                      <p className="text-sm font-medium">{selectedConta.historico || 'Sem historico'}</p>
                    </div>
                  </CardContent>
                </Card>

                <Card size="sm">
                  <CardHeader>
                    <CardTitle className="text-sm">Datas</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <p className="text-xs text-muted-foreground">Emissao</p>
                      <p className="text-sm font-medium">{formatDate(selectedConta.data_emissao)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Vencimento</p>
                      <p className="text-sm font-medium">{formatDate(selectedConta.data_vencimento)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Pagamento</p>
                      <p className="text-sm font-medium">{formatDate(selectedConta.data_pagamento)}</p>
                    </div>
                  </CardContent>
                </Card>

                <Card size="sm">
                  <CardHeader>
                    <CardTitle className="text-sm">Valores</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <p className="text-xs text-muted-foreground">Valor original</p>
                      <p className="text-sm font-medium">{formatCurrency(selectedConta.valor)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Pago acumulado</p>
                      <p className="text-sm font-medium">{formatCurrency(selectedConta.valor_pago)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Saldo em aberto</p>
                      <p className="text-sm font-medium">{formatCurrency(selectedConta.saldo_em_aberto)}</p>
                    </div>
                  </CardContent>
                </Card>

                <Card size="sm">
                  <CardHeader>
                    <CardTitle className="text-sm">Ajustes</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <p className="text-xs text-muted-foreground">Desconto</p>
                      <p className="text-sm font-medium">{formatCurrency(selectedConta.desconto)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Juros</p>
                      <p className="text-sm font-medium">{formatCurrency(selectedConta.juros)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Status</p>
                      <div className="pt-1">
                        <Badge variant="secondary" className={getStatusConfig(selectedConta).className}>
                          {getStatusConfig(selectedConta).label}
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <DialogFooter>
                {selectedConta.em_aberto && (
                  <Button type="button" onClick={() => openBaixaModal(selectedConta)}>
                    Baixar conta
                  </Button>
                )}
                <Button type="button" variant="outline" onClick={closeModals}>
                  Fechar
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={isBaixaModalOpen && selectedConta !== null} onOpenChange={(open) => !open && closeModals()}>
        <DialogContent className="max-h-[90vh] overflow-hidden p-0 sm:max-w-lg" showCloseButton={false}>
          <DialogHeader className="border-b px-6 py-5">
            <DialogTitle>Registrar recebimento</DialogTitle>
            <DialogDescription>
              Doc {selectedConta?.documento} / Parc {selectedConta ? formatParcela(selectedConta) : '-'}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleBaixaSubmit} className="flex min-h-0 flex-1 flex-col">
            <div className="space-y-4 overflow-y-auto px-6 py-5">
              <div className="space-y-2">
                <Label htmlFor="baixa-data-pagamento">Data pagamento</Label>
                <Input id="baixa-data-pagamento" type="date" required value={formData.data_pagamento} onChange={(event) => setFormData({ ...formData, data_pagamento: event.target.value })} />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="baixa-valor-pago">Valor recebido agora</Label>
                  <Input id="baixa-valor-pago" type="number" step="0.01" min="0" required value={formData.valor_pago} onChange={(event) => setFormData({ ...formData, valor_pago: Number(event.target.value) })} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="baixa-desconto">Desconto</Label>
                  <Input id="baixa-desconto" type="number" step="0.01" min="0" value={formData.desconto} onChange={(event) => setFormData({ ...formData, desconto: Number(event.target.value) })} />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="baixa-juros">Juros</Label>
                  <Input id="baixa-juros" type="number" step="0.01" min="0" value={formData.juros} onChange={(event) => setFormData({ ...formData, juros: Number(event.target.value) })} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="baixa-historico">Historico</Label>
                  <Input id="baixa-historico" placeholder="Opcional" value={formData.historico} onChange={(event) => setFormData({ ...formData, historico: event.target.value })} />
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeModals}>
                Cancelar
              </Button>
              <Button type="submit" disabled={baixaMutation.isPending}>
                {baixaMutation.isPending ? 'Salvando...' : 'Confirmar baixa'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
