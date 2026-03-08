import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import toast from 'react-hot-toast'

import api from '../services/api'

interface Produto {
  id: number
  nome: string
  codigo_barras?: string | null
  preco_unitario: number
  preco_liquido: number
  unidade?: string | null
  unidade_medida?: string | null
  estoque_atual: number
  ativo: boolean
  permite_fracionado?: boolean
  preco_varejo?: number | null
  preco_atacado?: number | null
  qtd_minima_atacado?: number | null
}

interface Cliente {
  id: number
  nome: string
  cpf_cnpj?: string | null
  observacao?: string | null
  historico_observacoes?: string | null
}

interface ItemCarrinho {
  produto: Produto
  quantidade: number
  preco_unitario: number
  desconto: number
}

interface FaixaDesconto {
  id: number
  produto_id: number
  qtd_minima: number
  desconto_maximo_percentual: number
  descricao?: string | null
}

interface PoliticaDescontoProduto {
  produto_id: number
  faixas: FaixaDesconto[]
}

/** Dada uma lista de faixas e a quantidade, retorna o desconto máximo permitido ou null (sem política = livre). */
const getDescontoMaximo = (faixas: FaixaDesconto[] | undefined, quantidade: number): number | null => {
  if (!faixas || faixas.length === 0) return null
  // Faixas ordenadas desc por qtd_minima para pegar a maior faixa aplicável
  const sorted = [...faixas].sort((a, b) => b.qtd_minima - a.qtd_minima)
  for (const f of sorted) {
    if (quantidade >= f.qtd_minima) return f.desconto_maximo_percentual
  }
  return 0 // quantidade abaixo da menor faixa → sem desconto
}

const permiteFracionado = (produto: Produto) => produto.permite_fracionado === true

const getPrecoEfetivo = (produto: Produto, quantidade: number): number => {
  if (
    produto.preco_atacado != null &&
    produto.qtd_minima_atacado != null &&
    quantidade >= produto.qtd_minima_atacado
  ) {
    return produto.preco_atacado
  }
  return produto.preco_varejo ?? produto.preco_unitario
}

const isAtacado = (produto: Produto, quantidade: number): boolean =>
  produto.preco_atacado != null &&
  produto.qtd_minima_atacado != null &&
  quantidade >= produto.qtd_minima_atacado

const formatQuantidade = (produto: Produto, quantidade: number) => {
  const unidade = (produto.unidade_medida ?? produto.unidade ?? 'UN').toUpperCase()
  const valor = permiteFracionado(produto) ? quantidade.toFixed(3).replace(/\.?0+$/, '') : String(Math.trunc(quantidade))
  return `${valor} ${unidade}`
}

interface ProdutoListResponse {
  items: Produto[]
  total: number
  pages: number
}

interface VendaPDVCreate {
  cliente_id?: number
  forma_pagamento: number
  desconto_geral: number
  observacao?: string
  autorizacao_terceiro_nome?: string
  autorizacao_terceiro_documento?: string
  autorizacao_terceiro_observacao?: string
  parcelas: number
  itens: {
    produto_id: number
    quantidade: number
    preco_unitario: number
    desconto: number
  }[]
}

interface VendaPDVRead {
  id: number
  numero_legado?: string | number | null
  total: number
  forma_pagamento: number
}

const paymentOptions = [
  { value: 1, label: 'Dinheiro' },
  { value: 2, label: 'Cartão Débito' },
  { value: 3, label: 'Cartão Crédito' },
  { value: 4, label: 'PIX' },
  { value: 5, label: 'Boleto' },
  { value: 6, label: 'A Prazo' }
]

const moneyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL'
})

const formatPayment = (value: number) => paymentOptions.find((option) => option.value === value)?.label ?? 'Não informado'

const calcItemTotal = (item: ItemCarrinho) => {
  const descontoPercentual = Math.min(100, Math.max(0, item.desconto))
  return item.quantidade * item.preco_unitario * (1 - descontoPercentual / 100)
}



const PDV = () => {
  const [productSearch, setProductSearch] = useState('')
  const [debouncedProductSearch, setDebouncedProductSearch] = useState('')
  const [clientSearchInput, setClientSearchInput] = useState('')
  const [debouncedClientSearch, setDebouncedClientSearch] = useState('')
  const [barcodeInput, setBarcodeInput] = useState('')
  const barcodeRef = useRef<HTMLInputElement>(null)
  const lastKeystrokeRef = useRef<number>(0)
  const [selectedClient, setSelectedClient] = useState<Cliente | null>(null)
  const [cartItems, setCartItems] = useState<ItemCarrinho[]>([])
  const [descontoGeral, setDescontoGeral] = useState('')
  const [formaPagamento, setFormaPagamento] = useState(1)
  const [parcelas, setParcelas] = useState(1)
  const [observacao, setObservacao] = useState('')
  const [autorizacaoTerceiroNome, setAutorizacaoTerceiroNome] = useState('')
  const [autorizacaoTerceiroDocumento, setAutorizacaoTerceiroDocumento] = useState('')
  const [autorizacaoTerceiroObservacao, setAutorizacaoTerceiroObservacao] = useState('')
  const [highlightedItemId, setHighlightedItemId] = useState<number | null>(null)
  const [submitError, setSubmitError] = useState('')
  const [saleResult, setSaleResult] = useState<VendaPDVRead | null>(null)
  const [politicasDesconto, setPoliticasDesconto] = useState<Record<number, FaixaDesconto[]>>({})

  // Busca bulk de políticas de desconto quando o carrinho muda
  const cartProductIds = useMemo(() => cartItems.map((i) => i.produto.id), [cartItems])
  useEffect(() => {
    if (cartProductIds.length === 0) {
      setPoliticasDesconto({})
      return
    }
    const idsToFetch = cartProductIds.filter((id) => !(id in politicasDesconto))
    if (idsToFetch.length === 0) return

    void (async () => {
      try {
        const res = await api.get('/politica-desconto/produtos/bulk', {
          params: { produto_ids: idsToFetch.join(',') }
        })
        const data = res.data as PoliticaDescontoProduto[]
        setPoliticasDesconto((prev) => {
          const next = { ...prev }
          for (const p of data) {
            next[p.produto_id] = p.faixas
          }
          // Marcar produtos sem política retornada
          for (const id of idsToFetch) {
            if (!(id in next)) next[id] = []
          }
          return next
        })
      } catch {
        // silencioso — desconto livre em caso de falha
      }
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cartProductIds.join(',')])

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedProductSearch(productSearch.trim())
    }, 300)

    return () => window.clearTimeout(timeout)
  }, [productSearch])

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedClientSearch(clientSearchInput.trim())
    }, 400)

    return () => window.clearTimeout(timeout)
  }, [clientSearchInput])

  const produtosQuery = useQuery({
    queryKey: ['pdv-produtos', debouncedProductSearch],
    queryFn: async () => {
      const response = await api.get('/produtos/', {
        params: {
          page: 1,
          page_size: 50,
          incluir_inativos: false,
          ...(debouncedProductSearch ? { search: debouncedProductSearch } : {})
        }
      })
      return response.data as ProdutoListResponse
    }
  })

  const clientesQuery = useQuery({
    queryKey: ['pdv-clientes', debouncedClientSearch],
    queryFn: async () => {
      const response = await api.get('/clientes/', {
        params: {
          search: debouncedClientSearch,
          limit: 10
        }
      })
      return response.data as Cliente[]
    },
    enabled: debouncedClientSearch.length > 0 && selectedClient === null
  })

  const caixaQuery = useQuery({
    queryKey: ['caixa-atual'],
    queryFn: async () => {
      try {
        const r = await api.get('/caixa/atual')
        return r.data as { id: number; status: string }
      } catch {
        return null
      }
    },
    retry: false,
  })

  const caixaAberto = caixaQuery.data?.status === 'aberto'

  const vendaMutation = useMutation({
    mutationFn: async (payload: VendaPDVCreate) => {
      const response = await api.post('/pdv/venda', payload)
      return response.data as VendaPDVRead
    },
    onSuccess: (data) => {
      setSaleResult(data)
      setSubmitError('')
      toast.success('Venda finalizada com sucesso!')
    },
    onError: (error) => {
      if (isAxiosError(error)) {
        const detail = error.response?.data?.message ?? error.response?.data?.detail
        if (typeof detail === 'string') {
          setSubmitError(detail)
          return
        }

        if (Array.isArray(detail)) {
          const parsedDetail = detail
            .map((item) => {
              if (typeof item === 'string') {
                return item
              }
              return item?.msg
            })
            .filter(Boolean)
            .join(' | ')
          setSubmitError(parsedDetail || 'Não foi possível finalizar a venda.')
          return
        }
      }

      setSubmitError('Não foi possível finalizar a venda. Tente novamente.')
    }
  })

  const filteredProducts = useMemo(() => {
    return produtosQuery.data?.items?.filter((produto) => produto.ativo) ?? []
  }, [produtosQuery.data?.items])

  const subtotal = useMemo(() => cartItems.reduce((acc, item) => acc + calcItemTotal(item), 0), [cartItems])
  const descontoGeralNumber = Math.max(0, Number(descontoGeral) || 0)
  const totalVenda = Math.max(0, subtotal - descontoGeralNumber)

  const resetSale = () => {
    setCartItems([])
    setSelectedClient(null)
    setClientSearchInput('')
    setDebouncedClientSearch('')
    setProductSearch('')
    setDescontoGeral('')
    setFormaPagamento(1)
    setParcelas(1)
    setObservacao('')
    setAutorizacaoTerceiroNome('')
    setAutorizacaoTerceiroDocumento('')
    setAutorizacaoTerceiroObservacao('')
    setBarcodeInput('')
    setHighlightedItemId(null)
    setSubmitError('')
    setSaleResult(null)
  }

  const addProductToCart = (produto: Produto) => {
    if (produto.estoque_atual <= 0) {
      return
    }

    setCartItems((previous) => {
      const existing = previous.find((item) => item.produto.id === produto.id)

      if (existing) {
        const novaQuantidade = existing.quantidade + 1
        const precoAtualizado = getPrecoEfetivo(produto, novaQuantidade)
        setHighlightedItemId(produto.id)
        window.setTimeout(() => setHighlightedItemId(null), 500)
        toast.success(`Quantidade atualizada: ${formatQuantidade(produto, novaQuantidade)}`)
        return previous.map((item) =>
          item.produto.id === produto.id ? { ...item, quantidade: novaQuantidade, preco_unitario: precoAtualizado } : item
        )
      }

      setHighlightedItemId(produto.id)
      window.setTimeout(() => setHighlightedItemId(null), 500)
      toast.success(`${produto.nome} adicionado ao carrinho`)

      return [
        ...previous,
        {
          produto,
          quantidade: 1,
          preco_unitario: getPrecoEfetivo(produto, 1),
          desconto: 0
        }
      ]
    })
  }

  const handleBarcodeSubmit = async () => {
    const barcode = barcodeInput.trim()
    if (!barcode) {
      return
    }

    try {
      const response = await api.get('/produtos/', {
        params: {
          page: 1,
          page_size: 1,
          incluir_inativos: false,
          barcode
        }
      })

      const result = response.data as ProdutoListResponse
      const produto = result.items?.[0]
      if (!produto) {
        toast.error('Código de barras não encontrado')
        return
      }

      addProductToCart(produto)
      setBarcodeInput('')
      barcodeRef.current?.focus()
    } catch {
      toast.error('Falha ao buscar código de barras')
      barcodeRef.current?.focus()
    }
  }

  // Atalho global F2 → foco no campo de código de barras
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'F2') {
        e.preventDefault()
        barcodeRef.current?.focus()
        barcodeRef.current?.select()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  // Detecta rajada de scanner — se digitação chega em ≤80ms limpa texto antigo
  const handleBarcodeChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const now = Date.now()
    const elapsed = now - lastKeystrokeRef.current
    lastKeystrokeRef.current = now

    if (elapsed > 500 && barcodeInput.length > 0) {
      // Primeira tecla após pausa longa e campo já tem texto → scanner novo, limpa
      setBarcodeInput(e.target.value.slice(-1))
    } else {
      setBarcodeInput(e.target.value)
    }
  }, [barcodeInput.length])

  const updateItem = (productId: number, field: 'quantidade' | 'preco_unitario' | 'desconto', value: string) => {
    setCartItems((previous) =>
      previous.map((item) => {
        if (item.produto.id !== productId) {
          return item
        }

        const numericValue = Number(value)

        if (field === 'quantidade') {
          const newQty = permiteFracionado(item.produto)
            ? Math.max(0.001, Number.isNaN(numericValue) ? 1 : numericValue)
            : Math.max(1, Number.isNaN(numericValue) ? 1 : Math.floor(numericValue))
          return {
            ...item,
            quantidade: newQty,
            preco_unitario: getPrecoEfetivo(item.produto, newQty)
          }
        }

        if (field === 'preco_unitario') {
          return {
            ...item,
            preco_unitario: Math.max(0.01, Number.isNaN(numericValue) ? item.preco_unitario : numericValue)
          }
        }

        return {
          ...item,
          desconto: Math.min(100, Math.max(0, Number.isNaN(numericValue) ? item.desconto : numericValue))
        }
      })
    )
  }

  const removeItem = (productId: number) => {
    setCartItems((previous) => previous.filter((item) => item.produto.id !== productId))
  }

  const decreaseItem = (productId: number) => {
    setCartItems((previous) => {
      const current = previous.find((item) => item.produto.id === productId)
      if (!current) {
        return previous
      }

      const step = permiteFracionado(current.produto) ? 0.001 : 1
      const min = permiteFracionado(current.produto) ? 0.001 : 1
      const nextQty = Number((current.quantidade - step).toFixed(3))

      if (nextQty < min) {
        toast.success(`${current.produto.nome} removido do carrinho`)
        return previous.filter((item) => item.produto.id !== productId)
      }

      setHighlightedItemId(productId)
      window.setTimeout(() => setHighlightedItemId(null), 500)
      toast.success(`Quantidade atualizada: ${formatQuantidade(current.produto, nextQty)}`)

      return previous.map((item) => {
        if (item.produto.id !== productId) {
          return item
        }
        return {
          ...item,
          quantidade: nextQty,
          preco_unitario: getPrecoEfetivo(item.produto, nextQty)
        }
      })
    })
  }

  const imprimirComprovantePdf = async () => {
    if (!saleResult?.id) {
      return
    }

    try {
      const response = await api.get(`/pdv/venda/${saleResult.id}/comprovante`, {
        responseType: 'blob'
      })
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank', 'noopener,noreferrer')
      window.setTimeout(() => URL.revokeObjectURL(url), 15000)
    } catch {
      toast.error('Não foi possível gerar o comprovante em PDF')
    }
  }

  const selectClient = (cliente: Cliente) => {
    setSelectedClient(cliente)
    setClientSearchInput(cliente.nome)
    setDebouncedClientSearch('')
  }

  const clearSelectedClient = () => {
    setSelectedClient(null)
    setClientSearchInput('')
    setDebouncedClientSearch('')
  }

  const handleSubmitSale = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSubmitError('')

    if (cartItems.length === 0) {
      return
    }

    const payload: VendaPDVCreate = {
      forma_pagamento: formaPagamento,
      desconto_geral: descontoGeralNumber,
      parcelas: formaPagamento === 6 ? Math.max(1, parcelas) : 1,
      itens: cartItems.map((item) => ({
        produto_id: item.produto.id,
        quantidade: item.quantidade,
        preco_unitario: item.preco_unitario,
        desconto: item.desconto
      }))
    }

    if (selectedClient) {
      payload.cliente_id = selectedClient.id
    }

    if (observacao.trim()) {
      payload.observacao = observacao.trim()
    }

    if (autorizacaoTerceiroNome.trim()) {
      payload.autorizacao_terceiro_nome = autorizacaoTerceiroNome.trim()
    }
    if (autorizacaoTerceiroDocumento.trim()) {
      payload.autorizacao_terceiro_documento = autorizacaoTerceiroDocumento.trim()
    }
    if (autorizacaoTerceiroObservacao.trim()) {
      payload.autorizacao_terceiro_observacao = autorizacaoTerceiroObservacao.trim()
    }

    vendaMutation.mutate(payload)
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">PDV</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">Registre vendas rápidas e acompanhe o total em tempo real.</p>
      </header>

      {!caixaQuery.isLoading && !caixaAberto && (
        <div className="flex items-center gap-3 rounded-xl border border-yellow-300 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-900/20 px-4 py-3 text-yellow-800 dark:text-yellow-300">
          <span className="text-xl">⚠️</span>
          <div>
            <p className="font-semibold text-sm">Caixa não está aberto</p>
            <p className="text-xs">As vendas serão bloqueadas. <a href="/caixa" className="underline font-medium">Abrir o caixa agora →</a></p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-2 xl:grid-cols-2">
        <section className="rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 p-1.5 shadow-sm flex flex-col gap-1">
          <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-100">Produtos</h2>
          <div className="mt-0.5 space-y-0.5">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="buscar-produto">
              Buscar produto
            </label>
            <input
              id="buscar-produto"
              type="text"
              value={productSearch}
              onChange={(event) => setProductSearch(event.target.value)}
              placeholder="Buscar produto..."
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
            />
          </div>

          <div className="mt-0.5 space-y-0.5">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="codigo-barras">
              Lançar por código de barras
            </label>
            <div className="flex items-center gap-2">
              <input
                ref={barcodeRef}
                id="codigo-barras"
                type="text"
                autoComplete="off"
                value={barcodeInput}
                onChange={handleBarcodeChange}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    event.preventDefault()
                    void handleBarcodeSubmit()
                  }
                }}
                placeholder="Bipe ou digite e pressione Enter (F2 = foco)"
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
              />
              <button
                type="button"
                onClick={() => void handleBarcodeSubmit()}
                className="rounded-lg bg-indigo-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-indigo-700"
              >
                Lançar
              </button>
            </div>
          </div>

          <div className="mt-1 max-h-[4.5rem] space-y-1.5 overflow-y-auto pr-1 sm:max-h-[5rem] xl:max-h-[5.5rem]">
            {produtosQuery.isLoading ? (
              <p className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700 px-3 py-2 text-sm text-gray-500 dark:text-gray-400">Carregando produtos...</p>
            ) : filteredProducts.length === 0 ? (
              <p className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700 px-3 py-2 text-sm text-gray-500 dark:text-gray-400">Nenhum produto encontrado.</p>
            ) : (
              filteredProducts.map((produto) => (
                <button
                  key={produto.id}
                  type="button"
                  onClick={() => addProductToCart(produto)}
                  disabled={produto.estoque_atual <= 0}
                  className="flex w-full items-center justify-between rounded-lg border border-gray-200 dark:border-gray-700 px-3 py-2 text-left transition hover:border-indigo-300 hover:bg-indigo-50 dark:hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-80"
                >
                  <div>
                    <p className="font-medium text-gray-800 dark:text-gray-100">{produto.nome}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {moneyFormatter.format(produto.preco_unitario)} • Estoque: {formatQuantidade(produto, produto.estoque_atual)}
                    </p>
                  </div>
                  {produto.estoque_atual <= 0 ? (
                    <span className="rounded-full bg-rose-100 dark:bg-rose-900/40 px-2 py-1 text-xs font-semibold text-rose-700 dark:text-rose-400">Sem estoque</span>
                  ) : (
                    <span className="rounded-full bg-emerald-100 dark:bg-emerald-900/40 px-2 py-1 text-xs font-semibold text-emerald-700 dark:text-emerald-400">Adicionar</span>
                  )}
                </button>
              ))
            )}
          </div>
        </section>

        <section className="rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 p-1.5 shadow-sm flex flex-col gap-1">
          <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-100">Cliente (opcional)</h2>

          <div className="mt-0.5 space-y-0.5">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="buscar-cliente">
              Buscar cliente
            </label>
            <div className="relative">
              <input
                id="buscar-cliente"
                type="text"
                value={clientSearchInput}
                onChange={(event) => {
                  setClientSearchInput(event.target.value)
                  if (selectedClient) {
                    setSelectedClient(null)
                  }
                }}
                placeholder="Buscar cliente..."
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 pr-10 text-sm outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
              />
              {selectedClient ? (
                <button
                  type="button"
                  onClick={clearSelectedClient}
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md px-2 py-1 text-xs font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-700 dark:hover:text-gray-100"
                >
                  ✕
                </button>
              ) : null}

              {debouncedClientSearch && !selectedClient ? (
                <div className="absolute z-20 mt-1 max-h-56 w-full overflow-y-auto rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 shadow-lg">
                  {clientesQuery.isLoading ? (
                    <p className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">Buscando clientes...</p>
                  ) : (clientesQuery.data ?? []).length === 0 ? (
                    <p className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">Nenhum cliente encontrado.</p>
                  ) : (
                    (clientesQuery.data ?? []).map((cliente) => (
                      <button
                        key={cliente.id}
                        type="button"
                        onClick={() => selectClient(cliente)}
                        className="block w-full border-b border-gray-200 dark:border-gray-700 px-3 py-2 text-left text-sm last:border-b-0 hover:bg-gray-50 dark:hover:bg-gray-700"
                      >
                        <p className="font-medium text-gray-800 dark:text-gray-100">{cliente.nome}</p>
                        {cliente.cpf_cnpj ? <p className="text-xs text-gray-500 dark:text-gray-400">{cliente.cpf_cnpj}</p> : null}
                      </button>
                    ))
                  )}
                </div>
              ) : null}
            </div>
          </div>

          <div className="mt-1 rounded-lg bg-gray-50 dark:bg-gray-700 px-3 py-2 text-sm">
            {selectedClient ? (
              <div className="space-y-1 text-gray-700 dark:text-gray-300">
                <p>
                  Cliente selecionado: <span className="font-semibold">{selectedClient.nome}</span>
                </p>
                {selectedClient.observacao ? (
                  <p className="text-xs rounded-md bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 px-2 py-1 text-amber-700 dark:text-amber-300">
                    Observação atual: {selectedClient.observacao}
                  </p>
                ) : null}
              </div>
            ) : (
              <p className="text-gray-500 dark:text-gray-400">Venda sem cliente</p>
            )}
          </div>
        </section>
      </div>

      <section className="rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 p-4 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Carrinho e finalização</h2>

        <form className="mt-4 space-y-4" onSubmit={handleSubmitSale}>
          <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700 text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                <tr>
                  <th className="px-3 py-2 text-left">Produto</th>
                  <th className="px-3 py-2 text-left">Qtd</th>
                  <th className="px-3 py-2 text-left">Preço Unit.</th>
                  <th className="px-3 py-2 text-left">Desc %</th>
                  <th className="px-3 py-2 text-left">Total</th>
                  <th className="px-3 py-2 text-left">Remover</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-800">
                {cartItems.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-3 py-6 text-center text-gray-500 dark:text-gray-400">
                      Nenhum item adicionado
                    </td>
                  </tr>
                ) : (
                  cartItems.map((item) => (
                    <tr
                      key={item.produto.id}
                      className={
                        highlightedItemId === item.produto.id
                          ? 'bg-indigo-50 dark:bg-indigo-900/20 transition-colors'
                          : ''
                      }
                    >
                      <td className="px-3 py-2 font-medium text-gray-800 dark:text-gray-100">
                        {item.produto.nome}
                        {isAtacado(item.produto, item.quantidade) && (
                          <span className="ml-2 rounded-full bg-amber-100 dark:bg-amber-900/40 px-2 py-0.5 text-xs font-semibold text-amber-700 dark:text-amber-400">Atacado</span>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => decreaseItem(item.produto.id)}
                            className="rounded-md border border-gray-300 dark:border-gray-600 px-2 py-1 font-semibold text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                          >
                            -
                          </button>
                          <input
                            type="number"
                            min={permiteFracionado(item.produto) ? 0.001 : 1}
                            step={permiteFracionado(item.produto) ? 0.001 : 1}
                            value={item.quantidade}
                            onChange={(event) => updateItem(item.produto.id, 'quantidade', event.target.value)}
                            className="w-20 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-2 py-1"
                          />
                          <button
                            type="button"
                            onClick={() => addProductToCart(item.produto)}
                            className="rounded-md border border-gray-300 dark:border-gray-600 px-2 py-1 font-semibold text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                          >
                            +
                          </button>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{(item.produto.unidade_medida ?? item.produto.unidade ?? 'UN').toUpperCase()}</p>
                      </td>
                      <td className="px-3 py-2">
                        <input
                          type="number"
                          min={0.01}
                          step="0.01"
                          value={item.preco_unitario}
                          onChange={(event) => updateItem(item.produto.id, 'preco_unitario', event.target.value)}
                          className="w-28 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-2 py-1"
                        />
                      </td>
                      <td className="px-3 py-2">
                        {(() => {
                          const maxDesc = getDescontoMaximo(politicasDesconto[item.produto.id], item.quantidade)
                          const excedido = maxDesc !== null && item.desconto > maxDesc
                          return (
                            <div>
                              <input
                                type="number"
                                min={0}
                                max={maxDesc !== null ? maxDesc : 100}
                                step="0.01"
                                value={item.desconto === 0 ? '' : item.desconto}
                                onChange={(event) => updateItem(item.produto.id, 'desconto', event.target.value)}
                                placeholder="%"
                                className={`w-24 rounded-md border px-2 py-1 ${excedido
                                    ? 'border-rose-500 bg-rose-50 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300'
                                    : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100'
                                  }`}
                              />
                              {maxDesc !== null && (
                                <p className={`text-xs mt-0.5 ${excedido ? 'text-rose-500 font-semibold' : 'text-gray-400 dark:text-gray-500'}`}>
                                  máx {maxDesc}%
                                </p>
                              )}
                            </div>
                          )
                        })()}
                      </td>
                      <td className="px-3 py-2 font-semibold text-gray-700 dark:text-gray-300">{moneyFormatter.format(calcItemTotal(item))}</td>
                      <td className="px-3 py-2">
                        <button
                          type="button"
                          onClick={() => removeItem(item.produto.id)}
                          className="rounded-md px-2 py-1 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-900/40"
                        >
                          ✕
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="space-y-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700 p-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-300">Subtotal</span>
                <strong className="text-gray-800 dark:text-gray-100">{moneyFormatter.format(subtotal)}</strong>
              </div>
              <label className="block">
                <span className="mb-1 block text-gray-700 dark:text-gray-300">Desconto Geral (R$)</span>
                <input
                  type="number"
                  min={0}
                  step="0.01"
                  value={descontoGeral}
                  onChange={(event) => setDescontoGeral(event.target.value)}
                  placeholder="Informe o desconto"
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
                />
              </label>
              <div className="flex items-center justify-between rounded-md bg-indigo-600 px-3 py-2 text-white">
                <span className="font-medium">Total</span>
                <strong className="text-lg">{moneyFormatter.format(totalVenda)}</strong>
              </div>
            </div>

            <div className="space-y-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 p-3 text-sm">
              <label className="block">
                <span className="mb-1 block text-gray-700 dark:text-gray-300">Forma de Pagamento</span>
                <select
                  value={formaPagamento}
                  onChange={(event) => setFormaPagamento(Number(event.target.value))}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
                >
                  {paymentOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              {formaPagamento === 6 ? (
                <label className="block">
                  <span className="mb-1 block text-gray-700 dark:text-gray-300">Parcelas</span>
                  <input
                    type="number"
                    min={1}
                    value={parcelas}
                    onChange={(event) => setParcelas(Math.max(1, Number(event.target.value) || 1))}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
                  />
                </label>
              ) : null}

              <label className="block">
                <span className="mb-1 block text-gray-700 dark:text-gray-300">Observação</span>
                <textarea
                  value={observacao}
                  onChange={(event) => setObservacao(event.target.value)}
                  rows={3}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
                  placeholder="Observação opcional"
                />
              </label>

              {formaPagamento === 6 ? (
                <>
                  <label className="block">
                    <span className="mb-1 block text-gray-700 dark:text-gray-300">Autorizado por (nome)</span>
                    <input
                      type="text"
                      value={autorizacaoTerceiroNome}
                      onChange={(event) => setAutorizacaoTerceiroNome(event.target.value)}
                      className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
                      placeholder="Ex.: Zé Eletricista"
                    />
                  </label>
                  <label className="block">
                    <span className="mb-1 block text-gray-700 dark:text-gray-300">Documento (opcional)</span>
                    <input
                      type="text"
                      value={autorizacaoTerceiroDocumento}
                      onChange={(event) => setAutorizacaoTerceiroDocumento(event.target.value)}
                      className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
                      placeholder="CPF/RG"
                    />
                  </label>
                  <label className="block">
                    <span className="mb-1 block text-gray-700 dark:text-gray-300">Observação da autorização</span>
                    <textarea
                      value={autorizacaoTerceiroObservacao}
                      onChange={(event) => setAutorizacaoTerceiroObservacao(event.target.value)}
                      rows={2}
                      className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
                      placeholder="Ex.: autorizado a retirar materiais no prazo"
                    />
                  </label>
                </>
              ) : null}
            </div>
          </div>

          {submitError ? <p className="rounded-lg bg-rose-50 dark:bg-rose-900/40 px-3 py-2 text-sm text-rose-700 dark:text-rose-400">{submitError}</p> : null}

          <button
            type="submit"
            disabled={cartItems.length === 0 || vendaMutation.isPending}
            className="rounded-lg bg-indigo-600 px-4 py-2 font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {vendaMutation.isPending ? 'Finalizando...' : 'Finalizar Venda'}
          </button>
        </form>
      </section>

      {saleResult ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 px-4">
          <div className="w-full max-w-md rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-5 shadow-2xl">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Venda concluída</h3>
            <div className="mt-3 space-y-2 text-sm text-gray-700 dark:text-gray-300">
              <p>
                Número da venda: <strong>{saleResult.numero_legado ?? saleResult.id}</strong>
              </p>
              <p>
                Total: <strong>{moneyFormatter.format(Number(saleResult.total ?? totalVenda))}</strong>
              </p>
              <p>
                Forma de pagamento: <strong>{formatPayment(saleResult.forma_pagamento ?? formaPagamento)}</strong>
              </p>
            </div>

            <button
              type="button"
              onClick={() => void imprimirComprovantePdf()}
              className="mt-4 w-full rounded-lg border border-indigo-300 dark:border-indigo-700 bg-indigo-50 dark:bg-indigo-900/30 px-4 py-2 font-semibold text-indigo-700 dark:text-indigo-300 transition hover:bg-indigo-100 dark:hover:bg-indigo-900/50"
            >
              Gerar comprovante (PDF)
            </button>

            <button
              type="button"
              onClick={resetSale}
              className="mt-5 w-full rounded-lg bg-emerald-600 px-4 py-2 font-semibold text-white transition hover:bg-emerald-700"
            >
              Nova Venda
            </button>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default PDV
