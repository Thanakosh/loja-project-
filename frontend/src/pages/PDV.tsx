import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { isAxiosError } from 'axios'

import api from '../services/api'

interface Produto {
  id: number
  nome: string
  preco_unitario: number
  preco_liquido: number
  unidade?: string | null
  estoque_atual: number
  ativo: boolean
}

interface Cliente {
  id: number
  nome: string
  cpf_cnpj?: string | null
}

interface ItemCarrinho {
  produto: Produto
  quantidade: number
  preco_unitario: number
  desconto: number
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
  const [clientSearchInput, setClientSearchInput] = useState('')
  const [debouncedClientSearch, setDebouncedClientSearch] = useState('')
  const [selectedClient, setSelectedClient] = useState<Cliente | null>(null)
  const [cartItems, setCartItems] = useState<ItemCarrinho[]>([])
  const [descontoGeral, setDescontoGeral] = useState('0')
  const [formaPagamento, setFormaPagamento] = useState(1)
  const [parcelas, setParcelas] = useState(1)
  const [observacao, setObservacao] = useState('')
  const [submitError, setSubmitError] = useState('')
  const [saleResult, setSaleResult] = useState<VendaPDVRead | null>(null)

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedClientSearch(clientSearchInput.trim())
    }, 400)

    return () => window.clearTimeout(timeout)
  }, [clientSearchInput])

  const produtosQuery = useQuery({
    queryKey: ['pdv-produtos'],
    queryFn: async () => {
      const response = await api.get('/produtos/', {
        params: {
          page: 1,
          page_size: 200,
          incluir_inativos: false
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

  const vendaMutation = useMutation({
    mutationFn: async (payload: VendaPDVCreate) => {
      const response = await api.post('/pdv/venda', payload)
      return response.data as VendaPDVRead
    },
    onSuccess: (data) => {
      setSaleResult(data)
      setSubmitError('')
    },
    onError: (error) => {
      if (isAxiosError(error)) {
        const detail = error.response?.data?.detail
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

  const produtos = produtosQuery.data?.items?.filter((produto) => produto.ativo) ?? []

  const filteredProducts = useMemo(() => {
    const search = productSearch.trim().toLowerCase()

    if (!search) {
      return produtos
    }

    return produtos.filter((produto) => produto.nome.toLowerCase().includes(search))
  }, [productSearch, produtos])

  const subtotal = useMemo(() => cartItems.reduce((acc, item) => acc + calcItemTotal(item), 0), [cartItems])
  const descontoGeralNumber = Math.max(0, Number(descontoGeral) || 0)
  const totalVenda = Math.max(0, subtotal - descontoGeralNumber)

  const resetSale = () => {
    setCartItems([])
    setSelectedClient(null)
    setClientSearchInput('')
    setDebouncedClientSearch('')
    setProductSearch('')
    setDescontoGeral('0')
    setFormaPagamento(1)
    setParcelas(1)
    setObservacao('')
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
        return previous.map((item) =>
          item.produto.id === produto.id ? { ...item, quantidade: item.quantidade + 1 } : item
        )
      }

      return [
        ...previous,
        {
          produto,
          quantidade: 1,
          preco_unitario: Number(produto.preco_unitario),
          desconto: 0
        }
      ]
    })
  }

  const updateItem = (productId: number, field: 'quantidade' | 'preco_unitario' | 'desconto', value: string) => {
    setCartItems((previous) =>
      previous.map((item) => {
        if (item.produto.id !== productId) {
          return item
        }

        const numericValue = Number(value)

        if (field === 'quantidade') {
          return {
            ...item,
            quantidade: Math.max(1, Number.isNaN(numericValue) ? 1 : Math.floor(numericValue))
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

    vendaMutation.mutate(payload)
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">PDV</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">Registre vendas rápidas e acompanhe o total em tempo real.</p>
      </header>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <section className="rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 p-4 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Produtos</h2>
          <div className="mt-4 space-y-2">
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

          <div className="mt-4 max-h-[26rem] space-y-2 overflow-y-auto pr-1">
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
                      {moneyFormatter.format(produto.preco_unitario)} • Estoque: {produto.estoque_atual}
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

        <section className="rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 p-4 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Cliente (opcional)</h2>

          <div className="mt-4 space-y-2">
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

          <div className="mt-3 rounded-lg bg-gray-50 dark:bg-gray-700 px-3 py-2 text-sm">
            {selectedClient ? (
              <p className="text-gray-700 dark:text-gray-300">
                Cliente selecionado: <span className="font-semibold">{selectedClient.nome}</span>
              </p>
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
                    <tr key={item.produto.id}>
                      <td className="px-3 py-2 font-medium text-gray-800 dark:text-gray-100">{item.produto.nome}</td>
                      <td className="px-3 py-2">
                        <input
                          type="number"
                          min={1}
                          value={item.quantidade}
                          onChange={(event) => updateItem(item.produto.id, 'quantidade', event.target.value)}
                          className="w-20 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-2 py-1"
                        />
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
                        <input
                          type="number"
                          min={0}
                          max={100}
                          step="0.01"
                          value={item.desconto}
                          onChange={(event) => updateItem(item.produto.id, 'desconto', event.target.value)}
                          className="w-24 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-2 py-1"
                        />
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
