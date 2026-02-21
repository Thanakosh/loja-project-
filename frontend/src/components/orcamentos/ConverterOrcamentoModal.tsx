import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import api from '../../services/api'

interface Orcamento {
    id: number
    total: number
}

interface ConverterOrcamentoModalProps {
    isOpen: boolean
    onClose: () => void
    orcamento: Orcamento | null
}

const paymentOptions = [
    { value: 1, label: 'Dinheiro' },
    { value: 2, label: 'Cartão Débito' },
    { value: 3, label: 'Cartão Crédito' },
    { value: 4, label: 'PIX' },
    { value: 5, label: 'Boleto' },
    { value: 6, label: 'A Prazo' }
]

const moneyFormatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })

export default function ConverterOrcamentoModal({ isOpen, onClose, orcamento }: ConverterOrcamentoModalProps) {
    const queryClient = useQueryClient()
    const [formaPagamento, setFormaPagamento] = useState(1)
    const [parcelas, setParcelas] = useState(1)
    const [submitError, setSubmitError] = useState('')

    const convertMutation = useMutation({
        mutationFn: async (payload: { forma_pagamento: number; parcelas: number }) => {
            const response = await api.post(`/orcamento/${orcamento?.id}/converter`, payload)
            return response.data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['orcamentos'] })
            queryClient.invalidateQueries({ queryKey: ['pdv-vendas'] }) // Atualizar histórico se existir no front
            onClose()
        },
        onError: (error) => {
            if (isAxiosError(error)) {
                const detail = error.response?.data?.detail
                setSubmitError(typeof detail === 'string' ? detail : 'Erro ao converter o orçamento.')
            } else {
                setSubmitError('Erro inesperado tentando converter o orçamento.')
            }
        }
    })

    if (!isOpen || !orcamento) return null

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        setSubmitError('')

        convertMutation.mutate({
            forma_pagamento: formaPagamento,
            parcelas: formaPagamento === 6 ? Math.max(1, parcelas) : 1
        })
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
            <div className="w-full max-w-md rounded-xl bg-white shadow-2xl overflow-hidden">
                <div className="bg-blue-600 px-6 py-4">
                    <h2 className="text-lg font-semibold text-white">Converter em Venda</h2>
                    <p className="text-blue-100 text-sm mt-1">Orçamento #{orcamento.id}</p>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div className="rounded-lg bg-blue-50 p-4 border border-blue-100">
                        <p className="text-sm text-blue-800">
                            Você está prestes a converter este orçamento na venda de total{' '}
                            <strong className="text-blue-900">{moneyFormatter.format(orcamento.total)}</strong>.<br />
                            <span className="text-xs">O estoque será baixado automaticamente.</span>
                        </p>
                    </div>

                    <div>
                        <label className="mb-1 block text-sm font-medium text-gray-700">Forma de Pagamento</label>
                        <select
                            value={formaPagamento}
                            onChange={(e) => setFormaPagamento(Number(e.target.value))}
                            className="w-full rounded-lg border px-3 py-2 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                        >
                            {paymentOptions.map((opt) => (
                                <option key={opt.value} value={opt.value}>{opt.label}</option>
                            ))}
                        </select>
                    </div>

                    {formaPagamento === 6 && (
                        <div>
                            <label className="mb-1 block text-sm font-medium text-gray-700">Parcelas</label>
                            <input
                                type="number"
                                min="1"
                                value={parcelas}
                                onChange={(e) => setParcelas(Math.max(1, Number(e.target.value) || 1))}
                                className="w-full rounded-lg border px-3 py-2 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                    )}

                    {submitError && (
                        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 border border-red-200">{submitError}</p>
                    )}

                    <div className="pt-2 flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-gray-700 font-medium hover:bg-gray-50 rounded-lg border"
                            disabled={convertMutation.isPending}
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={convertMutation.isPending}
                            className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg shadow hover:bg-blue-700 disabled:opacity-60"
                        >
                            {convertMutation.isPending ? 'Convertendo...' : 'Confirmar Venda'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
