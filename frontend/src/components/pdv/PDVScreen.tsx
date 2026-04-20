import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import toast from 'react-hot-toast'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

import api from '../../services/api'

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
  return 0 // quantidade abaixo da menor faixa, sem desconto
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
  forma_pagamento?: number
  desconto_geral: number
  observacao?: string
  autorizacao_terceiro_nome?: string
  autorizacao_terceiro_documento?: string
  autorizacao_terceiro_observacao?: string
  parcelas: number
  pagamentos: {
    forma_pagamento: number
    valor: number
    valor_recebido?: number
  }[]
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
  forma_pagamento?: number | null
  forma_pagamento_label?: string | null
  total_recebido?: number
  troco?: number
  pagamentos?: {
    id?: number
    ordem?: number
    forma_pagamento: number
    forma_pagamento_label?: string | null
    valor: number
    valor_recebido?: number | null
    troco?: number
  }[]
}

interface AlertaPrecoMinimo {
  produto_id: number
  produto_nome: string
  preco_praticado: number
  preco_minimo: number
  prejuizo_estimado: number
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

interface PaymentRow {
  id: string
  forma_pagamento: number
  valor: string
  valor_recebido: string
}

const roundCurrency = (value: number) => Math.round(value * 100) / 100

const createPaymentRow = (partial: Partial<PaymentRow> = {}): PaymentRow => ({
  id: partial.id ?? `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
  forma_pagamento: partial.forma_pagamento ?? 1,
  valor: partial.valor ?? '',
  valor_recebido: partial.valor_recebido ?? ''
})

const isMoneyPayment = (value: number) => value === 1
const isPrazoPayment = (value: number) => value === 6

const calcItemTotal = (item: ItemCarrinho) => {
  const descontoPercentual = Math.min(100, Math.max(0, item.desconto))
  return item.quantidade * item.preco_unitario * (1 - descontoPercentual / 100)
}



const PDVScreen = () => {
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
  const [paymentRows, setPaymentRows] = useState<PaymentRow[]>(() => [createPaymentRow()])
  const [parcelas, setParcelas] = useState(1)
  const [observacao, setObservacao] = useState('')
  const [autorizacaoTerceiroNome, setAutorizacaoTerceiroNome] = useState('')
  const [autorizacaoTerceiroDocumento, setAutorizacaoTerceiroDocumento] = useState('')
  const [autorizacaoTerceiroObservacao, setAutorizacaoTerceiroObservacao] = useState('')
  const [highlightedItemId, setHighlightedItemId] = useState<number | null>(null)
  const [submitError, setSubmitError] = useState('')
  const [saleResult, setSaleResult] = useState<VendaPDVRead | null>(null)
  const [politicasDesconto, setPoliticasDesconto] = useState<Record<number, FaixaDesconto[]>>({})

  // Verificaçãoo de preço mínimo
  const [alertasPreco, setAlertasPreco] = useState<AlertaPrecoMinimo[]>([])
  const [showPrecoModal, setShowPrecoModal] = useState(false)
  const [checkingPreco, setCheckingPreco] = useState(false)
  const pendingSalePayloadRef = useRef<VendaPDVCreate | null>(null)

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
        // silencioso: desconto livre em caso de falha
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
  const totalVenda = roundCurrency(Math.max(0, subtotal - descontoGeralNumber))
  const resolvedPaymentRows = useMemo(() => {
    return paymentRows.map((row, index) => {
      const parsedValue = Number(row.valor)
      const valor = roundCurrency(
        paymentRows.length === 1 && row.valor.trim() === ''
          ? totalVenda
          : Math.max(0, Number.isNaN(parsedValue) ? 0 : parsedValue)
      )

      if (!isMoneyPayment(row.forma_pagamento)) {
        return {
          ...row,
          ordem: index + 1,
          valor,
          valor_recebido: undefined as number | undefined
        }
      }

      const parsedReceived = Number(row.valor_recebido)
      const valorRecebido = roundCurrency(
        row.valor_recebido.trim() === ''
          ? valor
          : Math.max(0, Number.isNaN(parsedReceived) ? 0 : parsedReceived)
      )

      return {
        ...row,
        ordem: index + 1,
        valor,
        valor_recebido: valorRecebido
      }
    })
  }, [paymentRows, totalVenda])
  const totalInformado = useMemo(
    () => roundCurrency(resolvedPaymentRows.reduce((acc, row) => acc + row.valor, 0)),
    [resolvedPaymentRows]
  )
  const restantePagamento = roundCurrency(Math.max(0, totalVenda - totalInformado))
  const excessoPagamento = roundCurrency(Math.max(0, totalInformado - totalVenda))
  const trocoPrevisto = useMemo(
    () => roundCurrency(
      resolvedPaymentRows.reduce((acc, row) => {
        if (!isMoneyPayment(row.forma_pagamento)) {
          return acc
        }
        return acc + Math.max(0, (row.valor_recebido ?? row.valor) - row.valor)
      }, 0)
    ),
    [resolvedPaymentRows]
  )
  const hasPrazoRow = paymentRows.some((row) => isPrazoPayment(row.forma_pagamento))
  const isPrazoOnly = paymentRows.length === 1 && hasPrazoRow
  const paymentValidationError = useMemo(() => {
    if (hasPrazoRow && paymentRows.length > 1) {
      return 'Pagamento a prazo nao pode ser combinado com outras formas.'
    }

    for (const row of resolvedPaymentRows) {
      if (isMoneyPayment(row.forma_pagamento) && (row.valor_recebido ?? row.valor) + 0.01 < row.valor) {
        return 'Valor recebido em dinheiro nao pode ser menor que o valor da parcela.'
      }
    }

    if (excessoPagamento > 0.01) {
      return 'Os pagamentos excedem o valor total da venda.'
    }
    if (restantePagamento > 0.01) {
      return 'Os pagamentos ainda nao cobrem o valor total da venda.'
    }
    return ''
  }, [excessoPagamento, hasPrazoRow, paymentRows.length, resolvedPaymentRows, restantePagamento])

  const resetSale = () => {
    setCartItems([])
    setSelectedClient(null)
    setClientSearchInput('')
    setDebouncedClientSearch('')
    setProductSearch('')
    setDescontoGeral('')
    setPaymentRows([createPaymentRow()])
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

  // Atalho global F2 para foco no campo de codigo de barras
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

  // Detecta rajada de scanner: se a digitacao chegar em menos de 80 ms, limpa o texto antigo
  const handleBarcodeChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const now = Date.now()
    const elapsed = now - lastKeystrokeRef.current
    lastKeystrokeRef.current = now

    if (elapsed > 500 && barcodeInput.length > 0) {
      // Primeira tecla apos pausa longa com texto no campo: assume novo scanner e limpa
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

  const updatePaymentRow = (
    rowId: string,
    field: 'forma_pagamento' | 'valor' | 'valor_recebido',
    value: string,
  ) => {
    setPaymentRows((previous) =>
      previous.map((row) => {
        if (row.id !== rowId) {
          return row
        }
        if (field === 'forma_pagamento') {
          const nextPaymentType = Number(value)
          return {
            ...row,
            forma_pagamento: nextPaymentType,
            valor_recebido: isMoneyPayment(nextPaymentType) ? row.valor_recebido : ''
          }
        }
        return {
          ...row,
          [field]: value
        }
      })
    )
  }

  const addPaymentRow = () => {
    setPaymentRows((previous) => [
      ...previous,
      createPaymentRow({
        forma_pagamento: 4,
        valor: restantePagamento > 0 ? restantePagamento.toFixed(2) : ''
      })
    ])
  }

  const removePaymentRow = (rowId: string) => {
    setPaymentRows((previous) => {
      if (previous.length === 1) {
        return previous
      }
      return previous.filter((row) => row.id !== rowId)
    })
  }

  const buildPayload = (): VendaPDVCreate => {
    const pagamentos = resolvedPaymentRows
      .filter((row) => row.valor > 0 || (resolvedPaymentRows.length === 1 && totalVenda === 0))
      .map((row) => ({
        forma_pagamento: row.forma_pagamento,
        valor: row.valor,
        ...(isMoneyPayment(row.forma_pagamento) ? { valor_recebido: row.valor_recebido } : {})
      }))

    const payload: VendaPDVCreate = {
      desconto_geral: descontoGeralNumber,
      parcelas: isPrazoOnly ? Math.max(1, parcelas) : 1,
      pagamentos,
      itens: cartItems.map((item) => ({
        produto_id: item.produto.id,
        quantidade: item.quantidade,
        preco_unitario: item.preco_unitario,
        desconto: item.desconto
      }))
    }

    if (pagamentos.length === 1) {
      payload.forma_pagamento = pagamentos[0].forma_pagamento
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
    return payload
  }

  const confirmSale = (payload: VendaPDVCreate) => {
    setShowPrecoModal(false)
    setAlertasPreco([])
    pendingSalePayloadRef.current = null
    vendaMutation.mutate(payload)
  }

  const handleSubmitSale = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSubmitError('')

    if (cartItems.length === 0) {
      return
    }

    if (paymentValidationError) {
      setSubmitError(paymentValidationError)
      return
    }

    const payload = buildPayload()

    // Verificaçãoo de preço mínimo antes de finalizar
    setCheckingPreco(true)
    try {
      const res = await api.post('/pdv/verificar-preco', {
        itens: payload.itens
      })
      const data = res.data as { alertas: AlertaPrecoMinimo[]; tem_alertas: boolean }

      if (data.tem_alertas && data.alertas.length > 0) {
        setAlertasPreco(data.alertas)
        pendingSalePayloadRef.current = payload
        setShowPrecoModal(true)
        setCheckingPreco(false)
        return
      }
    } catch {
      // Se a verificaçãoo falhar, prossegue sem bloquear
    }
    setCheckingPreco(false)

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
          <span className="text-xl">!</span>
          <div>
            <p className="font-semibold text-sm">Caixa nao esta aberto</p>
            <p className="text-xs">As vendas serao bloqueadas. <a href="/caixa" className="underline font-medium">Abrir o caixa agora</a></p>
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
                      {moneyFormatter.format(produto.preco_unitario)} - Estoque: {formatQuantidade(produto, produto.estoque_atual)}
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
                  aria-label="Limpar cliente selecionado"
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md px-2 py-1 text-xs font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-700 dark:hover:text-gray-100"
                >
                  Limpar
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
                    Observaçãoo atual: {selectedClient.observacao}
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
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Carrinho e finalizaçãoo</h2>

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
                          aria-label={`Remover ${item.produto.nome} do carrinho`}
                          className="rounded-md px-2 py-1 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-900/40"
                        >
                          Remover
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
                  value={paymentRows[0]?.forma_pagamento ?? 1}
                  onChange={(event) => updatePaymentRow(paymentRows[0].id, 'forma_pagamento', event.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
                >
                  {paymentOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Composicao</span>
                  <button
                    type="button"
                    onClick={addPaymentRow}
                    disabled={hasPrazoRow}
                    className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-1.5 text-xs font-semibold text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Adicionar pagamento
                  </button>
                </div>

                {paymentRows.map((row, index) => {
                  const resolvedRow = resolvedPaymentRows[index]
                  const trocoLinha = isMoneyPayment(row.forma_pagamento)
                    ? roundCurrency(Math.max(0, (resolvedRow?.valor_recebido ?? resolvedRow?.valor ?? 0) - (resolvedRow?.valor ?? 0)))
                    : 0

                  return (
                    <div key={row.id} className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/40 p-3">
                      <div className="grid grid-cols-1 gap-3 md:grid-cols-[minmax(0,1.1fr)_minmax(0,0.8fr)_minmax(0,0.8fr)_auto]">
                        <label className="block">
                          <span className="mb-1 block text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Forma</span>
                          <select
                            aria-label={`Forma pagamento ${index + 1}`}
                            value={row.forma_pagamento}
                            onChange={(event) => updatePaymentRow(row.id, 'forma_pagamento', event.target.value)}
                            className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
                          >
                            {paymentOptions.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                        </label>

                        <label className="block">
                          <span className="mb-1 block text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Valor</span>
                          <input
                            aria-label={`Valor pagamento ${index + 1}`}
                            type="number"
                            min={0}
                            step="0.01"
                            value={row.valor}
                            onChange={(event) => updatePaymentRow(row.id, 'valor', event.target.value)}
                            placeholder={paymentRows.length === 1 ? totalVenda.toFixed(2) : '0.00'}
                            className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
                          />
                        </label>

                        {isMoneyPayment(row.forma_pagamento) ? (
                          <label className="block">
                            <span className="mb-1 block text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Recebido</span>
                            <input
                              aria-label={`Recebido pagamento ${index + 1}`}
                              type="number"
                              min={0}
                              step="0.01"
                              value={row.valor_recebido}
                              onChange={(event) => updatePaymentRow(row.id, 'valor_recebido', event.target.value)}
                              placeholder={(resolvedRow?.valor ?? totalVenda).toFixed(2)}
                              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
                            />
                          </label>
                        ) : (
                          <div className="flex items-end">
                            <p className="w-full rounded-lg border border-dashed border-gray-300 dark:border-gray-600 px-3 py-2 text-xs text-gray-500 dark:text-gray-400">
                              Sem troco
                            </p>
                          </div>
                        )}

                        <div className="flex items-end">
                          <button
                            type="button"
                            onClick={() => removePaymentRow(row.id)}
                            disabled={paymentRows.length === 1}
                            className="rounded-lg border border-rose-300 dark:border-rose-700 px-3 py-2 text-xs font-semibold text-rose-700 dark:text-rose-300 hover:bg-rose-50 dark:hover:bg-rose-900/30 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            Remover
                          </button>
                        </div>
                      </div>

                      {isMoneyPayment(row.forma_pagamento) ? (
                        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                          Troco previsto nesta linha: <span className="font-semibold text-gray-700 dark:text-gray-200">{moneyFormatter.format(trocoLinha)}</span>
                        </p>
                      ) : null}
                    </div>
                  )
                })}

                <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                  <div className="rounded-lg bg-gray-50 dark:bg-gray-700 px-3 py-2">
                    <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Informado</p>
                    <p className="font-semibold text-gray-800 dark:text-gray-100">{moneyFormatter.format(totalInformado)}</p>
                  </div>
                  <div className="rounded-lg bg-gray-50 dark:bg-gray-700 px-3 py-2">
                    <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Restante</p>
                    <p className="font-semibold text-gray-800 dark:text-gray-100">{moneyFormatter.format(restantePagamento)}</p>
                  </div>
                  <div className="rounded-lg bg-gray-50 dark:bg-gray-700 px-3 py-2">
                    <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Troco previsto</p>
                    <p className="font-semibold text-gray-800 dark:text-gray-100">{moneyFormatter.format(trocoPrevisto)}</p>
                  </div>
                </div>
              </div>

              {paymentValidationError ? (
                <p className="rounded-lg bg-amber-50 dark:bg-amber-900/30 px-3 py-2 text-sm text-amber-700 dark:text-amber-300">
                  {paymentValidationError}
                </p>
              ) : null}

              {isPrazoOnly ? (
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
                <span className="mb-1 block text-gray-700 dark:text-gray-300">Observaçãoo</span>
                <textarea
                  value={observacao}
                  onChange={(event) => setObservacao(event.target.value)}
                  rows={3}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
                  placeholder="Observaçãoo opcional"
                />
              </label>

              {isPrazoOnly ? (
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
                    <span className="mb-1 block text-gray-700 dark:text-gray-300">Observaçãoo da autorizaçãoo</span>
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
            disabled={cartItems.length === 0 || vendaMutation.isPending || checkingPreco || Boolean(paymentValidationError)}
            className="rounded-lg bg-indigo-600 px-4 py-2 font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {checkingPreco ? 'Verificando preços...' : vendaMutation.isPending ? 'Finalizando...' : 'Finalizar Venda'}
          </button>
        </form>
      </section>

      {/* Modal de alerta de preco minimo */}
            <Dialog
        open={showPrecoModal && alertasPreco.length > 0}
        onOpenChange={(open) => {
          if (!open) {
            setShowPrecoModal(false)
            setAlertasPreco([])
            pendingSalePayloadRef.current = null
          }
        }}
      >
        <DialogContent className="max-w-lg gap-0 overflow-hidden p-0" showCloseButton={false}>
          <DialogHeader className="gap-3 border-b border-amber-200 bg-amber-50 px-6 py-4 dark:border-amber-700 dark:bg-amber-900/30">
            <div className="flex items-start gap-3">
              <div className="flex size-10 items-center justify-center rounded-full bg-amber-100 text-sm font-semibold text-amber-800 dark:bg-amber-800/60 dark:text-amber-100">
                IA
              </div>
              <div className="space-y-1">
                <DialogTitle className="text-amber-900 dark:text-amber-100">
                  Alerta de preco minimo
                </DialogTitle>
                <DialogDescription className="text-xs text-amber-700 dark:text-amber-300">
                  {alertasPreco.length === 1 ? '1 produto esta' : `${alertasPreco.length} produtos estao`} com preco abaixo do custo minimo calculado.
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>

          <div className="max-h-72 space-y-2 overflow-y-auto px-6 py-4">
            {alertasPreco.map((alerta) => (
              <div
                key={alerta.produto_id}
                className="rounded-xl border border-red-200 bg-red-50 p-3 dark:border-red-700 dark:bg-red-900/20"
              >
                <div className="flex items-start gap-3">
                  <span className="mt-0.5 text-lg text-red-600 dark:text-red-300">!</span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-gray-800 dark:text-gray-100">{alerta.produto_nome}</p>
                    <div className="mt-1.5 grid grid-cols-3 gap-2 text-sm">
                      <div>
                        <p className="text-xs text-gray-400 dark:text-gray-500">Praticado</p>
                        <p className="font-semibold text-red-600 dark:text-red-400">
                          {moneyFormatter.format(alerta.preco_praticado)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-400 dark:text-gray-500">Minimo</p>
                        <p className="font-semibold text-gray-700 dark:text-gray-300">
                          {moneyFormatter.format(alerta.preco_minimo)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-400 dark:text-gray-500">Prejuizo</p>
                        <p className="font-semibold text-red-600 dark:text-red-400">
                          -{moneyFormatter.format(alerta.prejuizo_estimado)}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <DialogFooter className="gap-3 border-t border-gray-200 bg-gray-50 px-6 py-4 dark:border-gray-700 dark:bg-gray-700/50">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setShowPrecoModal(false)
                setAlertasPreco([])
                pendingSalePayloadRef.current = null
              }}
            >
              Corrigir precos
            </Button>
            <Button
              type="button"
              className="bg-amber-600 hover:bg-amber-700"
              onClick={() => {
                if (pendingSalePayloadRef.current) confirmSale(pendingSalePayloadRef.current)
              }}
            >
              Vender mesmo assim
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

            <Dialog open={Boolean(saleResult)} onOpenChange={(open) => !open && resetSale()}>
        <DialogContent className="max-w-md gap-0 overflow-hidden p-0" showCloseButton={false}>
          <DialogHeader className="gap-2 border-b px-5 py-4">
            <DialogTitle>Venda concluida</DialogTitle>
            <DialogDescription>
              Revise os dados da venda e gere o comprovante antes de iniciar o proximo atendimento.
            </DialogDescription>
          </DialogHeader>

          {saleResult ? (
            <div className="space-y-4 px-5 py-4 text-sm text-gray-700 dark:text-gray-300">
              <div className="space-y-2">
                <p>
                  Numero da venda: <strong>{saleResult.numero_legado ?? saleResult.id}</strong>
                </p>
                <p>
                  Total: <strong>{moneyFormatter.format(Number(saleResult.total ?? totalVenda))}</strong>
                </p>
                <p>
                  Forma de pagamento: <strong>{saleResult.forma_pagamento_label ?? formatPayment(saleResult.forma_pagamento ?? paymentRows[0]?.forma_pagamento ?? 1)}</strong>
                </p>
                {saleResult.pagamentos && saleResult.pagamentos.length > 0 ? (
                  <div className="space-y-1 rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-700/50">
                    {saleResult.pagamentos.map((pagamento, index) => (
                      <p key={`${pagamento.forma_pagamento}-${index}`}>
                        {(pagamento.forma_pagamento_label ?? formatPayment(pagamento.forma_pagamento))}: <strong>{moneyFormatter.format(pagamento.valor)}</strong>
                      </p>
                    ))}
                  </div>
                ) : null}
              </div>
            </div>
          ) : null}

          <DialogFooter className="gap-3 border-t border-gray-200 bg-gray-50 px-5 py-4 dark:border-gray-700 dark:bg-gray-700/50">
            <Button
              type="button"
              variant="outline"
              className="border-indigo-300 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 dark:border-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 dark:hover:bg-indigo-900/50"
              onClick={() => void imprimirComprovantePdf()}
            >
              Gerar comprovante (PDF)
            </Button>
            <Button type="button" onClick={resetSale}>
              Nova Venda
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default PDVScreen
