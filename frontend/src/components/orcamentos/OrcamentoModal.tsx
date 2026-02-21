import { useMemo, useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'

import api from '../../services/api'

interface Cliente {
    id: number
    nome: string
    cpf_cnpj?: string | null
}

interface Produto {
    id: number
    nome: string
    preco_unitario: number
    estoque_atual: number
    ativo: boolean
}

interface ProdutoListResponse {
    items: Produto[]
    total: number
    pages: number
}

interface OrcamentoItem {
    produto_id: number | null
    descricao: string
    quantidade: number
    preco_unitario: number
    desconto: number
    preco_total: number
}

interface Orcamento {
    id: number
    cliente_id: number | null
    cliente_nome: string | null
    desconto_geral: number
    observacao: string | null
    data_validade: string | null
    status: number
    data_criacao: string
    itens: OrcamentoItem[]
}

interface OrcamentoModalProps {
    isOpen: boolean
    onClose: () => void
    orcamentoToEdit: Orcamento | null
}

const moneyFormatter = new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
})

const calcItemTotal = (item: Omit<OrcamentoItem, 'preco_total'>) => {
    const descontoPercentual = Math.min(100, Math.max(0, item.desconto))
    return item.quantidade * item.preco_unitario * (1 - descontoPercentual / 100)
}

export default function OrcamentoModal({ isOpen, onClose, orcamentoToEdit }: OrcamentoModalProps) {
    const queryClient = useQueryClient()
    const isEditing = !!orcamentoToEdit

    // Form State
    const [clienteId, setClienteId] = useState<number | null>(null)
    const [clienteNome, setClienteNome] = useState('')
    const [dataValidade, setDataValidade] = useState('')
    const [observacao, setObservacao] = useState('')
    const [descontoGeral, setDescontoGeral] = useState('0')
    const [cartItems, setCartItems] = useState<Omit<OrcamentoItem, 'preco_total'>[]>([])
    const [submitError, setSubmitError] = useState('')

    // Search state
    const [productSearch, setProductSearch] = useState('')
    const [clientSearchInput, setClientSearchInput] = useState('')
    const [debouncedClientSearch, setDebouncedClientSearch] = useState('')

    useEffect(() => {
        if (isOpen && orcamentoToEdit) {
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setClienteId(orcamentoToEdit.cliente_id)
            setClienteNome(orcamentoToEdit.cliente_nome ?? '')
            setClientSearchInput(orcamentoToEdit.cliente_nome ?? '')
            setDataValidade(orcamentoToEdit.data_validade ? orcamentoToEdit.data_validade.split('T')[0] : '')
            setObservacao(orcamentoToEdit.observacao ?? '')
            setDescontoGeral(String(orcamentoToEdit.desconto_geral))

            const mappedItems = orcamentoToEdit.itens.map(it => ({
                produto_id: it.produto_id,
                descricao: it.descricao,
                quantidade: it.quantidade,
                preco_unitario: it.preco_unitario,
                desconto: it.desconto
            }))
            setCartItems(mappedItems)
        } else if (isOpen) {
            // Reset form on new
            setClienteId(null)
            setClienteNome('')
            setClientSearchInput('')
            setDataValidade('')
            setObservacao('')
            setDescontoGeral('0')
            setCartItems([])
            setSubmitError('')
        }
    }, [isOpen, orcamentoToEdit])

    useEffect(() => {
        const timeout = window.setTimeout(() => {
            setDebouncedClientSearch(clientSearchInput.trim())
        }, 400)
        return () => window.clearTimeout(timeout)
    }, [clientSearchInput])

    const produtosQuery = useQuery({
        queryKey: ['orcamento-produtos'],
        queryFn: async () => {
            const response = await api.get('/produtos/', {
                params: { page: 1, page_size: 200, incluir_inativos: false }
            })
            return response.data as ProdutoListResponse
        },
        enabled: isOpen
    })

    const clientesQuery = useQuery({
        queryKey: ['orcamento-clientes', debouncedClientSearch],
        queryFn: async () => {
            const response = await api.get('/clientes/', {
                params: { search: debouncedClientSearch, limit: 10 }
            })
            return response.data as Cliente[]
        },
        enabled: isOpen && debouncedClientSearch.length > 0 && !clienteId
    })

    const saveMutation = useMutation({
        mutationFn: async (payload: Record<string, unknown>) => {
            if (isEditing) {
                const response = await api.put(`/orcamento/${orcamentoToEdit.id}`, payload)
                return response.data
            } else {
                const response = await api.post('/orcamento/', payload)
                return response.data
            }
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['orcamentos'] })
            onClose()
        },
        onError: (error) => {
            if (isAxiosError(error)) {
                const detail = error.response?.data?.detail
                setSubmitError(typeof detail === 'string' ? detail : 'Erro ao salvar. Verifique os dados.')
            } else {
                setSubmitError('Erro inesperado tentar salvar o orçamento.')
            }
        }
    })

    const filteredProducts = useMemo(() => {
        const pList = produtosQuery.data?.items?.filter((p) => p.ativo) ?? []
        const search = productSearch.trim().toLowerCase()
        if (!search) return pList
        return pList.filter((p) => p.nome.toLowerCase().includes(search))
    }, [productSearch, produtosQuery.data?.items])

    const subtotal = useMemo(() => cartItems.reduce((acc, item) => acc + calcItemTotal(item), 0), [cartItems])
    const descontoGeralNumber = Math.max(0, Number(descontoGeral) || 0)
    const totalOrcamento = Math.max(0, subtotal - descontoGeralNumber)

    const addProductToCart = (produto: Produto) => {
        setCartItems((previous) => {
            const existing = previous.find((item) => item.produto_id === produto.id)
            if (existing) {
                return previous.map((item) =>
                    item.produto_id === produto.id ? { ...item, quantidade: item.quantidade + 1 } : item
                )
            }
            return [
                ...previous,
                {
                    produto_id: produto.id,
                    descricao: produto.nome,
                    quantidade: 1,
                    preco_unitario: Number(produto.preco_unitario),
                    desconto: 0
                }
            ]
        })
    }

    const updateItem = (index: number, field: 'quantidade' | 'preco_unitario' | 'desconto', value: string) => {
        setCartItems((previous) =>
            previous.map((item, i) => {
                if (i !== index) return item
                const numericValue = Number(value)
                if (field === 'quantidade') {
                    return { ...item, quantidade: Math.max(1, Number.isNaN(numericValue) ? 1 : Math.floor(numericValue)) }
                }
                if (field === 'preco_unitario') {
                    return { ...item, preco_unitario: Math.max(0.01, Number.isNaN(numericValue) ? item.preco_unitario : numericValue) }
                }
                return { ...item, desconto: Math.min(100, Math.max(0, Number.isNaN(numericValue) ? item.desconto : numericValue)) }
            })
        )
    }

    const removeItem = (index: number) => {
        setCartItems((previous) => previous.filter((_, i) => i !== index))
    }

    const selectClient = (cliente: Cliente) => {
        setClienteId(cliente.id)
        setClienteNome(cliente.nome)
        setClientSearchInput(cliente.nome)
        setDebouncedClientSearch('')
    }

    const handleClientNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setClientSearchInput(e.target.value)
        if (clienteId) {
            setClienteId(null)
        }
    }

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        setSubmitError('')

        if (cartItems.length === 0) {
            setSubmitError('Adicione pelo menos um item ao orçamento.')
            return
        }

        if (!clienteId && !clientSearchInput.trim()) {
            setSubmitError('Obrigatório informar o nome do cliente ou selecionar um cliente existente.')
            return
        }

        const payload: Record<string, unknown> = {
            cliente_id: clienteId || null,
            cliente_nome: clienteId ? clienteNome : clientSearchInput.trim(),
            desconto_geral: descontoGeralNumber,
            itens: cartItems
        }

        if (observacao.trim()) {
            payload.observacao = observacao.trim()
        }
        if (dataValidade) {
            payload.data_validade = dataValidade
        }

        saveMutation.mutate(payload)
    }

    if (!isOpen) return null

    // Se o orçamento aberto não estiver com status 1 (Aberto), desabilita a edição de campos 
    // no backend também daria erro. Mas protegemos no frontend visualmente.
    const isReadOnly = isEditing && orcamentoToEdit?.status !== 1

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 py-8">
            <div className="flex h-full max-h-[90vh] w-full max-w-5xl flex-col rounded-xl bg-white shadow-2xl">
                <div className="flex items-center justify-between border-b px-6 py-4">
                    <h2 className="text-xl font-semibold text-gray-800">
                        {isEditing ? (isReadOnly ? `Detalhes do Orçamento #${orcamentoToEdit.id}` : `Editar Orçamento #${orcamentoToEdit.id}`) : 'Novo Orçamento'}
                    </h2>
                    <button
                        type="button"
                        onClick={onClose}
                        className="rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                    >
                        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto px-6 py-4">
                    <form id="orcamento-form" onSubmit={handleSubmit} className="space-y-6">
                        {/* Header info */}
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                            <div className="relative col-span-1 lg:col-span-2">
                                <label className="mb-1 block text-sm font-medium text-gray-700">Cliente *</label>
                                <input
                                    type="text"
                                    value={clientSearchInput}
                                    onChange={handleClientNameChange}
                                    disabled={isReadOnly}
                                    placeholder="Selecione ou digite um nome"
                                    className="w-full rounded-lg border px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-50"
                                />
                                {!isReadOnly && debouncedClientSearch && !clienteId && (
                                    <div className="absolute z-20 mt-1 max-h-40 w-full overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-lg">
                                        {clientesQuery.isLoading ? (
                                            <p className="px-3 py-2 text-sm text-gray-500">Buscando...</p>
                                        ) : (clientesQuery.data ?? []).length === 0 ? (
                                            <p className="px-3 py-2 text-sm text-gray-500">Nenhum cliente cadastrado. Usará como cliente avulso.</p>
                                        ) : (
                                            (clientesQuery.data ?? []).map((cliente) => (
                                                <button
                                                    key={cliente.id}
                                                    type="button"
                                                    onClick={() => selectClient(cliente)}
                                                    className="w-full border-b border-gray-100 px-3 py-2 text-left text-sm hover:bg-gray-50"
                                                >
                                                    <span className="font-medium">{cliente.nome}</span>
                                                    {cliente.cpf_cnpj && <span className="ml-2 text-xs text-gray-500">{cliente.cpf_cnpj}</span>}
                                                </button>
                                            ))
                                        )}
                                    </div>
                                )}
                                {clienteId && (
                                    <p className="mt-1 text-xs text-emerald-600 font-medium">✨ Cliente vinculado ao cadastro</p>
                                )}
                            </div>

                            <div>
                                <label className="mb-1 block text-sm font-medium text-gray-700">Validade</label>
                                <input
                                    type="date"
                                    value={dataValidade}
                                    onChange={(e) => setDataValidade(e.target.value)}
                                    disabled={isReadOnly}
                                    className="w-full rounded-lg border px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-50"
                                />
                            </div>

                            <div className="col-span-1 md:col-span-2 lg:col-span-3">
                                <label className="mb-1 block text-sm font-medium text-gray-700">Observação</label>
                                <input
                                    type="text"
                                    value={observacao}
                                    onChange={(e) => setObservacao(e.target.value)}
                                    disabled={isReadOnly}
                                    placeholder="Informações adicionais do orçamento"
                                    className="w-full rounded-lg border px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-50"
                                />
                            </div>
                        </div>

                        {/* Split view: Add Products / Cart */}
                        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                            {!isReadOnly && (
                                <div className="rounded-xl border border-gray-200 p-4">
                                    <h3 className="mb-3 font-medium text-gray-800">1. Buscar Produtos</h3>
                                    <input
                                        type="text"
                                        value={productSearch}
                                        onChange={(e) => setProductSearch(e.target.value)}
                                        placeholder="Filtrar por nome..."
                                        className="mb-3 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                                    />
                                    <div className="max-h-64 overflow-y-auto pr-2 space-y-2 scrollbar-thin scrollbar-thumb-gray-300">
                                        {produtosQuery.isLoading ? (
                                            <p className="text-sm text-gray-500">Carregando...</p>
                                        ) : filteredProducts.length === 0 ? (
                                            <p className="text-sm text-gray-500">Nenhum produto encontrado.</p>
                                        ) : (
                                            filteredProducts.map((produto) => (
                                                <button
                                                    key={produto.id}
                                                    type="button"
                                                    onClick={() => addProductToCart(produto)}
                                                    className="flex w-full items-center justify-between rounded-lg border border-gray-200 px-3 py-2 text-left transition hover:bg-blue-50 hover:border-blue-200"
                                                >
                                                    <div>
                                                        <p className="font-medium text-gray-900">{produto.nome}</p>
                                                        <p className="text-xs text-gray-500">{moneyFormatter.format(produto.preco_unitario)}</p>
                                                    </div>
                                                    <span className="rounded-md bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-700">+ Add</span>
                                                </button>
                                            ))
                                        )}
                                    </div>
                                </div>
                            )}

                            <div className={`rounded-xl border border-gray-200 p-4 ${isReadOnly ? 'lg:col-span-2' : ''}`}>
                                <h3 className="mb-3 font-medium text-gray-800">
                                    {!isReadOnly ? '2. Itens do Orçamento' : 'Itens do Orçamento'}
                                </h3>
                                <div className="overflow-x-auto rounded-lg border border-gray-200">
                                    <table className="min-w-full divide-y divide-gray-200 text-sm">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th className="px-3 py-2 text-left font-medium text-gray-500">Produto</th>
                                                <th className="px-3 py-2 text-left font-medium text-gray-500 w-20">Qtd</th>
                                                <th className="px-3 py-2 text-left font-medium text-gray-500 w-24">Unit (R$)</th>
                                                <th className="px-3 py-2 text-left font-medium text-gray-500 w-20">Desc%</th>
                                                <th className="px-3 py-2 text-left font-medium text-gray-500">Total</th>
                                                {!isReadOnly && <th className="px-3 py-2"></th>}
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-100 bg-white">
                                            {cartItems.length === 0 ? (
                                                <tr>
                                                    <td colSpan={isReadOnly ? 5 : 6} className="px-3 py-4 text-center text-gray-500">
                                                        Nenhum item adicionado
                                                    </td>
                                                </tr>
                                            ) : (
                                                cartItems.map((item, index) => (
                                                    // Usando index como fallback para key se produto_id for nulo (produto avulso via api)
                                                    <tr key={item.produto_id || `item-${index}`}>
                                                        <td className="px-3 py-2 font-medium text-gray-800">{item.descricao}</td>
                                                        <td className="px-3 py-2">
                                                            {isReadOnly ? item.quantidade : (
                                                                <input
                                                                    type="number"
                                                                    min={1}
                                                                    value={item.quantidade}
                                                                    onChange={(e) => updateItem(index, 'quantidade', e.target.value)}
                                                                    className="w-full rounded border px-2 py-1"
                                                                />
                                                            )}
                                                        </td>
                                                        <td className="px-3 py-2">
                                                            {isReadOnly ? moneyFormatter.format(item.preco_unitario) : (
                                                                <input
                                                                    type="number"
                                                                    min={0.01}
                                                                    step="0.01"
                                                                    value={item.preco_unitario}
                                                                    onChange={(e) => updateItem(index, 'preco_unitario', e.target.value)}
                                                                    className="w-full rounded border px-2 py-1"
                                                                />
                                                            )}
                                                        </td>
                                                        <td className="px-3 py-2">
                                                            {isReadOnly ? `${item.desconto}%` : (
                                                                <input
                                                                    type="number"
                                                                    min={0}
                                                                    max={100}
                                                                    step="0.01"
                                                                    value={item.desconto}
                                                                    onChange={(e) => updateItem(index, 'desconto', e.target.value)}
                                                                    className="w-full rounded border px-2 py-1"
                                                                />
                                                            )}
                                                        </td>
                                                        <td className="px-3 py-2 font-semibold text-gray-700">
                                                            {moneyFormatter.format(calcItemTotal(item))}
                                                        </td>
                                                        {!isReadOnly && (
                                                            <td className="px-3 py-2 text-right">
                                                                <button
                                                                    type="button"
                                                                    onClick={() => removeItem(index)}
                                                                    className="text-red-500 hover:text-red-700"
                                                                >
                                                                    ✕
                                                                </button>
                                                            </td>
                                                        )}
                                                    </tr>
                                                ))
                                            )}
                                        </tbody>
                                    </table>
                                </div>

                                <div className="mt-4 flex flex-col items-end space-y-2 border-t pt-4">
                                    <div className="flex w-full items-center justify-between sm:w-1/2 md:w-1/3">
                                        <span className="text-sm text-gray-600">Subtotal:</span>
                                        <span className="font-medium">{moneyFormatter.format(subtotal)}</span>
                                    </div>
                                    <div className="flex w-full items-center justify-between sm:w-1/2 md:w-1/3">
                                        <span className="text-sm text-gray-600">Desconto Extra (R$):</span>
                                        {isReadOnly ? (
                                            <span className="font-medium text-red-600">- {moneyFormatter.format(descontoGeralNumber)}</span>
                                        ) : (
                                            <input
                                                type="number"
                                                min="0"
                                                step="0.01"
                                                value={descontoGeral}
                                                onChange={(e) => setDescontoGeral(e.target.value)}
                                                className="w-24 rounded border px-2 py-1 text-right text-sm"
                                            />
                                        )}
                                    </div>
                                    <div className="flex w-full items-center justify-between rounded-lg bg-gray-50 p-2 sm:w-1/2 md:w-1/3">
                                        <span className="font-semibold text-gray-800">Total:</span>
                                        <span className="text-lg font-bold text-blue-600">{moneyFormatter.format(totalOrcamento)}</span>
                                    </div>
                                </div>

                            </div>
                        </div>

                        {submitError && (
                            <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                                {submitError}
                            </div>
                        )}
                    </form>
                </div>

                <div className="border-t bg-gray-50 px-6 py-4 flex items-center justify-end gap-3 rounded-b-xl">
                    <button
                        type="button"
                        onClick={onClose}
                        className="rounded-lg border bg-white px-4 py-2 font-medium text-gray-700 hover:bg-gray-50"
                    >
                        {isReadOnly ? 'Fechar' : 'Cancelar'}
                    </button>
                    {!isReadOnly && (
                        <button
                            type="submit"
                            form="orcamento-form"
                            disabled={saveMutation.isPending}
                            className="rounded-lg bg-blue-600 px-6 py-2 font-medium text-white shadow hover:bg-blue-700 disabled:opacity-60"
                        >
                            {saveMutation.isPending ? 'Salvando...' : (isEditing ? 'Salvar Alterações' : 'Criar Orçamento')}
                        </button>
                    )}
                </div>
            </div>
        </div>
    )
}
