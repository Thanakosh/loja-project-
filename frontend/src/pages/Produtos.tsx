import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { Pencil, Plus, Search, Trash2 } from 'lucide-react'

import {
  useCategoriasArvore,
  useCheckProdutoDuplicate,
  useCreateProduto,
  useDeactivateProduto,
  useDeleteProdutoPermanente,
  useProdutos,
  useReactivateProduto,
  useUpdateProduto,
} from '../hooks/useProdutos'
import type { CategoriaTreeNode, Produto, ProdutoFormPayload } from '../types/produtos'
import { AiFeedback, type AiResult } from './produtos/AiFeedback'
import { DeleteProdutoDialog } from './produtos/DeleteProdutoDialog'
import { ProductTableSkeleton } from './produtos/ProductTableSkeleton'

import { cn } from '@/lib/utils'
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

interface FormState {
  nome: string
  fornecedor: string
  preco_unitario: string
  preco_liquido: string
  estoque_minimo: string
  quantidade_inicial: string
  unidade: string
  unidade_medida: string
  codigo_ncm: string
  descricao: string
  categoria_id: string
  preco_custo: string
  preco_varejo: string
  preco_atacado: string
  qtd_minima_atacado: string
}

interface FormErrors {
  nome?: string
  fornecedor?: string
  preco_unitario?: string
  preco_liquido?: string
}

type ModalMode = 'create' | 'edit'

const PAGE_SIZE = 50
const FILTER_ALL = '__all__'
const CATEGORY_NONE = '__none__'

const moneyFormatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })

const emptyFormState: FormState = {
  nome: '',
  fornecedor: '',
  preco_unitario: '',
  preco_liquido: '',
  estoque_minimo: '0',
  quantidade_inicial: '0',
  unidade: '',
  unidade_medida: 'UN',
  codigo_ncm: '',
  descricao: '',
  categoria_id: '',
  preco_custo: '',
  preco_varejo: '',
  preco_atacado: '',
  qtd_minima_atacado: '',
}

const textareaClassName =
  'flex min-h-24 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm transition-colors outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50'

const categoriaLabel = (nome: string, level: number) => `${'-- '.repeat(level)}${nome}`

const fieldError = (message?: string) =>
  message ? <p className="mt-1 text-xs text-destructive">{message}</p> : null

const flattenCategorias = (
  nodes: CategoriaTreeNode[],
  level = 0,
): Array<{ id: number; nome: string; level: number }> =>
  nodes.flatMap((node) => [
    { id: node.id, nome: node.nome, level },
    ...flattenCategorias(node.children ?? [], level + 1),
  ])

const nomeInputToneClass = (aiResult: AiResult) => {
  if (aiResult.status === 'duplicata_exata') {
    return 'border-sky-400 focus-visible:border-sky-500 focus-visible:ring-sky-500/20'
  }
  if (aiResult.status === 'similar' && aiResult.candidato?.nivel === 'duplicata') {
    return 'border-destructive focus-visible:border-destructive focus-visible:ring-destructive/20'
  }
  if (aiResult.status === 'similar') {
    return 'border-amber-400 focus-visible:border-amber-500 focus-visible:ring-amber-500/20'
  }
  return ''
}

const buildPayload = (formState: FormState, modalMode: ModalMode): ProdutoFormPayload => {
  const payload: ProdutoFormPayload = {
    nome: formState.nome.trim(),
    fornecedor: formState.fornecedor.trim(),
    preco_unitario: Number(formState.preco_unitario),
    preco_liquido: Number(formState.preco_liquido),
    estoque_minimo: Math.max(0, Number(formState.estoque_minimo) || 0),
  }

  if (modalMode === 'create') payload.quantidade_inicial = Math.max(0, Number(formState.quantidade_inicial) || 0)
  if (formState.unidade.trim()) payload.unidade = formState.unidade.trim()

  payload.unidade_medida = (formState.unidade_medida || 'UN').trim().toUpperCase()

  if (formState.codigo_ncm.trim()) payload.codigo_ncm = formState.codigo_ncm.trim()
  if (formState.descricao.trim()) payload.descricao = formState.descricao.trim()
  if (formState.categoria_id) payload.categoria_id = Number(formState.categoria_id)
  if (formState.preco_custo !== '') payload.preco_custo = Number(formState.preco_custo)
  if (formState.preco_varejo !== '') payload.preco_varejo = Number(formState.preco_varejo)
  if (formState.preco_atacado !== '') payload.preco_atacado = Number(formState.preco_atacado)
  if (formState.qtd_minima_atacado !== '') payload.qtd_minima_atacado = Number(formState.qtd_minima_atacado)

  return payload
}

const validateForm = (formState: FormState) => {
  const errors: FormErrors = {}

  if (!formState.nome.trim()) errors.nome = 'Nome e obrigatorio.'
  if (!formState.fornecedor.trim()) errors.fornecedor = 'Fornecedor e obrigatorio.'

  const precoUnitario = Number(formState.preco_unitario)
  if (!formState.preco_unitario || Number.isNaN(precoUnitario) || precoUnitario <= 0) {
    errors.preco_unitario = 'Preco unitario deve ser maior que zero.'
  }

  const precoLiquido = Number(formState.preco_liquido)
  if (!formState.preco_liquido || Number.isNaN(precoLiquido) || precoLiquido <= 0) {
    errors.preco_liquido = 'Preco liquido deve ser maior que zero.'
  }

  return errors
}

const initialAiResult: AiResult = { status: 'idle' }

const Produtos = () => {
  const [searchInput, setSearchInput] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(1)
  const [incluirInativos, setIncluirInativos] = useState(false)
  const [categoriaFiltro, setCategoriaFiltro] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<ModalMode>('create')
  const [editingProduto, setEditingProduto] = useState<Produto | null>(null)
  const [produtoParaExcluir, setProdutoParaExcluir] = useState<Produto | null>(null)
  const [formState, setFormState] = useState<FormState>(emptyFormState)
  const [formErrors, setFormErrors] = useState<FormErrors>({})
  const [formError, setFormError] = useState('')
  const [aiResult, setAiResult] = useState<AiResult>(initialAiResult)

  const aiDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const lastCheckedNomeRef = useRef('')

  const produtosQuery = useProdutos({
    page,
    page_size: PAGE_SIZE,
    incluir_inativos: incluirInativos,
    search: searchTerm || undefined,
    categoria_id: categoriaFiltro ? Number(categoriaFiltro) : undefined,
  })

  const categoriasQuery = useCategoriasArvore()
  const checkDuplicateMutation = useCheckProdutoDuplicate()
  const createMutation = useCreateProduto()
  const updateMutation = useUpdateProduto()
  const deactivateMutation = useDeactivateProduto()
  const reactivateMutation = useReactivateProduto()
  const deletePermanenteMutation = useDeleteProdutoPermanente()

  const produtos = produtosQuery.data?.items ?? []
  const totalPages = Math.max(1, produtosQuery.data?.pages ?? 1)
  const totalRegistros = produtosQuery.data?.total ?? 0
  const categoriaOptions = flattenCategorias(categoriasQuery.data ?? [])
  const isSaving = createMutation.isPending || updateMutation.isPending

  const resetAiState = () => {
    setAiResult(initialAiResult)
    lastCheckedNomeRef.current = ''
    if (aiDebounceRef.current) {
      clearTimeout(aiDebounceRef.current)
      aiDebounceRef.current = null
    }
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingProduto(null)
    setFormState(emptyFormState)
    setFormErrors({})
    setFormError('')
    resetAiState()
  }

  const openCreateModal = () => {
    setModalMode('create')
    setEditingProduto(null)
    setFormState(emptyFormState)
    setFormErrors({})
    setFormError('')
    resetAiState()
    setIsModalOpen(true)
  }

  const openEditModal = (produto: Produto) => {
    setModalMode('edit')
    setEditingProduto(produto)
    setFormState({
      nome: produto.nome ?? '',
      fornecedor: produto.fornecedor ?? '',
      preco_unitario: String(produto.preco_unitario ?? ''),
      preco_liquido: String(produto.preco_liquido ?? ''),
      estoque_minimo: String(produto.estoque_minimo ?? 0),
      quantidade_inicial: '0',
      unidade: produto.unidade ?? '',
      unidade_medida: produto.unidade_medida ?? 'UN',
      codigo_ncm: produto.codigo_ncm ?? '',
      descricao: produto.descricao ?? '',
      categoria_id: produto.categoria_id ? String(produto.categoria_id) : '',
      preco_custo: produto.preco_custo != null ? String(produto.preco_custo) : '',
      preco_varejo: produto.preco_varejo != null ? String(produto.preco_varejo) : '',
      preco_atacado: produto.preco_atacado != null ? String(produto.preco_atacado) : '',
      qtd_minima_atacado: produto.qtd_minima_atacado != null ? String(produto.qtd_minima_atacado) : '',
    })
    setFormErrors({})
    setFormError('')
    resetAiState()
    setIsModalOpen(true)
  }

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

  const handleInputChange = (field: keyof FormState, value: string) => {
    setFormState((prev) => ({ ...prev, [field]: value }))
    if (field in formErrors) setFormErrors((prev) => ({ ...prev, [field]: undefined }))
  }

  const checkAiDuplicate = async (nome: string) => {
    const nomeTrimmed = nome.trim()
    if (!nomeTrimmed || nomeTrimmed === lastCheckedNomeRef.current) return

    lastCheckedNomeRef.current = nomeTrimmed
    setAiResult({ status: 'checking' })

    try {
      const data = await checkDuplicateMutation.mutateAsync(nomeTrimmed)
      if (data.candidatos.length === 0) {
        setAiResult({ status: 'ok' })
        return
      }

      const top = data.candidatos[0]
      const nomeIgual = top.produto_nome.trim().toLowerCase() === nomeTrimmed.toLowerCase()

      if (editingProduto && top.produto_id === editingProduto.id) {
        setAiResult({ status: 'ok' })
        return
      }

      if (nomeIgual || top.similaridade >= 0.98) {
        setAiResult({ status: 'duplicata_exata', candidato: top })
      } else {
        setAiResult({ status: 'similar', candidato: top })
      }
    } catch {
      setAiResult(initialAiResult)
    }
  }

  const handleNomeChange = (value: string) => {
    handleInputChange('nome', value)
    resetAiState()
    if (value.trim().length >= 3) {
      aiDebounceRef.current = setTimeout(() => checkAiDuplicate(value), 600)
    }
  }

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setFormError('')

    const errors = validateForm(formState)
    setFormErrors(errors)
    if (Object.keys(errors).length > 0) return

    const payload = buildPayload(formState, modalMode)

    if (modalMode === 'create') {
      createMutation.mutate(payload, {
        onSuccess: ({ acao }) => {
          closeModal()
          toast.success(
            acao === 'estoque_somado'
              ? 'Produto ja existia e o estoque foi somado com sucesso.'
              : 'Produto criado com sucesso.',
          )
        },
        onError: () => setFormError('Nao foi possivel criar o produto. Revise os dados e tente novamente.'),
      })
      return
    }

    if (!editingProduto) {
      setFormError('Produto invalido para edicao.')
      return
    }

    updateMutation.mutate(
      { id: editingProduto.id, payload },
      {
        onSuccess: () => {
          closeModal()
          toast.success('Produto atualizado com sucesso.')
        },
        onError: () => setFormError('Nao foi possivel atualizar o produto. Revise os dados e tente novamente.'),
      },
    )
  }

  const handleToggleStatus = (produto: Produto) => {
    if (produto.ativo) {
      if (!window.confirm(`Deseja desativar o produto "${produto.nome}"?`)) return
      deactivateMutation.mutate(produto.id, { onSuccess: () => toast.success('Produto desativado com sucesso.') })
      return
    }
    reactivateMutation.mutate(produto.id, { onSuccess: () => toast.success('Produto reativado com sucesso.') })
  }

  return (
    <div className="space-y-6">
      <DeleteProdutoDialog
        key={produtoParaExcluir?.id ?? 'delete-dialog'}
        produto={produtoParaExcluir}
        isPending={deletePermanenteMutation.isPending}
        onClose={() => {
          if (!deletePermanenteMutation.isPending) setProdutoParaExcluir(null)
        }}
        onConfirmar={(produtoId) =>
          deletePermanenteMutation.mutate(produtoId, {
            onSuccess: (data) => {
              setProdutoParaExcluir(null)
              toast.success(data.message ?? 'Produto removido permanentemente.')
            },
            onError: () => toast.error('Nao foi possivel remover o produto. Tente novamente.'),
          })
        }
      />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">Produtos</h1>
          <p className="text-sm text-muted-foreground">Gerencie catalogo, precificacao e estoque minimo.</p>
        </div>
        <Button type="button" onClick={openCreateModal}>
          <Plus className="size-4" />
          Novo produto
        </Button>
      </div>

      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-1">
              <CardTitle>Busca e filtros</CardTitle>
              <CardDescription>Refine a lista por nome, categoria e status do cadastro.</CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">Pagina {produtosQuery.data?.page ?? page} de {totalPages}</Badge>
              <Badge variant="outline">{totalRegistros} registros</Badge>
              {incluirInativos && <Badge variant="secondary">Incluindo inativos</Badge>}
            </div>
          </div>
        </CardHeader>
        <CardContent className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_220px_auto_auto]">
          <form onSubmit={(event) => { event.preventDefault(); setPage(1); setSearchTerm(searchInput.trim()) }} className="contents">
            <div className="relative">
              <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input value={searchInput} onChange={(event) => setSearchInput(event.target.value)} placeholder="Buscar por nome" className="pl-9" />
            </div>
            <Select value={categoriaFiltro || FILTER_ALL} onValueChange={(value) => { setPage(1); setCategoriaFiltro(value === FILTER_ALL ? '' : value) }}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Todas categorias" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={FILTER_ALL}>Todas categorias</SelectItem>
                {categoriaOptions.map((categoria) => (
                  <SelectItem key={categoria.id} value={String(categoria.id)}>
                    {categoriaLabel(categoria.nome, categoria.level)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button type="submit" variant="outline">Buscar</Button>
            <Button type="button" variant={incluirInativos ? 'secondary' : 'outline'} onClick={() => { setPage(1); setIncluirInativos((prev) => !prev) }}>
              {incluirInativos ? 'Ocultar inativos' : 'Mostrar inativos'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-1">
              <CardTitle>Catalogo</CardTitle>
              <CardDescription>
                {produtosQuery.isFetching && !produtosQuery.isLoading ? 'Atualizando lista de produtos...' : 'Visao consolidada do cadastro atual.'}
              </CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {searchTerm && <Badge variant="outline">Busca: {searchTerm}</Badge>}
              {categoriaFiltro && <Badge variant="outline">Categoria: {categoriaOptions.find((categoria) => String(categoria.id) === categoriaFiltro)?.nome ?? categoriaFiltro}</Badge>}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead>Fornecedor</TableHead>
                <TableHead>Preco unitario</TableHead>
                <TableHead>Estoque atual</TableHead>
                <TableHead>Estoque minimo</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Acoes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {produtosQuery.isLoading ? (
                <ProductTableSkeleton />
              ) : produtosQuery.isError ? (
                <TableRow><TableCell colSpan={7}><Alert variant="destructive"><AlertTitle>Erro ao carregar produtos</AlertTitle><AlertDescription>Tente novamente em alguns instantes.</AlertDescription></Alert></TableCell></TableRow>
              ) : produtos.length === 0 ? (
                <TableRow><TableCell colSpan={7} className="py-10 text-center text-muted-foreground">Nenhum produto encontrado.</TableCell></TableRow>
              ) : (
                produtos.map((produto) => (
                  <TableRow key={produto.id}>
                    <TableCell><div className="space-y-1"><div className="font-medium">{produto.nome}</div>{produto.codigo_ncm && <p className="text-xs text-muted-foreground">NCM: {produto.codigo_ncm}</p>}</div></TableCell>
                    <TableCell className="text-muted-foreground">{produto.fornecedor}</TableCell>
                    <TableCell className="text-muted-foreground">{moneyFormatter.format(produto.preco_unitario)}</TableCell>
                    <TableCell><div className="flex items-center gap-2"><span className={cn(produto.estoque_baixo && 'font-semibold text-destructive')}>{produto.estoque_atual}</span>{produto.estoque_baixo && <Badge variant="outline" className="border-destructive/30 bg-destructive/10 text-destructive">Baixo</Badge>}</div></TableCell>
                    <TableCell className="text-muted-foreground">{produto.estoque_minimo}</TableCell>
                    <TableCell><Badge variant={produto.ativo ? 'secondary' : 'outline'} className={cn(produto.ativo && 'bg-primary/10 text-primary', !produto.ativo && 'text-muted-foreground')}>{produto.ativo ? 'Ativo' : 'Inativo'}</Badge></TableCell>
                    <TableCell className="text-right">
                      <div className="flex flex-wrap justify-end gap-2">
                        <Button type="button" variant="outline" size="sm" onClick={() => openEditModal(produto)}><Pencil className="size-3.5" />Editar</Button>
                        <Button type="button" variant="outline" size="sm" onClick={() => handleToggleStatus(produto)} disabled={deactivateMutation.isPending || reactivateMutation.isPending}>{produto.ativo ? 'Desativar' : 'Reativar'}</Button>
                        <Button type="button" variant="outline" size="sm" onClick={() => setProdutoParaExcluir(produto)} className="border-destructive/30 text-destructive hover:bg-destructive/10 hover:text-destructive"><Trash2 className="size-3.5" />Excluir</Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>

          <Separator />

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">Pagina {produtosQuery.data?.page ?? page} de {totalPages} - mostrando {produtos.length} registros nesta pagina</p>
            <div className="flex gap-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setPage((currentPage) => Math.max(1, currentPage - 1))} disabled={page <= 1 || produtosQuery.isFetching}>Anterior</Button>
              <Button type="button" variant="outline" size="sm" onClick={() => setPage((currentPage) => currentPage + 1)} disabled={page >= totalPages || produtosQuery.isFetching}>Proxima</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog open={isModalOpen} onOpenChange={(open) => { if (!open && !isSaving) closeModal() }}>
        <DialogContent className="max-h-[90vh] overflow-hidden p-0 sm:max-w-5xl" onEscapeKeyDown={(event) => { if (isSaving) event.preventDefault() }} onInteractOutside={(event) => { if (isSaving) event.preventDefault() }}>
          <DialogHeader className="border-b px-6 py-5">
            <DialogTitle>{modalMode === 'create' ? 'Novo produto' : 'Editar produto'}</DialogTitle>
            <DialogDescription>Atualize dados comerciais, estoque minimo e regras de precificacao.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col">
            <div className="flex-1 space-y-5 overflow-y-auto px-6 py-5">
              <Card size="sm">
                <CardHeader><CardTitle className="text-sm">Dados principais</CardTitle><CardDescription>Informacoes basicas do cadastro e verificacao de duplicidade.</CardDescription></CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="produto-nome">Nome *</Label>
                    <Input id="produto-nome" value={formState.nome} onChange={(event) => handleNomeChange(event.target.value)} placeholder="Nome do produto" className={nomeInputToneClass(aiResult)} />
                    {fieldError(formErrors.nome)}
                    <AiFeedback result={aiResult} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="produto-fornecedor">Fornecedor *</Label>
                    <Input id="produto-fornecedor" value={formState.fornecedor} onChange={(event) => handleInputChange('fornecedor', event.target.value)} placeholder="Nome do fornecedor" />
                    {fieldError(formErrors.fornecedor)}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="produto-categoria">Categoria</Label>
                    <Select value={formState.categoria_id || CATEGORY_NONE} onValueChange={(value) => handleInputChange('categoria_id', value === CATEGORY_NONE ? '' : value)}>
                      <SelectTrigger id="produto-categoria" className="w-full"><SelectValue placeholder="Sem categoria" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value={CATEGORY_NONE}>Sem categoria</SelectItem>
                        {categoriaOptions.map((categoria) => <SelectItem key={categoria.id} value={String(categoria.id)}>{categoriaLabel(categoria.nome, categoria.level)}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>

              <Card size="sm">
                <CardHeader><CardTitle className="text-sm">Comercial e estoque</CardTitle><CardDescription>Precos principais, estoque minimo e unidade de venda.</CardDescription></CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="space-y-2"><Label htmlFor="produto-preco-unitario">Preco unitario *</Label><Input id="produto-preco-unitario" type="number" min="0.01" step="0.01" value={formState.preco_unitario} onChange={(event) => handleInputChange('preco_unitario', event.target.value)} />{fieldError(formErrors.preco_unitario)}</div>
                    <div className="space-y-2"><Label htmlFor="produto-preco-liquido">Preco liquido *</Label><Input id="produto-preco-liquido" type="number" min="0.01" step="0.01" value={formState.preco_liquido} onChange={(event) => handleInputChange('preco_liquido', event.target.value)} />{fieldError(formErrors.preco_liquido)}</div>
                    <div className="space-y-2"><Label htmlFor="produto-estoque-minimo">Estoque minimo</Label><Input id="produto-estoque-minimo" type="number" min="0" step="1" value={formState.estoque_minimo} onChange={(event) => handleInputChange('estoque_minimo', event.target.value)} /></div>
                  </div>
                  {modalMode === 'create' && (
                    <div className="space-y-2">
                      <Label htmlFor="produto-estoque-inicial">Estoque inicial{aiResult.status === 'duplicata_exata' && <span className="ml-2 text-xs font-normal text-sky-600 dark:text-sky-400">sera somado ao estoque existente</span>}</Label>
                      <Input id="produto-estoque-inicial" type="number" min="0" step="1" value={formState.quantidade_inicial} onChange={(event) => handleInputChange('quantidade_inicial', event.target.value)} />
                      <p className="text-xs text-muted-foreground">A quantidade sera registrada como entrada inicial.</p>
                    </div>
                  )}
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="space-y-2">
                      <Label htmlFor="produto-unidade-medida">Unidade de medida</Label>
                      <Select value={formState.unidade_medida} onValueChange={(value) => handleInputChange('unidade_medida', value)}>
                        <SelectTrigger id="produto-unidade-medida" className="w-full"><SelectValue placeholder="Selecione" /></SelectTrigger>
                        <SelectContent>{['UN', 'CX', 'MT', 'KG', 'LT', 'PC', 'M2', 'M3'].map((unidade) => <SelectItem key={unidade} value={unidade}>{unidade}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2"><Label htmlFor="produto-unidade">Sigla exibida</Label><Input id="produto-unidade" value={formState.unidade} onChange={(event) => handleInputChange('unidade', event.target.value)} placeholder="UN, KG, CX" /></div>
                    <div className="space-y-2"><Label htmlFor="produto-codigo-ncm">Codigo NCM</Label><Input id="produto-codigo-ncm" value={formState.codigo_ncm} onChange={(event) => handleInputChange('codigo_ncm', event.target.value)} placeholder="Opcional" /></div>
                  </div>
                </CardContent>
              </Card>

              <Card size="sm">
                <CardHeader><CardTitle className="text-sm">Precificacao avancada</CardTitle><CardDescription>Campos opcionais para custo, varejo e atacado.</CardDescription></CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2"><Label htmlFor="produto-preco-custo">Preco de custo</Label><Input id="produto-preco-custo" type="number" min="0" step="0.01" value={formState.preco_custo} onChange={(event) => handleInputChange('preco_custo', event.target.value)} placeholder="Opcional" /></div>
                  <div className="space-y-2"><Label htmlFor="produto-preco-varejo">Preco varejo</Label><Input id="produto-preco-varejo" type="number" min="0" step="0.01" value={formState.preco_varejo} onChange={(event) => handleInputChange('preco_varejo', event.target.value)} placeholder="Opcional" /></div>
                  <div className="space-y-2"><Label htmlFor="produto-preco-atacado">Preco atacado</Label><Input id="produto-preco-atacado" type="number" min="0" step="0.01" value={formState.preco_atacado} onChange={(event) => handleInputChange('preco_atacado', event.target.value)} placeholder="Opcional" /></div>
                  <div className="space-y-2"><Label htmlFor="produto-qtd-minima-atacado">Qtd. minima para atacado</Label><Input id="produto-qtd-minima-atacado" type="number" min="0" step="1" value={formState.qtd_minima_atacado} onChange={(event) => handleInputChange('qtd_minima_atacado', event.target.value)} placeholder="Opcional" /></div>
                </CardContent>
              </Card>

              <Card size="sm">
                <CardHeader><CardTitle className="text-sm">Descricao</CardTitle><CardDescription>Contexto adicional exibido nas telas que consomem o produto.</CardDescription></CardHeader>
                <CardContent className="space-y-2"><Label htmlFor="produto-descricao">Descricao</Label><textarea id="produto-descricao" value={formState.descricao} onChange={(event) => handleInputChange('descricao', event.target.value)} className={textareaClassName} placeholder="Descricao do produto" /></CardContent>
              </Card>
            </div>

            {formError && <div className="px-6 pb-4"><Alert variant="destructive"><AlertTitle>Falha ao salvar</AlertTitle><AlertDescription>{formError}</AlertDescription></Alert></div>}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeModal} disabled={isSaving}>Cancelar</Button>
              <Button type="submit" disabled={isSaving}>{modalMode === 'create' ? 'Criar produto' : 'Salvar alteracoes'}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default Produtos
