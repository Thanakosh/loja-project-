import { useCallback, useEffect, useMemo, useState } from 'react'
import { Ban, FileText } from 'lucide-react'
import toast from 'react-hot-toast'

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
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

interface VendaItem {
  id: number
  nome_produto: string
  quantidade: number
  preco_unitario: number
  preco_total: number
  unidade?: string
  desconto?: number
}

interface VendaPagamento {
  forma_pagamento: number
  forma_pagamento_label?: string | null
  valor: number
  troco?: number
}

interface Venda {
  id: number
  numero_legado: number
  data: string
  total: number
  desconto: number
  forma_pagamento?: number | null
  forma_pagamento_label?: string | null
  troco?: number
  pagamentos?: VendaPagamento[]
  cancelada: boolean
  observacao?: string
  cliente_id?: number
  itens: VendaItem[]
}

interface VendasPaginadas {
  items: Venda[]
  total: number
  page: number
  page_size: number
  pages: number
}

interface VendasParams {
  page: number
  page_size: number
  start_date?: string
  end_date?: string
}

const PAYMENT_LABELS: Record<number, string> = {
  1: 'Dinheiro',
  2: 'Debito',
  3: 'Credito',
  4: 'PIX',
  5: 'Boleto',
  6: 'A prazo',
}

const PAGE_SIZE = 50
const currencyFormatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })

const formatVendaPagamentos = (venda: Venda) => {
  if (venda.pagamentos && venda.pagamentos.length > 0) {
    return venda.pagamentos
      .map(
        (pagamento) =>
          `${pagamento.forma_pagamento_label ?? PAYMENT_LABELS[pagamento.forma_pagamento] ?? 'Nao informado'} (${currencyFormatter.format(pagamento.valor)})`,
      )
      .join(' + ')
  }
  return venda.forma_pagamento_label ?? PAYMENT_LABELS[venda.forma_pagamento ?? 0] ?? 'Nao informado'
}

const Vendas = () => {
  const [vendas, setVendas] = useState<Venda[]>([])
  const [loading, setLoading] = useState(true)
  const [listError, setListError] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [appliedStartDate, setAppliedStartDate] = useState('')
  const [appliedEndDate, setAppliedEndDate] = useState('')
  const [selectedVenda, setSelectedVenda] = useState<Venda | null>(null)
  const [isCancelConfirmOpen, setIsCancelConfirmOpen] = useState(false)
  const [modalLoading, setModalLoading] = useState(false)
  const [detailError, setDetailError] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  const fetchVendas = useCallback(async (currentPage: number, currentStartDate: string, currentEndDate: string) => {
    setLoading(true)
    setListError('')
    try {
      const params: VendasParams = { page: currentPage, page_size: PAGE_SIZE }
      if (currentStartDate) params.start_date = currentStartDate
      if (currentEndDate) params.end_date = currentEndDate

      const response = await api.get('/vendas/', { params })
      const data = response.data as VendasPaginadas
      setVendas(data.items ?? [])
      setTotalPages(data.pages ?? 1)
    } catch (error) {
      console.error('Erro ao buscar vendas', error)
      setListError('Nao foi possivel carregar o historico de vendas.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void fetchVendas(page, appliedStartDate, appliedEndDate)
  }, [appliedEndDate, appliedStartDate, fetchVendas, page])

  const resumo = useMemo(
    () => ({
      total: vendas.length,
      ativas: vendas.filter((venda) => !venda.cancelada).length,
      canceladas: vendas.filter((venda) => venda.cancelada).length,
      faturamento: vendas.filter((venda) => !venda.cancelada).reduce((acc, venda) => acc + venda.total, 0),
    }),
    [vendas],
  )

  const handleFilter = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setAppliedStartDate(startDate)
    setAppliedEndDate(endDate)
    setPage(1)
  }

  const handleOpenDetails = async (vendaId: number) => {
    setModalLoading(true)
    setDetailError('')
    setSelectedVenda(null)
    try {
      const response = await api.get(`/vendas/${vendaId}`)
      setSelectedVenda(response.data)
    } catch (error) {
      console.error('Erro ao carregar detalhes da venda', error)
      setDetailError('Nao foi possivel carregar os detalhes da venda.')
    } finally {
      setModalLoading(false)
    }
  }

  const closeDetails = () => {
    setSelectedVenda(null)
    setDetailError('')
    setModalLoading(false)
    setIsCancelConfirmOpen(false)
  }

  const handleCancelVenda = async () => {
    if (!selectedVenda || selectedVenda.cancelada) return

    try {
      await api.post(`/pdv/venda/${selectedVenda.id}/cancelar`)
      setIsCancelConfirmOpen(false)
      closeDetails()
      await fetchVendas(page, appliedStartDate, appliedEndDate)
      toast.success('Venda cancelada com sucesso!')
    } catch (error) {
      console.error('Erro ao cancelar venda', error)
      toast.error('Nao foi possivel cancelar a venda. Tente novamente.')
    }
  }

  return (
    <div className="space-y-6">
      <AlertDialog open={isCancelConfirmOpen} onOpenChange={setIsCancelConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancelar venda</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja cancelar a venda #{selectedVenda?.numero_legado ?? selectedVenda?.id}?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Voltar</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onClick={handleCancelVenda}>
              Confirmar cancelamento
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <div className="space-y-1">
        <h1 className="text-2xl font-semibold">Historico de vendas</h1>
        <p className="text-sm text-muted-foreground">Consulte vendas concluidas, pagamentos e cancelamentos realizados no PDV.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card size="sm">
          <CardHeader>
            <CardDescription>Vendas na pagina</CardDescription>
            <CardTitle>{resumo.total}</CardTitle>
          </CardHeader>
        </Card>
        <Card size="sm">
          <CardHeader>
            <CardDescription>Ativas</CardDescription>
            <CardTitle>{resumo.ativas}</CardTitle>
          </CardHeader>
        </Card>
        <Card size="sm">
          <CardHeader>
            <CardDescription>Canceladas</CardDescription>
            <CardTitle>{resumo.canceladas}</CardTitle>
          </CardHeader>
        </Card>
        <Card size="sm">
          <CardHeader>
            <CardDescription>Faturamento da pagina</CardDescription>
            <CardTitle>{currencyFormatter.format(resumo.faturamento)}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-1">
              <CardTitle>Filtro por periodo</CardTitle>
              <CardDescription>Use as datas para revisar vendas e cancelamentos de um intervalo especifico.</CardDescription>
            </div>
            <Badge variant="outline">Pagina {page} de {totalPages}</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleFilter} className="grid gap-3 lg:grid-cols-[minmax(0,220px)_minmax(0,220px)_auto]">
            <div className="space-y-2">
              <Label htmlFor="vendas-start-date">De</Label>
              <Input id="vendas-start-date" type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="vendas-end-date">Ate</Label>
              <Input id="vendas-end-date" type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
            </div>
            <div className="flex items-end">
              <Button type="submit" variant="outline">
                Filtrar
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-1">
              <CardTitle>Lista de vendas</CardTitle>
              <CardDescription>Visao resumida das vendas registradas no periodo filtrado.</CardDescription>
            </div>
            {(appliedStartDate || appliedEndDate) && (
              <div className="flex flex-wrap items-center gap-2">
                {appliedStartDate && <Badge variant="secondary">Inicio: {appliedStartDate}</Badge>}
                {appliedEndDate && <Badge variant="secondary">Fim: {appliedEndDate}</Badge>}
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Data</TableHead>
                <TableHead>Numero</TableHead>
                <TableHead>Pagamento</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Total</TableHead>
                <TableHead>Itens</TableHead>
                <TableHead className="text-right">Acoes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-10 text-center text-muted-foreground">Carregando vendas...</TableCell>
                </TableRow>
              ) : listError ? (
                <TableRow>
                  <TableCell colSpan={7}>
                    <Alert variant="destructive">
                      <AlertTitle>Erro ao carregar vendas</AlertTitle>
                      <AlertDescription>{listError}</AlertDescription>
                    </Alert>
                  </TableCell>
                </TableRow>
              ) : vendas.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-10 text-center text-muted-foreground">Nenhuma venda encontrada no periodo.</TableCell>
                </TableRow>
              ) : (
                vendas.map((venda) => (
                  <TableRow key={venda.id}>
                    <TableCell className="text-muted-foreground">{new Date(venda.data).toLocaleDateString('pt-BR')}</TableCell>
                    <TableCell className="font-medium">{venda.numero_legado}</TableCell>
                    <TableCell className="max-w-sm text-muted-foreground">{formatVendaPagamentos(venda)}</TableCell>
                    <TableCell>
                      <Badge
                        variant={venda.cancelada ? 'outline' : 'secondary'}
                        className={venda.cancelada ? 'border-destructive/40 text-destructive' : 'bg-primary/10 text-primary'}
                      >
                        {venda.cancelada ? 'Cancelada' : 'Ativa'}
                      </Badge>
                    </TableCell>
                    <TableCell className={venda.cancelada ? 'line-through text-muted-foreground' : 'font-medium text-primary'}>
                      {currencyFormatter.format(venda.total)}
                    </TableCell>
                    <TableCell className="text-muted-foreground">{venda.itens.length} itens</TableCell>
                    <TableCell className="text-right">
                      <Button type="button" variant="outline" size="sm" onClick={() => void handleOpenDetails(venda.id)}>
                        <FileText className="size-3.5" />
                        Ver detalhes
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>

          <Separator />

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">
              Exibindo {vendas.length} registro(s) na pagina {page} de {totalPages}
            </p>
            <div className="flex gap-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setPage((prev) => Math.max(prev - 1, 1))} disabled={loading || page <= 1}>
                Anterior
              </Button>
              <Button type="button" variant="outline" size="sm" onClick={() => setPage((prev) => prev + 1)} disabled={loading || page >= totalPages}>
                Proxima
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog open={modalLoading || selectedVenda !== null || Boolean(detailError)} onOpenChange={(open) => !open && closeDetails()}>
        <DialogContent className="max-h-[90vh] overflow-hidden p-0 sm:max-w-4xl" showCloseButton={false}>
          <DialogHeader className="border-b px-6 py-5">
            <DialogTitle>
              {selectedVenda
                ? `Detalhes da venda #${selectedVenda.numero_legado || selectedVenda.id}`
                : 'Detalhes da venda'}
            </DialogTitle>
            <DialogDescription>Resumo financeiro, pagamentos e itens da venda selecionada.</DialogDescription>
          </DialogHeader>

          <div className="space-y-4 overflow-y-auto px-6 py-5">
            {modalLoading ? (
              <p className="py-10 text-center text-muted-foreground">Carregando detalhes...</p>
            ) : detailError ? (
              <Alert variant="destructive">
                <AlertTitle>Falha ao carregar detalhes</AlertTitle>
                <AlertDescription>{detailError}</AlertDescription>
              </Alert>
            ) : selectedVenda ? (
              <>
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                  <Card size="sm">
                    <CardHeader>
                      <CardDescription>Data da venda</CardDescription>
                      <CardTitle>{new Date(selectedVenda.data).toLocaleString('pt-BR')}</CardTitle>
                    </CardHeader>
                  </Card>
                  <Card size="sm">
                    <CardHeader>
                      <CardDescription>Total</CardDescription>
                      <CardTitle>{currencyFormatter.format(selectedVenda.total)}</CardTitle>
                    </CardHeader>
                  </Card>
                  <Card size="sm">
                    <CardHeader>
                      <CardDescription>Pagamento</CardDescription>
                      <CardTitle>{formatVendaPagamentos(selectedVenda)}</CardTitle>
                    </CardHeader>
                  </Card>
                  <Card size="sm">
                    <CardHeader>
                      <CardDescription>Status</CardDescription>
                      <CardTitle>{selectedVenda.cancelada ? 'Cancelada' : 'Ativa'}</CardTitle>
                    </CardHeader>
                  </Card>
                </div>

                {selectedVenda.observacao && (
                  <Alert>
                    <AlertTitle>Observacao</AlertTitle>
                    <AlertDescription>{selectedVenda.observacao}</AlertDescription>
                  </Alert>
                )}

                <Card>
                  <CardHeader>
                    <CardTitle>Itens da venda</CardTitle>
                    <CardDescription>Produtos registrados na venda selecionada.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Produto</TableHead>
                          <TableHead className="text-center">Qtd</TableHead>
                          <TableHead className="text-right">Preco unit.</TableHead>
                          <TableHead className="text-right">Subtotal</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {selectedVenda.itens.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={4} className="py-10 text-center text-muted-foreground">Nenhum item registrado nesta venda.</TableCell>
                          </TableRow>
                        ) : (
                          selectedVenda.itens.map((item) => (
                            <TableRow key={item.id}>
                              <TableCell className="font-medium">{item.nome_produto}</TableCell>
                              <TableCell className="text-center text-muted-foreground">{item.quantidade}</TableCell>
                              <TableCell className="text-right text-muted-foreground">{currencyFormatter.format(item.preco_unitario)}</TableCell>
                              <TableCell className="text-right font-medium">{currencyFormatter.format(item.preco_total)}</TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              </>
            ) : null}
          </div>

          <DialogFooter>
            {selectedVenda && !selectedVenda.cancelada && (
              <Button type="button" variant="destructive" onClick={() => setIsCancelConfirmOpen(true)}>
                <Ban className="size-4" />
                Cancelar venda
              </Button>
            )}
            <Button type="button" variant="outline" onClick={closeDetails}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default Vendas
