import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CalendarRange, FileText } from 'lucide-react'

import api from '../services/api'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

interface NotaFiscalItem {
  id: number
  nome_produto?: string | null
  unidade?: string | null
  quantidade: number
  preco_unitario: number
  preco_total: number
  ncm?: string | null
  cfop?: string | null
}

interface NotaFiscal {
  id: number
  numero_legado: number
  chave_acesso?: string | null
  serie?: string | null
  data_emissao?: string | null
  situacao: number
  entrada_saida?: 'E' | 'S' | null
  cfop_descricao?: string | null
  cliente_id?: number | null
  valor_produtos: number
  valor_total: number
  valor_desconto: number
  valor_icms: number
  valor_ipi: number
  observacao?: string | null
  itens: NotaFiscalItem[]
}

const LIMIT = 10

const moneyFormatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const dateFormatter = new Intl.DateTimeFormat('pt-BR')

const movementLabel = (tipo: NotaFiscal['entrada_saida']) => {
  if (tipo === 'E') return 'Entrada'
  if (tipo === 'S') return 'Saida'
  return 'Nao informado'
}

const NotasFiscais = () => {
  const [dataInicio, setDataInicio] = useState('')
  const [dataFim, setDataFim] = useState('')
  const [appliedDataInicio, setAppliedDataInicio] = useState('')
  const [appliedDataFim, setAppliedDataFim] = useState('')
  const [page, setPage] = useState(1)
  const [notaSelecionadaId, setNotaSelecionadaId] = useState<number | null>(null)

  const skip = (page - 1) * LIMIT

  const notasQuery = useQuery({
    queryKey: ['notas-fiscais', skip, appliedDataInicio, appliedDataFim],
    queryFn: async () => {
      const response = await api.get('/notas-fiscais/', {
        params: {
          skip,
          limit: LIMIT,
          data_inicio: appliedDataInicio || undefined,
          data_fim: appliedDataFim || undefined,
        },
      })
      return response.data as NotaFiscal[]
    },
    placeholderData: (previousData) => previousData,
  })

  const detalhesNotaQuery = useQuery({
    queryKey: ['nota-fiscal', notaSelecionadaId],
    queryFn: async () => {
      const response = await api.get(`/notas-fiscais/${notaSelecionadaId}`)
      return response.data as NotaFiscal
    },
    enabled: notaSelecionadaId !== null,
  })

  const notas = useMemo(() => notasQuery.data ?? [], [notasQuery.data])
  const hasNextPage = notas.length === LIMIT

  const resumo = useMemo(
    () =>
      notas.reduce(
        (acc, nota) => {
          acc.totalNotas += 1
          acc.totalValor += nota.valor_total
          return acc
        },
        { totalNotas: 0, totalValor: 0 },
      ),
    [notas],
  )

  const handleFiltrar = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setAppliedDataInicio(dataInicio)
    setAppliedDataFim(dataFim)
    setPage(1)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">Notas fiscais</h1>
          <p className="text-sm text-muted-foreground">
            Consulte documentos emitidos, totais fiscais e detalhes dos itens processados.
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card size="sm">
          <CardHeader>
            <CardDescription>Total de notas nesta pagina</CardDescription>
            <CardTitle>{resumo.totalNotas}</CardTitle>
          </CardHeader>
        </Card>
        <Card size="sm">
          <CardHeader>
            <CardDescription>Soma do valor total</CardDescription>
            <CardTitle>{moneyFormatter.format(resumo.totalValor)}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-1">
              <CardTitle>Filtro por periodo</CardTitle>
              <CardDescription>Refine a lista usando a data de emissao das notas.</CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">Pagina {page}</Badge>
              {appliedDataInicio && <Badge variant="secondary">Inicio: {appliedDataInicio}</Badge>}
              {appliedDataFim && <Badge variant="secondary">Fim: {appliedDataFim}</Badge>}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleFiltrar} className="grid gap-3 lg:grid-cols-[minmax(0,220px)_minmax(0,220px)_auto]">
            <div className="space-y-2">
              <Label htmlFor="nota-data-inicio">Data inicio</Label>
              <Input id="nota-data-inicio" type="date" value={dataInicio} onChange={(event) => setDataInicio(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="nota-data-fim">Data fim</Label>
              <Input id="nota-data-fim" type="date" value={dataFim} onChange={(event) => setDataFim(event.target.value)} />
            </div>
            <div className="flex items-end">
              <Button type="submit" variant="outline">
                <CalendarRange className="size-4" />
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
              <CardTitle>Documentos encontrados</CardTitle>
              <CardDescription>Visao resumida das notas fiscais da pagina atual.</CardDescription>
            </div>
            <Badge variant="outline">Limite {LIMIT} por pagina</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Numero</TableHead>
                <TableHead>Data emissao</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>CFOP</TableHead>
                <TableHead>Valor produtos</TableHead>
                <TableHead>Valor total</TableHead>
                <TableHead className="text-right">Acoes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {notasQuery.isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-10 text-center text-muted-foreground">
                    Carregando notas fiscais...
                  </TableCell>
                </TableRow>
              ) : notasQuery.isError ? (
                <TableRow>
                  <TableCell colSpan={7}>
                    <Alert variant="destructive">
                      <AlertTitle>Erro ao carregar notas fiscais</AlertTitle>
                      <AlertDescription>Tente novamente em alguns instantes.</AlertDescription>
                    </Alert>
                  </TableCell>
                </TableRow>
              ) : notas.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-10 text-center text-muted-foreground">
                    Nenhuma nota fiscal encontrada.
                  </TableCell>
                </TableRow>
              ) : (
                notas.map((nota) => (
                  <TableRow key={nota.id}>
                    <TableCell className="font-medium">{nota.numero_legado}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {nota.data_emissao ? dateFormatter.format(new Date(nota.data_emissao)) : '-'}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className={
                          nota.entrada_saida === 'E'
                            ? 'bg-primary/10 text-primary'
                            : nota.entrada_saida === 'S'
                              ? 'bg-sky-500/10 text-sky-700 dark:text-sky-300'
                              : ''
                        }
                      >
                        {movementLabel(nota.entrada_saida)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{nota.cfop_descricao || '-'}</TableCell>
                    <TableCell className="text-muted-foreground">{moneyFormatter.format(nota.valor_produtos)}</TableCell>
                    <TableCell className="font-medium">{moneyFormatter.format(nota.valor_total)}</TableCell>
                    <TableCell className="text-right">
                      <Button type="button" variant="outline" size="sm" onClick={() => setNotaSelecionadaId(nota.id)}>
                        <FileText className="size-3.5" />
                        Ver itens
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>

          <Separator />

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <Button type="button" variant="outline" size="sm" onClick={() => setPage((prev) => Math.max(1, prev - 1))} disabled={page === 1}>
              Anterior
            </Button>
            <span className="text-sm text-muted-foreground">Pagina {page}</span>
            <Button type="button" variant="outline" size="sm" onClick={() => setPage((prev) => prev + 1)} disabled={!hasNextPage}>
              Proxima
            </Button>
          </div>
        </CardContent>
      </Card>

      <Dialog open={notaSelecionadaId !== null} onOpenChange={(open) => !open && setNotaSelecionadaId(null)}>
        <DialogContent className="max-h-[90vh] overflow-hidden p-0 sm:max-w-5xl" showCloseButton={false}>
          <DialogHeader className="border-b px-6 py-5">
            <DialogTitle>Itens da nota fiscal</DialogTitle>
            <DialogDescription>Detalhes completos do documento selecionado.</DialogDescription>
          </DialogHeader>

          <div className="space-y-4 overflow-y-auto px-6 py-5">
            {detalhesNotaQuery.isLoading ? (
              <p className="py-10 text-center text-muted-foreground">Carregando itens...</p>
            ) : detalhesNotaQuery.isError ? (
              <Alert variant="destructive">
                <AlertTitle>Erro ao carregar detalhes da nota</AlertTitle>
                <AlertDescription>Tente novamente em alguns instantes.</AlertDescription>
              </Alert>
            ) : (
              <>
                <div className="grid gap-3 md:grid-cols-4">
                  <Card size="sm">
                    <CardHeader>
                      <CardDescription>Numero</CardDescription>
                      <CardTitle>{detalhesNotaQuery.data?.numero_legado ?? '-'}</CardTitle>
                    </CardHeader>
                  </Card>
                  <Card size="sm">
                    <CardHeader>
                      <CardDescription>Serie</CardDescription>
                      <CardTitle>{detalhesNotaQuery.data?.serie || '-'}</CardTitle>
                    </CardHeader>
                  </Card>
                  <Card size="sm">
                    <CardHeader>
                      <CardDescription>Valor total</CardDescription>
                      <CardTitle>{moneyFormatter.format(detalhesNotaQuery.data?.valor_total ?? 0)}</CardTitle>
                    </CardHeader>
                  </Card>
                  <Card size="sm">
                    <CardHeader>
                      <CardDescription>ICMS / IPI</CardDescription>
                      <CardTitle>
                        {moneyFormatter.format(detalhesNotaQuery.data?.valor_icms ?? 0)} / {moneyFormatter.format(detalhesNotaQuery.data?.valor_ipi ?? 0)}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                </div>

                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Produto</TableHead>
                      <TableHead>Unidade</TableHead>
                      <TableHead>Qtd</TableHead>
                      <TableHead>Preco unit.</TableHead>
                      <TableHead>Total</TableHead>
                      <TableHead>NCM</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(detalhesNotaQuery.data?.itens ?? []).length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="py-10 text-center text-muted-foreground">
                          Nenhum item encontrado para esta NF.
                        </TableCell>
                      </TableRow>
                    ) : (
                      detalhesNotaQuery.data?.itens.map((item) => (
                        <TableRow key={item.id}>
                          <TableCell className="font-medium">{item.nome_produto || '-'}</TableCell>
                          <TableCell className="text-muted-foreground">{item.unidade || '-'}</TableCell>
                          <TableCell className="text-muted-foreground">{item.quantidade}</TableCell>
                          <TableCell className="text-muted-foreground">{moneyFormatter.format(item.preco_unitario)}</TableCell>
                          <TableCell className="font-medium">{moneyFormatter.format(item.preco_total)}</TableCell>
                          <TableCell className="text-muted-foreground">{item.ncm || '-'}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setNotaSelecionadaId(null)}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default NotasFiscais
