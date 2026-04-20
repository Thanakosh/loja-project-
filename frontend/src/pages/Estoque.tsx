import axios from 'axios'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { ArrowUpDown, Boxes, History, Search } from 'lucide-react'
import toast from 'react-hot-toast'

import { API_BASE_URL } from '../config/api'
import api from '../services/api'
import { getToken } from '../utils/auth'

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

const apiV2 = axios.create({ baseURL: `${API_BASE_URL}/api/v2` })
apiV2.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

interface Produto {
  id: number
  nome: string
  codigo_barras: string
  preco_unitario: number
  unidade: string
  estoque_atual?: number
}

interface Movimentacao {
  id: number
  produto_id: number
  tipo: 'entrada' | 'saida' | 'ajuste' | 'devolucao'
  quantidade: number
  motivo: string | null
  usuario_id: number | null
  data_transacao: string
}

interface NovaMovimentacao {
  produto_id: number
  tipo: 'entrada' | 'saida' | 'ajuste' | 'devolucao'
  quantidade: number
  motivo: string
}

const PAGE_SIZE = 50
const textareaClassName =
  'flex min-h-24 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm transition-colors outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50'

const movementTypeLabel: Record<NovaMovimentacao['tipo'], string> = {
  entrada: 'Entrada',
  saida: 'Saida',
  ajuste: 'Ajuste de saldo',
  devolucao: 'Devolucao',
}

const movementBadgeClassName = (tipo: Movimentacao['tipo']) => {
  if (tipo === 'entrada' || tipo === 'devolucao') return 'bg-primary/10 text-primary'
  if (tipo === 'saida') return 'bg-destructive/10 text-destructive'
  return 'bg-amber-500/10 text-amber-700 dark:text-amber-300'
}

const Estoque = () => {
  const [produtos, setProdutos] = useState<Produto[]>([])
  const [loading, setLoading] = useState(true)
  const [listError, setListError] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [searchInput, setSearchInput] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [kardexProduto, setKardexProduto] = useState<Produto | null>(null)
  const [selectedProduto, setSelectedProduto] = useState<Produto | null>(null)
  const [movimentacoes, setMovimentacoes] = useState<Movimentacao[]>([])
  const [loadingMov, setLoadingMov] = useState(false)
  const [kardexError, setKardexError] = useState('')
  const [isNovaMovOpen, setIsNovaMovOpen] = useState(false)
  const [novaMov, setNovaMov] = useState<NovaMovimentacao>({
    produto_id: 0,
    tipo: 'entrada',
    quantidade: 0,
    motivo: '',
  })
  const [submittingMov, setSubmittingMov] = useState(false)

  const fetchProdutos = useCallback(
    async (newPage = 1, search = searchTerm) => {
      setLoading(true)
      setListError('')
      try {
        const response = await api.get('/produtos', {
          params: { page: newPage, page_size: PAGE_SIZE, incluir_inativos: true, search: search || undefined },
        })
        const data = response.data
        setProdutos(data.items ?? data)
        if (data.pages) setTotalPages(data.pages)
      } catch (error) {
        console.error('Erro ao buscar produtos', error)
        setListError('Nao foi possivel carregar os produtos para o controle de estoque.')
      } finally {
        setLoading(false)
      }
    },
    [searchTerm],
  )

  const fetchKardex = useCallback(async (produtoId: number) => {
    setLoadingMov(true)
    setKardexError('')
    try {
      const response = await apiV2.get(`/estoque/historico/${produtoId}`)
      const data = response.data
      setMovimentacoes(Array.isArray(data) ? data : (data.items ?? []))
    } catch (error) {
      console.error('Erro ao buscar kardex', error)
      setKardexError('Nao foi possivel carregar o historico deste produto.')
    } finally {
      setLoadingMov(false)
    }
  }, [])

  useEffect(() => {
    void fetchProdutos(page, searchTerm)
  }, [page, searchTerm, fetchProdutos])

  useEffect(() => {
    const normalizedSearch = searchInput.trim()
    const timeoutId = setTimeout(() => {
      if (normalizedSearch !== searchTerm) {
        setPage(1)
        setSearchTerm(normalizedSearch)
      }
    }, 300)

    return () => clearTimeout(timeoutId)
  }, [searchInput, searchTerm])

  const resumo = useMemo(
    () => ({
      registrosPagina: produtos.length,
      saldoPagina: produtos.reduce((total, produto) => total + (produto.estoque_atual ?? 0), 0),
    }),
    [produtos],
  )

  const handleSearchSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setPage(1)
    setSearchTerm(searchInput.trim())
  }

  const closeKardex = () => {
    setKardexProduto(null)
    setMovimentacoes([])
    setKardexError('')
  }

  const handleCloseNovaMov = () => {
    setIsNovaMovOpen(false)
    setSelectedProduto(null)
  }

  const handleOpenKardex = (produto: Produto) => {
    setKardexProduto(produto)
    void fetchKardex(produto.id)
  }

  const handleOpenNovaMov = (produto: Produto) => {
    setSelectedProduto(produto)
    setNovaMov({ produto_id: produto.id, tipo: 'entrada', quantidade: 0, motivo: '' })
    setIsNovaMovOpen(true)
  }

  const handleSubmitMov = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (novaMov.quantidade <= 0) {
      toast.error('A quantidade deve ser maior que zero.')
      return
    }

    setSubmittingMov(true)
    try {
      await apiV2.post('/estoque/transacao', novaMov)
      toast.success('Movimentacao registrada com sucesso.')
      void fetchProdutos(page)
      if (kardexProduto && kardexProduto.id === novaMov.produto_id) void fetchKardex(novaMov.produto_id)
      handleCloseNovaMov()
    } catch (error) {
      console.error('Erro ao registrar movimentacao', error)
      toast.error('Erro ao registrar movimentacao. Verifique os dados.')
    } finally {
      setSubmittingMov(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">Estoque</h1>
          <p className="text-sm text-muted-foreground">
            Controle saldo, ajuste de movimentos e acompanhe o historico de cada produto.
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card size="sm">
          <CardHeader>
            <CardDescription>Produtos nesta pagina</CardDescription>
            <CardTitle>{resumo.registrosPagina}</CardTitle>
          </CardHeader>
        </Card>
        <Card size="sm">
          <CardHeader>
            <CardDescription>Saldo acumulado da pagina</CardDescription>
            <CardTitle>{resumo.saldoPagina}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-1">
              <CardTitle>Busca</CardTitle>
              <CardDescription>Localize um produto antes de registrar ajustes ou consultar o kardex.</CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">Pagina {page} de {totalPages}</Badge>
              {searchTerm && <Badge variant="secondary">Busca: {searchTerm}</Badge>}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearchSubmit} className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto_auto]">
            <div className="relative">
              <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
                placeholder="Buscar por nome"
                className="pl-9"
              />
            </div>
            <Button type="submit" variant="outline">
              Buscar
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setSearchInput('')
                setSearchTerm('')
                setPage(1)
              }}
              disabled={!searchTerm && !searchInput}
            >
              Limpar
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-1">
              <CardTitle>Saldo atual</CardTitle>
              <CardDescription>Os ajustes alimentam a trilha de estoque v2 via transacoes.</CardDescription>
            </div>
            <Badge variant="outline">Page size {PAGE_SIZE}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Produto</TableHead>
                <TableHead>Codigo</TableHead>
                <TableHead>Unidade</TableHead>
                <TableHead>Saldo atual</TableHead>
                <TableHead className="text-right">Acoes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={5} className="py-10 text-center text-muted-foreground">
                    Carregando produtos...
                  </TableCell>
                </TableRow>
              ) : listError ? (
                <TableRow>
                  <TableCell colSpan={5}>
                    <Alert variant="destructive">
                      <AlertTitle>Erro ao carregar estoque</AlertTitle>
                      <AlertDescription>{listError}</AlertDescription>
                    </Alert>
                  </TableCell>
                </TableRow>
              ) : produtos.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="py-10 text-center text-muted-foreground">
                    Nenhum produto encontrado.
                  </TableCell>
                </TableRow>
              ) : (
                produtos.map((produto) => (
                  <TableRow key={produto.id}>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium">{produto.nome}</div>
                        <p className="text-xs text-muted-foreground">Preco atual: {produto.preco_unitario.toFixed(2)}</p>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{produto.codigo_barras || '-'}</TableCell>
                    <TableCell className="text-muted-foreground">{produto.unidade || '-'}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className={(produto.estoque_atual ?? 0) <= 0 ? 'border-destructive/40 text-destructive' : ''}>
                        {produto.estoque_atual ?? 'N/A'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex flex-wrap justify-end gap-2">
                        <Button type="button" variant="outline" size="sm" onClick={() => handleOpenNovaMov(produto)}>
                          <ArrowUpDown className="size-3.5" />
                          Ajustar
                        </Button>
                        <Button type="button" variant="outline" size="sm" onClick={() => handleOpenKardex(produto)}>
                          <History className="size-3.5" />
                          Ver kardex
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>

          <Separator />

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">
              Pagina {page} de {totalPages} - mostrando {produtos.length} registros
            </p>
            <div className="flex gap-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1 || loading}>
                Anterior
              </Button>
              <Button type="button" variant="outline" size="sm" onClick={() => setPage((current) => current + 1)} disabled={page >= totalPages || loading}>
                Proxima
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog open={kardexProduto !== null} onOpenChange={(open) => !open && closeKardex()}>
        <DialogContent className="max-h-[90vh] overflow-hidden p-0 sm:max-w-5xl" showCloseButton={false}>
          <DialogHeader className="border-b px-6 py-5">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-1">
                <DialogTitle>Kardex: {kardexProduto?.nome}</DialogTitle>
                <DialogDescription>Historico consolidado de entradas, saidas, devolucoes e ajustes.</DialogDescription>
              </div>
              {kardexProduto && (
                <Button type="button" onClick={() => handleOpenNovaMov(kardexProduto)}>
                  <Boxes className="size-4" />
                  Novo lancamento
                </Button>
              )}
            </div>
          </DialogHeader>

          <div className="space-y-4 overflow-y-auto px-6 py-5">
            {loadingMov ? (
              <p className="py-10 text-center text-muted-foreground">Carregando movimentacoes...</p>
            ) : kardexError ? (
              <Alert variant="destructive">
                <AlertTitle>Erro ao carregar kardex</AlertTitle>
                <AlertDescription>{kardexError}</AlertDescription>
              </Alert>
            ) : movimentacoes.length === 0 ? (
              <Alert>
                <AlertTitle>Nenhuma movimentacao encontrada</AlertTitle>
                <AlertDescription>Este produto ainda nao possui historico registrado.</AlertDescription>
              </Alert>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Data</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Motivo</TableHead>
                    <TableHead className="text-right">Entrada</TableHead>
                    <TableHead className="text-right">Saida</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {movimentacoes.map((movimentacao) => {
                    const isEntrada = movimentacao.quantidade > 0
                    return (
                      <TableRow key={movimentacao.id}>
                        <TableCell className="text-muted-foreground">
                          {new Date(movimentacao.data_transacao).toLocaleString('pt-BR')}
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary" className={movementBadgeClassName(movimentacao.tipo)}>
                            {movementTypeLabel[movimentacao.tipo]}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground">{movimentacao.motivo || '-'}</TableCell>
                        <TableCell className="text-right text-primary">
                          {isEntrada ? `+${movimentacao.quantidade}` : '-'}
                        </TableCell>
                        <TableCell className="text-right text-destructive">
                          {!isEntrada ? movimentacao.quantidade : '-'}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={closeKardex}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={isNovaMovOpen && selectedProduto !== null} onOpenChange={(open) => !open && handleCloseNovaMov()}>
        <DialogContent className="max-h-[90vh] overflow-hidden p-0 sm:max-w-lg" showCloseButton={false}>
          <DialogHeader className="border-b px-6 py-5">
            <DialogTitle>Lancar movimentacao</DialogTitle>
            <DialogDescription>{selectedProduto?.nome}</DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmitMov} className="flex min-h-0 flex-1 flex-col">
            <div className="space-y-4 overflow-y-auto px-6 py-5">
              <div className="space-y-2">
                <Label htmlFor="movimentacao-tipo">Tipo</Label>
                <Select
                  value={novaMov.tipo}
                  onValueChange={(value) => setNovaMov((current) => ({ ...current, tipo: value as NovaMovimentacao['tipo'] }))}
                >
                  <SelectTrigger id="movimentacao-tipo" className="w-full">
                    <SelectValue placeholder="Selecione o tipo" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="entrada">Entrada</SelectItem>
                    <SelectItem value="saida">Saida</SelectItem>
                    <SelectItem value="ajuste">Ajuste de saldo</SelectItem>
                    <SelectItem value="devolucao">Devolucao</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="movimentacao-quantidade">Quantidade</Label>
                <Input
                  id="movimentacao-quantidade"
                  type="number"
                  min="1"
                  step="1"
                  value={novaMov.quantidade || ''}
                  onChange={(event) =>
                    setNovaMov((current) => ({
                      ...current,
                      quantidade: Number.parseInt(event.target.value, 10) || 0,
                    }))
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="movimentacao-motivo">Motivo / observacao</Label>
                <textarea
                  id="movimentacao-motivo"
                  value={novaMov.motivo}
                  onChange={(event) => setNovaMov((current) => ({ ...current, motivo: event.target.value }))}
                  className={textareaClassName}
                  rows={4}
                  placeholder="Ex: nota fiscal 123, ajuste contabil, produto danificado..."
                />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleCloseNovaMov} disabled={submittingMov}>
                Cancelar
              </Button>
              <Button type="submit" disabled={submittingMov}>
                {submittingMov ? 'Salvando...' : 'Confirmar lancamento'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default Estoque
