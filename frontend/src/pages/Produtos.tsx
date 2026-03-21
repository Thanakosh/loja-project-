import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import api from '../services/api'
import { useAccessibleModal } from '../hooks/useAccessibleModal'

interface Produto {
  id: number
  nome: string
  descricao?: string | null
  fornecedor: string
  preco_unitario: number
  preco_liquido: number
  codigo_ncm?: string | null
  unidade?: string | null
  unidade_medida?: string | null
  estoque_atual: number
  estoque_baixo: boolean
  estoque_minimo: number
  ativo: boolean
  data_emissao?: string | null
  numero_nota?: string | null
  cnpj_fornecedor?: string | null
  categoria_id?: number | null
  preco_custo?: number | null
  preco_varejo?: number | null
  preco_atacado?: number | null
  qtd_minima_atacado?: number | null
}

interface CategoriaTreeNode {
  id: number
  nome: string
  parent_id?: number | null
  ativo: boolean
  children: CategoriaTreeNode[]
}

interface ProdutoFormPayload {
  nome: string
  fornecedor: string
  preco_unitario: number
  preco_liquido: number
  estoque_minimo: number
  quantidade_inicial?: number
  unidade?: string
  unidade_medida?: string
  codigo_ncm?: string
  descricao?: string
  categoria_id?: number
  preco_custo?: number
  preco_varejo?: number
  preco_atacado?: number
  qtd_minima_atacado?: number
}

interface ProdutoListResponse {
  items: Produto[]
  total: number
  page: number
  pages: number
}

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

// ── Tipos de IA ──
type AiStatus = 'idle' | 'checking' | 'duplicata_exata' | 'similar' | 'ok'

interface DuplicateCandidate {
  produto_id: number
  produto_nome: string
  similaridade: number
  nivel: 'duplicata' | 'alerta'
}

interface DuplicateCheckResponse {
  tem_duplicata: boolean
  tem_alerta: boolean
  metodo: string
  candidatos: DuplicateCandidate[]
}

interface AiResult {
  status: AiStatus
  candidato?: DuplicateCandidate
}

type ModalMode = 'create' | 'edit'

const PAGE_SIZE = 50

const moneyFormatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })

const emptyFormState: FormState = {
  nome: '', fornecedor: '', preco_unitario: '', preco_liquido: '',
  estoque_minimo: '0', quantidade_inicial: '0', unidade: '', unidade_medida: 'UN',
  codigo_ncm: '', descricao: '', categoria_id: '', preco_custo: '',
  preco_varejo: '', preco_atacado: '', qtd_minima_atacado: ''
}

const inputCls = 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'

// ── Feedback de IA ──
const AiFeedback = ({ result }: { result: AiResult }) => {
  if (result.status === 'idle') return null

  if (result.status === 'checking') {
    return (
      <div className="mt-1.5 flex items-center gap-1.5 text-xs text-blue-500 dark:text-blue-400">
        <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        Verificando duplicatas...
      </div>
    )
  }

  if (result.status === 'ok') {
    return (
      <div className="mt-1.5 flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400">
        <span>✅</span>
        <span>Nome disponível — nenhum produto parecido encontrado.</span>
      </div>
    )
  }

  if (result.status === 'duplicata_exata' && result.candidato) {
    return (
      <div className="mt-1.5 rounded-lg border border-sky-200 dark:border-sky-700 bg-sky-50 dark:bg-sky-900/30 px-3 py-2">
        <div className="flex items-start gap-2">
          <span className="text-base">🔄</span>
          <div>
            <p className="text-xs font-semibold text-sky-800 dark:text-sky-200">Produto já existe no estoque</p>
            <p className="text-xs text-sky-700 dark:text-sky-300 mt-0.5">
              <span className="font-medium">"{result.candidato.produto_nome}"</span> — ao salvar, a quantidade será somada ao estoque existente.
            </p>
          </div>
        </div>
      </div>
    )
  }

  if (result.status === 'similar' && result.candidato) {
    const pct = Math.round(result.candidato.similaridade * 100)
    const forte = result.candidato.nivel === 'duplicata'
    return (
      <div className={`mt-1.5 rounded-lg border px-3 py-2 ${forte ? 'border-red-200 dark:border-red-700 bg-red-50 dark:bg-red-900/20' : 'border-amber-200 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20'}`}>
        <div className="flex items-start gap-2">
          <span className="text-base">{forte ? '🔴' : '⚠️'}</span>
          <div>
            <p className={`text-xs font-semibold ${forte ? 'text-red-800 dark:text-red-200' : 'text-amber-800 dark:text-amber-200'}`}>
              {forte ? 'Possível duplicata detectada' : 'Nome parecido encontrado'} · {pct}% similar
            </p>
            <p className={`text-xs mt-0.5 ${forte ? 'text-red-700 dark:text-red-300' : 'text-amber-700 dark:text-amber-300'}`}>
              Já existe: <span className="font-medium">"{result.candidato.produto_nome}"</span>. Verifique antes de salvar.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return null
}

// ── Modal de confirmação de exclusão permanente ──
interface ModalExclusaoProps {
  produto: Produto
  onConfirmar: () => void
  onCancelar: () => void
  isPending: boolean
}

const ModalExclusao = ({ produto, onConfirmar, onCancelar, isPending }: ModalExclusaoProps) => {
  const [confirmacaoTexto, setConfirmacaoTexto] = useState('')
  const nomeEsperado = produto.nome.trim()
  const confirmacaoCorreta = confirmacaoTexto.trim() === nomeEsperado

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-2xl bg-white dark:bg-gray-800 shadow-2xl overflow-hidden">
        {/* Cabeçalho vermelho */}
        <div className="bg-red-600 px-6 py-4 flex items-center gap-3">
          <span className="text-2xl">🗑️</span>
          <div>
            <h2 className="text-base font-semibold text-white">Excluir produto permanentemente</h2>
            <p className="text-xs text-red-200 mt-0.5">Esta ação não pode ser desfeita</p>
          </div>
        </div>

        <div className="px-6 py-5 space-y-4">
          {/* Info do produto */}
          <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50 p-4 space-y-1">
            <p className="text-sm font-semibold text-gray-800 dark:text-gray-100">{produto.nome}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Fornecedor: {produto.fornecedor}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Estoque atual: <span className={`font-semibold ${produto.estoque_atual > 0 ? 'text-amber-600 dark:text-amber-400' : 'text-gray-600 dark:text-gray-300'}`}>{produto.estoque_atual} unid.</span>
            </p>
          </div>

          {/* Aviso de consequências */}
          <div className="rounded-xl border border-red-200 dark:border-red-700 bg-red-50 dark:bg-red-900/20 p-3 space-y-1">
            <p className="text-xs font-semibold text-red-800 dark:text-red-200">O que será removido:</p>
            <ul className="text-xs text-red-700 dark:text-red-300 space-y-0.5 list-disc list-inside">
              <li>Cadastro do produto</li>
              <li>Todo o histórico de movimentações de estoque</li>
              <li>Embeddings e dados de IA associados</li>
            </ul>
            {produto.estoque_atual > 0 && (
              <p className="text-xs font-semibold text-red-800 dark:text-red-200 mt-2">
                ⚠️ Atenção: este produto ainda tem {produto.estoque_atual} unid. em estoque!
              </p>
            )}
          </div>

          {/* Campo de confirmação digitando o nome */}
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Para confirmar, digite o nome do produto:
              <span className="ml-1 font-semibold text-gray-900 dark:text-gray-100">"{nomeEsperado}"</span>
            </label>
            <input
              type="text"
              value={confirmacaoTexto}
              onChange={(e) => setConfirmacaoTexto(e.target.value)}
              placeholder="Digite o nome exato do produto"
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 transition-colors
                ${confirmacaoCorreta
                  ? 'border-red-400 dark:border-red-500 focus:ring-red-400 bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200'
                  : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-red-400'
                }`}
              autoComplete="off"
            />
            {confirmacaoTexto.length > 0 && !confirmacaoCorreta && (
              <p className="mt-1 text-xs text-red-500">Nome não confere. Digite exatamente como mostrado acima.</p>
            )}
          </div>
        </div>

        <div className="px-6 pb-5 flex gap-3 justify-end">
          <button
            type="button"
            onClick={onCancelar}
            disabled={isPending}
            className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 transition disabled:opacity-60"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onConfirmar}
            disabled={!confirmacaoCorreta || isPending}
            className="rounded-lg bg-red-600 px-5 py-2 text-sm font-semibold text-white hover:bg-red-700 transition disabled:opacity-40 flex items-center gap-2"
          >
            {isPending
              ? <><span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />Excluindo...</>
              : '🗑️ Excluir permanentemente'
            }
          </button>
        </div>
      </div>
    </div>
  )
}

const Produtos = () => {
  const queryClient = useQueryClient()
  const [searchInput, setSearchInput] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(1)
  const [incluirInativos, setIncluirInativos] = useState(false)
  const [categoriaFiltro, setCategoriaFiltro] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<ModalMode>('create')
  const [editingProduto, setEditingProduto] = useState<Produto | null>(null)
  const [formState, setFormState] = useState<FormState>(emptyFormState)
  const [formErrors, setFormErrors] = useState<FormErrors>({})
  const [formError, setFormError] = useState('')

  // ── Estado de exclusão permanente ──
  const [produtoParaExcluir, setProdutoParaExcluir] = useState<Produto | null>(null)

  // ── Estado de IA ──
  const [aiResult, setAiResult] = useState<AiResult>({ status: 'idle' })
  const aiDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const lastCheckedNomeRef = useRef<string>('')

  const produtosQuery = useQuery({
    queryKey: ['produtos', page, searchTerm, incluirInativos, categoriaFiltro],
    queryFn: async () => {
      const response = await api.get('/produtos/', {
        params: {
          page, page_size: PAGE_SIZE, incluir_inativos: incluirInativos,
          search: searchTerm || undefined,
          categoria_id: categoriaFiltro ? Number(categoriaFiltro) : undefined
        }
      })
      return response.data as ProdutoListResponse
    },
    placeholderData: (previousData) => previousData
  })

  const categoriasQuery = useQuery({
    queryKey: ['categorias-arvore'],
    queryFn: async () => {
      const response = await api.get('/categorias/arvore')
      return response.data as CategoriaTreeNode[]
    }
  })

  const produtos = produtosQuery.data?.items ?? []
  const totalPages = Math.max(1, produtosQuery.data?.pages ?? 1)

  const createMutation = useMutation({
    mutationFn: async (payload: ProdutoFormPayload) => {
      const response = await api.post('/produtos/', payload)
      return { data: response.data as Produto, acao: response.headers['x-produto-acao'] ?? 'criado' }
    },
    onSuccess: ({ acao }) => {
      queryClient.invalidateQueries({ queryKey: ['produtos'] })
      closeModal()
      if (acao === 'estoque_somado') {
        toast.success('Produto já existia — estoque somado com sucesso!')
      } else {
        toast.success('Produto criado com sucesso!')
      }
    },
    onError: () => { setFormError('Não foi possível criar o produto. Verifique os dados e tente novamente.') }
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: ProdutoFormPayload }) => {
      const response = await api.put(`/produtos/${id}`, payload)
      return response.data as Produto
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['produtos'] })
      closeModal()
      toast.success('Produto atualizado com sucesso!')
    },
    onError: () => { setFormError('Não foi possível atualizar o produto. Verifique os dados e tente novamente.') }
  })

  const deactivateMutation = useMutation({
    mutationFn: async (id: number) => { await api.delete(`/produtos/${id}`) },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['produtos'] })
      toast.success('Produto desativado com sucesso!')
    }
  })

  const reactivateMutation = useMutation({
    mutationFn: async (id: number) => { await api.post(`/produtos/${id}/reativar`) },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['produtos'] })
      toast.success('Produto reativado com sucesso!')
    }
  })

  const deletePermanenteMutation = useMutation({
    mutationFn: async (id: number) => {
      const response = await api.delete(`/produtos/${id}/permanente`)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['produtos'] })
      setProdutoParaExcluir(null)
      toast.success(data.message ?? 'Produto removido permanentemente.')
    },
    onError: () => {
      toast.error('Não foi possível remover o produto. Tente novamente.')
    }
  })

  const isSaving = createMutation.isPending || updateMutation.isPending
  const modalRef = useAccessibleModal(isModalOpen, closeModal)

  // ── Verificação de IA com debounce ──
  const checkAiDuplicate = async (nome: string) => {
    const nomeTrimmed = nome.trim()
    if (!nomeTrimmed || nomeTrimmed === lastCheckedNomeRef.current) return

    lastCheckedNomeRef.current = nomeTrimmed
    setAiResult({ status: 'checking' })

    try {
      const res = await api.post<DuplicateCheckResponse>('/ai/check-duplicate', {
        descricao: nomeTrimmed, limite: 3,
      })
      const data = res.data

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
      setAiResult({ status: 'idle' })
    }
  }

  const handleNomeChange = (value: string) => {
    handleInputChange('nome', value)
    setAiResult({ status: 'idle' })
    lastCheckedNomeRef.current = ''

    if (aiDebounceRef.current) clearTimeout(aiDebounceRef.current)

    if (value.trim().length >= 3) {
      aiDebounceRef.current = setTimeout(() => checkAiDuplicate(value), 600)
    }
  }

  useEffect(() => {
    if (!isModalOpen && aiDebounceRef.current) clearTimeout(aiDebounceRef.current)
  }, [isModalOpen])

  const openCreateModal = () => {
    setModalMode('create'); setEditingProduto(null); setFormState(emptyFormState)
    setFormErrors({}); setFormError(''); setAiResult({ status: 'idle' }); lastCheckedNomeRef.current = ''
    setIsModalOpen(true)
  }

  const openEditModal = (produto: Produto) => {
    setModalMode('edit'); setEditingProduto(produto)
    setFormState({
      nome: produto.nome ?? '', fornecedor: produto.fornecedor ?? '',
      preco_unitario: String(produto.preco_unitario ?? ''), preco_liquido: String(produto.preco_liquido ?? ''),
      estoque_minimo: String(produto.estoque_minimo ?? 0), quantidade_inicial: '0',
      unidade: produto.unidade ?? '', codigo_ncm: produto.codigo_ncm ?? '', descricao: produto.descricao ?? '',
      unidade_medida: produto.unidade_medida ?? 'UN',
      categoria_id: produto.categoria_id ? String(produto.categoria_id) : '',
      preco_custo: produto.preco_custo != null ? String(produto.preco_custo) : '',
      preco_varejo: produto.preco_varejo != null ? String(produto.preco_varejo) : '',
      preco_atacado: produto.preco_atacado != null ? String(produto.preco_atacado) : '',
      qtd_minima_atacado: produto.qtd_minima_atacado != null ? String(produto.qtd_minima_atacado) : ''
    })
    setFormErrors({}); setFormError(''); setAiResult({ status: 'idle' }); lastCheckedNomeRef.current = ''
    setIsModalOpen(true)
  }

  function closeModal() {
    setIsModalOpen(false); setEditingProduto(null); setFormState(emptyFormState)
    setFormErrors({}); setFormError(''); setAiResult({ status: 'idle' }); lastCheckedNomeRef.current = ''
    if (aiDebounceRef.current) clearTimeout(aiDebounceRef.current)
  }

  const handleSearchSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setPage(1); setSearchTerm(searchInput.trim())
  }

  useEffect(() => {
    const normalizedSearch = searchInput.trim()
    const timeoutId = setTimeout(() => {
      if (normalizedSearch !== searchTerm) { setPage(1); setSearchTerm(normalizedSearch) }
    }, 300)
    return () => clearTimeout(timeoutId)
  }, [searchInput, searchTerm])

  const handleInputChange = (field: keyof FormState, value: string) => {
    setFormState((prev) => ({ ...prev, [field]: value }))
    if (field in formErrors) setFormErrors((prev) => ({ ...prev, [field]: undefined }))
  }

  const validateForm = () => {
    const errors: FormErrors = {}
    if (!formState.nome.trim()) errors.nome = 'Nome é obrigatório.'
    if (!formState.fornecedor.trim()) errors.fornecedor = 'Fornecedor é obrigatório.'
    const precoUnitario = Number(formState.preco_unitario)
    if (!formState.preco_unitario || Number.isNaN(precoUnitario) || precoUnitario <= 0)
      errors.preco_unitario = 'Preço unitário deve ser maior que zero.'
    const precoLiquido = Number(formState.preco_liquido)
    if (!formState.preco_liquido || Number.isNaN(precoLiquido) || precoLiquido <= 0)
      errors.preco_liquido = 'Preço líquido deve ser maior que zero.'
    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const buildPayload = (): ProdutoFormPayload => {
    const payload: ProdutoFormPayload = {
      nome: formState.nome.trim(), fornecedor: formState.fornecedor.trim(),
      preco_unitario: Number(formState.preco_unitario), preco_liquido: Number(formState.preco_liquido),
      estoque_minimo: Math.max(0, Number(formState.estoque_minimo) || 0)
    }
    if (modalMode === 'create') payload.quantidade_inicial = Math.max(0, Number(formState.quantidade_inicial) || 0)
    const unidade = formState.unidade.trim()
    payload.unidade_medida = (formState.unidade_medida || 'UN').trim().toUpperCase()
    if (unidade) payload.unidade = unidade
    if (formState.codigo_ncm.trim()) payload.codigo_ncm = formState.codigo_ncm.trim()
    if (formState.descricao.trim()) payload.descricao = formState.descricao.trim()
    if (formState.categoria_id) payload.categoria_id = Number(formState.categoria_id)
    if (formState.preco_custo !== '') payload.preco_custo = Number(formState.preco_custo)
    if (formState.preco_varejo !== '') payload.preco_varejo = Number(formState.preco_varejo)
    if (formState.preco_atacado !== '') payload.preco_atacado = Number(formState.preco_atacado)
    if (formState.qtd_minima_atacado !== '') payload.qtd_minima_atacado = Number(formState.qtd_minima_atacado)
    return payload
  }

  const flattenCategorias = (nodes: CategoriaTreeNode[], level = 0): Array<{ id: number; nome: string; level: number }> => {
    return nodes.flatMap((node) => [
      { id: node.id, nome: node.nome, level },
      ...flattenCategorias(node.children ?? [], level + 1)
    ])
  }

  const categoriaOptions = flattenCategorias(categoriasQuery.data ?? [])

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setFormError('')
    if (!validateForm()) return
    const payload = buildPayload()
    if (modalMode === 'create') { createMutation.mutate(payload); return }
    if (!editingProduto) { setFormError('Produto inválido para edição.'); return }
    updateMutation.mutate({ id: editingProduto.id, payload })
  }

  const handleToggleStatus = (produto: Produto) => {
    if (produto.ativo) {
      if (!window.confirm(`Deseja desativar o produto "${produto.nome}"?`)) return
      deactivateMutation.mutate(produto.id)
    } else {
      reactivateMutation.mutate(produto.id)
    }
  }

  const nomeInputBorderCls = () => {
    if (aiResult.status === 'duplicata_exata') return 'border-sky-400 dark:border-sky-500 focus:ring-sky-500'
    if (aiResult.status === 'similar' && aiResult.candidato?.nivel === 'duplicata') return 'border-red-400 dark:border-red-500 focus:ring-red-500'
    if (aiResult.status === 'similar') return 'border-amber-400 dark:border-amber-500 focus:ring-amber-500'
    return 'border-gray-300 dark:border-gray-600 focus:ring-blue-500'
  }

  return (
    <div className="container mx-auto">

      {/* Modal de exclusão permanente */}
      {produtoParaExcluir && (
        <ModalExclusao
          produto={produtoParaExcluir}
          isPending={deletePermanenteMutation.isPending}
          onConfirmar={() => deletePermanenteMutation.mutate(produtoParaExcluir.id)}
          onCancelar={() => { if (!deletePermanenteMutation.isPending) setProdutoParaExcluir(null) }}
        />
      )}

      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Produtos</h1>
        <div className="flex flex-wrap items-center gap-2">
          <form onSubmit={handleSearchSubmit} className="flex gap-2">
            <input
              type="text"
              placeholder="Buscar por nome"
              className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
            />
            <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700">Buscar</button>
          </form>

          <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
            <input
              type="checkbox" checked={incluirInativos}
              onChange={(event) => { setPage(1); setIncluirInativos(event.target.checked) }}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Mostrar inativos
          </label>

          <select
            value={categoriaFiltro}
            onChange={(event) => { setPage(1); setCategoriaFiltro(event.target.value) }}
            className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todas categorias</option>
            {categoriaOptions.map((c) => (
              <option key={c.id} value={c.id}>{'— '.repeat(c.level)}{c.nome}</option>
            ))}
          </select>

          <button type="button" onClick={openCreateModal} className="rounded-lg bg-emerald-600 px-4 py-2 text-white transition hover:bg-emerald-700">
            + Novo Produto
          </button>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg bg-white dark:bg-gray-800 shadow">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              {['Nome', 'Fornecedor', 'Preço Unitário', 'Estoque Atual', 'Estoque Mín.', 'Status'].map(h => (
                <th key={h} className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">{h}</th>
              ))}
              <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-800">
            {produtosQuery.isLoading ? (
              <tr><td colSpan={7} className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">Carregando...</td></tr>
            ) : produtosQuery.isError ? (
              <tr><td colSpan={7} className="px-6 py-4 text-center text-red-600">Erro ao carregar produtos.</td></tr>
            ) : produtos.length === 0 ? (
              <tr><td colSpan={7} className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">Nenhum produto encontrado.</td></tr>
            ) : (
              produtos.map((produto) => (
                <tr key={produto.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900 dark:text-gray-100">{produto.nome}</td>
                  <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{produto.fornecedor}</td>
                  <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{moneyFormatter.format(produto.preco_unitario)}</td>
                  <td className={`px-6 py-4 text-sm ${produto.estoque_baixo ? 'font-semibold text-red-600' : 'text-gray-500 dark:text-gray-400'}`}>
                    {produto.estoque_atual}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{produto.estoque_minimo}</td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${produto.ativo ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'}`}>
                      {produto.ativo ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right text-sm">
                    <div className="flex justify-end gap-2">
                      <button type="button" onClick={() => openEditModal(produto)}
                        className="rounded border border-gray-300 dark:border-gray-600 px-3 py-1 text-gray-700 dark:text-gray-300 transition hover:bg-gray-100 dark:hover:bg-gray-700">
                        Editar
                      </button>
                      <button type="button" onClick={() => handleToggleStatus(produto)}
                        disabled={deactivateMutation.isPending || reactivateMutation.isPending}
                        className="rounded border border-gray-300 dark:border-gray-600 px-3 py-1 text-gray-700 dark:text-gray-300 transition hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-60">
                        {produto.ativo ? 'Desativar' : 'Reativar'}
                      </button>
                      <button
                        type="button"
                        onClick={() => setProdutoParaExcluir(produto)}
                        title="Excluir permanentemente"
                        className="rounded border border-red-200 dark:border-red-800 px-3 py-1 text-red-600 dark:text-red-400 transition hover:bg-red-50 dark:hover:bg-red-900/30"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <span className="text-sm text-gray-500 dark:text-gray-400">
          Página {produtosQuery.data?.page ?? page} de {totalPages} — mostrando {produtos.length} registros
        </span>
        <div className="flex gap-2">
          <button type="button" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1 || produtosQuery.isFetching}
            className="rounded border border-gray-300 dark:border-gray-600 px-3 py-1 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40">
            ← Anterior
          </button>
          <button type="button" onClick={() => setPage((p) => p + 1)} disabled={page >= totalPages || produtosQuery.isFetching}
            className="rounded border border-gray-300 dark:border-gray-600 px-3 py-1 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40">
            Próxima →
          </button>
        </div>
      </div>

      {/* ── MODAL DE CRIAÇÃO/EDIÇÃO ── */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4" role="dialog" aria-modal="true" onMouseDown={closeModal}>
          <div ref={modalRef} tabIndex={-1} onMouseDown={(e) => e.stopPropagation()} className="flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-lg bg-white dark:bg-gray-800 shadow-xl">
            <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
              <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                {modalMode === 'create' ? 'Novo produto' : 'Editar produto'}
              </h2>
            </div>

            <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col px-6 py-5">
              <div className="space-y-4 overflow-y-auto pr-1">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  {/* Campo Nome com IA */}
                  <div className="md:col-span-2">
                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="produto-nome">
                      Nome *
                      {aiResult.status === 'checking' && (
                        <span className="ml-2 inline-flex items-center gap-1 text-xs font-normal text-blue-500">
                          <span className="inline-block h-2.5 w-2.5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
                          verificando IA...
                        </span>
                      )}
                    </label>
                    <input
                      id="produto-nome" type="text" value={formState.nome}
                      onChange={(e) => handleNomeChange(e.target.value)}
                      className={`w-full rounded-lg border bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 transition-colors ${nomeInputBorderCls()}`}
                      placeholder="Nome do produto"
                    />
                    {formErrors.nome && <p className="mt-1 text-xs text-red-600">{formErrors.nome}</p>}
                    <AiFeedback result={aiResult} />
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="produto-fornecedor">Fornecedor *</label>
                    <input id="produto-fornecedor" type="text" value={formState.fornecedor} onChange={(e) => handleInputChange('fornecedor', e.target.value)} className={inputCls} placeholder="Nome do fornecedor" />
                    {formErrors.fornecedor && <p className="mt-1 text-xs text-red-600">{formErrors.fornecedor}</p>}
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="produto-categoria">Categoria</label>
                    <select id="produto-categoria" value={formState.categoria_id} onChange={(e) => handleInputChange('categoria_id', e.target.value)} className={inputCls}>
                      <option value="">Sem categoria</option>
                      {categoriaOptions.map((c) => (
                        <option key={c.id} value={c.id}>{'— '.repeat(c.level)}{c.nome}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="produto-preco-unitario">Preço Unitário *</label>
                    <input id="produto-preco-unitario" type="number" min="0.01" step="0.01" value={formState.preco_unitario} onChange={(e) => handleInputChange('preco_unitario', e.target.value)} className={inputCls} />
                    {formErrors.preco_unitario && <p className="mt-1 text-xs text-red-600">{formErrors.preco_unitario}</p>}
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="produto-preco-liquido">Preço Líquido *</label>
                    <input id="produto-preco-liquido" type="number" min="0.01" step="0.01" value={formState.preco_liquido} onChange={(e) => handleInputChange('preco_liquido', e.target.value)} className={inputCls} />
                    {formErrors.preco_liquido && <p className="mt-1 text-xs text-red-600">{formErrors.preco_liquido}</p>}
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="produto-estoque-minimo">Estoque Mínimo</label>
                    <input id="produto-estoque-minimo" type="number" min="0" step="1" value={formState.estoque_minimo} onChange={(e) => handleInputChange('estoque_minimo', e.target.value)} className={inputCls} />
                  </div>
                </div>

                <fieldset className="rounded-lg border border-gray-200 dark:border-gray-600 p-3">
                  <legend className="px-1 text-sm font-medium text-gray-700 dark:text-gray-300">Precificação avançada</legend>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div>
                      <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="produto-preco-custo">Preço de Custo</label>
                      <input id="produto-preco-custo" type="number" min="0" step="0.01" value={formState.preco_custo} onChange={(e) => handleInputChange('preco_custo', e.target.value)} className={inputCls} placeholder="Opcional" />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="produto-preco-varejo">Preço Varejo</label>
                      <input id="produto-preco-varejo" type="number" min="0" step="0.01" value={formState.preco_varejo} onChange={(e) => handleInputChange('preco_varejo', e.target.value)} className={inputCls} placeholder="Opcional" />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="produto-preco-atacado">Preço Atacado</label>
                      <input id="produto-preco-atacado" type="number" min="0" step="0.01" value={formState.preco_atacado} onChange={(e) => handleInputChange('preco_atacado', e.target.value)} className={inputCls} placeholder="Opcional" />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="produto-qtd-minima-atacado">Qtd. mínima para atacado</label>
                      <input id="produto-qtd-minima-atacado" type="number" min="0" step="1" value={formState.qtd_minima_atacado} onChange={(e) => handleInputChange('qtd_minima_atacado', e.target.value)} className={inputCls} placeholder="Opcional" />
                    </div>
                  </div>
                </fieldset>

                {modalMode === 'create' && (
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="produto-estoque-inicial">
                      Estoque Inicial
                      {aiResult.status === 'duplicata_exata' && (
                        <span className="ml-2 text-xs font-normal text-sky-600 dark:text-sky-400">(será somado ao estoque existente)</span>
                      )}
                    </label>
                    <input id="produto-estoque-inicial" type="number" min="0" step="1" value={formState.quantidade_inicial} onChange={(e) => handleInputChange('quantidade_inicial', e.target.value)} className={inputCls} />
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Será registrado como entrada de estoque</p>
                  </div>
                )}

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="produto-unidade-medida">Unidade de medida</label>
                    <select id="produto-unidade-medida" value={formState.unidade_medida} onChange={(e) => handleInputChange('unidade_medida', e.target.value)} className={inputCls}>
                      {['UN', 'CX', 'MT', 'KG', 'LT', 'PC', 'M2', 'M3'].map((u) => (
                        <option key={u} value={u}>{u}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="produto-unidade">Sigla exibida</label>
                    <input id="produto-unidade" type="text" value={formState.unidade} onChange={(e) => handleInputChange('unidade', e.target.value)} className={inputCls} placeholder="UN, KG, CX" />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="produto-codigo-ncm">Código NCM</label>
                    <input id="produto-codigo-ncm" type="text" value={formState.codigo_ncm} onChange={(e) => handleInputChange('codigo_ncm', e.target.value)} className={inputCls} placeholder="Opcional" />
                  </div>
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="produto-descricao">Descrição</label>
                  <textarea id="produto-descricao" value={formState.descricao} onChange={(e) => handleInputChange('descricao', e.target.value)} className={`min-h-24 ${inputCls}`} placeholder="Descrição do produto" />
                </div>
              </div>

              {formError && (
                <div className="rounded-md border border-red-200 bg-red-50 dark:bg-red-900/30 dark:border-red-800 px-3 py-2 text-sm text-red-700 dark:text-red-400">
                  {formError}
                </div>
              )}

              <div className="mt-4 flex shrink-0 justify-end gap-3 border-t border-gray-200 dark:border-gray-700 pt-4">
                <button type="button" onClick={closeModal} disabled={isSaving}
                  className="rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-gray-700 dark:text-gray-300 transition hover:bg-gray-100 dark:hover:bg-gray-700">
                  Cancelar
                </button>
                <button type="submit" disabled={isSaving}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700 disabled:opacity-60">
                  {isSaving ? 'Salvando...' : modalMode === 'create' ? 'Criar produto' : 'Salvar alterações'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Produtos
