import { useCallback, useEffect, useRef, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import toast from 'react-hot-toast'

import api from '../services/api'

/* ─────────────────────────────────────────────
   TYPES
───────────────────────────────────────────── */
interface ItemExtraido {
    key: string
    nome: string
    quantidade: number
    preco_unitario: number
    unidade: string
    codigo_ncm: string
    codigo_barras: string
    fornecedor: string
    selecionado: boolean
}

interface OCRTaskResponse { task_id: string; status: string; message: string }
interface OCRTaskStatus {
    task_id: string
    status: 'pending' | 'processing' | 'completed' | 'failed'
    result?: {
        texto: string
        nota_fiscal?: {
            fornecedor: string; nome_fantasia_fornecedor?: string; cnpj_fornecedor?: string
            numero_nota?: string; data_emissao?: string
            produtos: Array<{ nome: string; quantidade: number; preco_unitario: number; unidade?: string; codigo_ncm?: string; codigo_barras?: string }>
            valor_total: number; fornecedor_status?: 'novo' | 'existente' | null; fornecedor_id?: number | null
        }
        produtos?: string[]; quantidade?: number[]; valor?: number[]
    }
    error?: string
}

interface NCMCandidato { codigo: string; descricao: string; score: number }
interface SupplierRankingItem {
    fornecedor_id: number; razao_social: string; cnpj: string
    total_notas: number; total_itens: number; valor_total: number; score_confiabilidade: number
}

/* ─────────────────────────────────────────────
   HELPERS
───────────────────────────────────────────── */
const moneyFormatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
let keyCounter = 0
const nextKey = () => `item-${++keyCounter}`
const POLLING_INTERVAL = 2000
const ACCEPT_STRING = '.xml,text/xml,application/xml'
type FileKind = 'xml' | 'unknown'
function detectFileKind(file: File): FileKind {
    const name = file.name.toLowerCase()
    if (name.endsWith('.xml') || file.type.includes('xml')) return 'xml'
    return 'unknown'
}
const FILE_KIND_LABELS: Record<FileKind, { icon: string; label: string }> = {
    xml: { icon: '📋', label: 'XML de NFe' },
    unknown: { icon: '❓', label: 'Desconhecido' },
}

type Tab = 'importar' | 'ncm' | 'ranking'

/* ─────────────────────────────────────────────
   COMPONENT
───────────────────────────────────────────── */
const ImportarNota = () => {
    const [activeTab, setActiveTab] = useState<Tab>('importar')

    return (
        <div className="container mx-auto space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Notas Fiscais & Fiscal IA</h1>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    Importe XMLs, classifique NCM e consulte o ranking de fornecedores com inteligência artificial
                </p>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 rounded-xl bg-gray-100 dark:bg-gray-800 p-1 w-fit">
                {([
                    { id: 'importar', label: '📤 Importar XML' },
                    { id: 'ncm', label: '🔍 Classificar NCM' },
                    { id: 'ranking', label: '🏆 Ranking Fornecedores' },
                ] as { id: Tab; label: string }[]).map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${activeTab === tab.id
                            ? 'bg-white dark:bg-gray-700 text-blue-700 dark:text-blue-300 shadow'
                            : 'text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
                            }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Tab content */}
            {activeTab === 'importar' && <TabImportar />}
            {activeTab === 'ncm' && <TabNCM />}
            {activeTab === 'ranking' && <TabRanking />}
        </div>
    )
}

/* ─────────────────────────────────────────────
   TAB: CLASSIFICAR NCM
───────────────────────────────────────────── */
const TabNCM = () => {
    const [descricao, setDescricao] = useState('')
    const [limite, setLimite] = useState(5)
    const [feedbackEnviado, setFeedbackEnviado] = useState<Record<string, string>>({})

    const { mutate, isPending, data, reset } = useMutation({
        mutationFn: async () => {
            const res = await api.post('/fiscal-ai/classify-ncm', { descricao: descricao.trim(), limite })
            return res.data as { descricao_consultada: string; candidatos: NCMCandidato[]; total_encontrado: number }
        },
        onError: (err: unknown) => {
            toast.error(isAxiosError<{ detail?: string }>(err) ? err.response?.data?.detail ?? 'Erro ao classificar NCM.' : 'Erro ao classificar NCM.')
        },
    })

    const enviarFeedback = async (codigo: string, decisao: 'aceito' | 'rejeitado') => {
        try {
            await api.post('/fiscal-ai/feedback', {
                origem_sugestao: 'classify_ncm',
                versao_motor: '1.0.0',
                decisao,
                referencia_id: codigo,
                observacao: descricao.trim(),
            })
            setFeedbackEnviado(prev => ({ ...prev, [codigo]: decisao }))
            toast.success(decisao === 'aceito' ? '✅ Feedback registrado!' : '❌ Feedback registrado.')
        } catch {
            toast.error('Erro ao registrar feedback.')
        }
    }

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (!descricao.trim()) { toast.error('Digite uma descrição.'); return }
        setFeedbackEnviado({})
        mutate()
    }

    return (
        <div className="space-y-6">
            {/* Form */}
            <div className="rounded-lg bg-white dark:bg-gray-800 p-5 shadow">
                <h2 className="text-base font-semibold text-gray-800 dark:text-gray-100 mb-4">
                    🔍 Classificar código NCM por descrição
                </h2>
                <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
                    <input
                        type="text"
                        value={descricao}
                        onChange={e => { setDescricao(e.target.value); reset() }}
                        placeholder="Ex: fio de cobre 2,5mm, arroz branco polido, parafuso sextavado..."
                        className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2.5 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <select
                        value={limite}
                        onChange={e => setLimite(Number(e.target.value))}
                        className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2.5 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        {[3, 5, 10].map(n => <option key={n} value={n}>{n} resultados</option>)}
                    </select>
                    <button
                        type="submit"
                        disabled={isPending}
                        className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 whitespace-nowrap"
                    >
                        {isPending
                            ? <><span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" /> Buscando...</>
                            : '🔍 Buscar NCM'
                        }
                    </button>
                </form>
                <p className="mt-2 text-xs text-gray-400 dark:text-gray-500">
                    A IA busca os códigos NCM mais relevantes com base nas palavras-chave da descrição.
                </p>
            </div>

            {/* Results */}
            {data && (
                <div className="rounded-lg bg-white dark:bg-gray-800 shadow overflow-hidden">
                    <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-5 py-3">
                        <div>
                            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100">Resultados</h3>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                {data.total_encontrado} código(s) encontrado(s) para "{data.descricao_consultada}"
                            </p>
                        </div>
                    </div>

                    {data.candidatos.length === 0 ? (
                        <div className="p-8 text-center text-sm text-gray-500 dark:text-gray-400">
                            Nenhum código NCM encontrado para esta descrição. Tente termos mais gerais.
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-100 dark:divide-gray-700">
                            {data.candidatos.map((c, i) => {
                                const fb = feedbackEnviado[c.codigo]
                                const scorePct = Math.round(c.score * 100)
                                return (
                                    <div key={c.codigo} className="flex items-center gap-4 px-5 py-3.5 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                                        {/* Rank badge */}
                                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-bold flex items-center justify-center">
                                            {i + 1}
                                        </span>

                                        {/* NCM code */}
                                        <div className="flex-shrink-0">
                                            <span className="font-mono text-sm font-semibold text-gray-800 dark:text-gray-100 bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">
                                                {c.codigo}
                                            </span>
                                        </div>

                                        {/* Description */}
                                        <p className="flex-1 text-sm text-gray-700 dark:text-gray-300 min-w-0">{c.descricao}</p>

                                        {/* Score bar */}
                                        <div className="flex-shrink-0 flex items-center gap-2">
                                            <div className="w-20 h-1.5 rounded-full bg-gray-200 dark:bg-gray-600">
                                                <div
                                                    className="h-1.5 rounded-full bg-blue-500"
                                                    style={{ width: `${scorePct}%` }}
                                                />
                                            </div>
                                            <span className="text-xs text-gray-500 dark:text-gray-400 w-8 text-right">{scorePct}%</span>
                                        </div>

                                        {/* Feedback buttons */}
                                        <div className="flex-shrink-0 flex gap-1">
                                            {fb ? (
                                                <span className={`text-xs px-2 py-1 rounded-full font-medium ${fb === 'aceito'
                                                    ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300'
                                                    : 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300'
                                                    }`}>
                                                    {fb === 'aceito' ? '✅ Aceito' : '❌ Rejeitado'}
                                                </span>
                                            ) : (
                                                <>
                                                    <button
                                                        onClick={() => enviarFeedback(c.codigo, 'aceito')}
                                                        title="Este NCM é correto"
                                                        className="rounded p-1.5 text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-900/30 transition-colors"
                                                    >
                                                        👍
                                                    </button>
                                                    <button
                                                        onClick={() => enviarFeedback(c.codigo, 'rejeitado')}
                                                        title="Este NCM não é adequado"
                                                        className="rounded p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors"
                                                    >
                                                        👎
                                                    </button>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    )}
                </div>
            )}

            {/* Empty state before first search */}
            {!data && !isPending && (
                <div className="rounded-lg border-2 border-dashed border-gray-200 dark:border-gray-700 p-12 text-center">
                    <div className="text-4xl mb-3">🔍</div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                        Digite a descrição de um produto e clique em Buscar NCM para ver as sugestões.
                    </p>
                </div>
            )}
        </div>
    )
}

/* ─────────────────────────────────────────────
   TAB: RANKING DE FORNECEDORES
───────────────────────────────────────────── */
const TabRanking = () => {
    const [criterio, setCriterio] = useState<'valor_total' | 'total_notas' | 'total_itens'>('valor_total')
    const [limite, setLimite] = useState(10)

    const { data, isLoading, isError, refetch } = useQuery({
        queryKey: ['supplier-ranking', criterio, limite],
        queryFn: async () => {
            const res = await api.get(`/fiscal-ai/supplier-ranking?criterio=${criterio}&limite=${limite}`)
            return res.data as { fornecedores: SupplierRankingItem[]; total: number; criterio: string }
        },
    })

    const criterioLabels = {
        valor_total: { label: 'Valor Total', icon: '💰' },
        total_notas: { label: 'Nº de Notas', icon: '🧾' },
        total_itens: { label: 'Nº de Itens', icon: '📦' },
    }

    return (
        <div className="space-y-5">
            {/* Controls */}
            <div className="rounded-lg bg-white dark:bg-gray-800 p-5 shadow flex flex-wrap gap-3 items-end">
                <div>
                    <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Ordenar por</label>
                    <div className="flex gap-2">
                        {(Object.entries(criterioLabels) as [typeof criterio, { label: string; icon: string }][]).map(([key, { label, icon }]) => (
                            <button
                                key={key}
                                onClick={() => setCriterio(key)}
                                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${criterio === key
                                    ? 'bg-blue-600 text-white shadow'
                                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                                    }`}
                            >
                                {icon} {label}
                            </button>
                        ))}
                    </div>
                </div>
                <div>
                    <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Exibir</label>
                    <select
                        value={limite}
                        onChange={e => setLimite(Number(e.target.value))}
                        className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        {[5, 10, 20].map(n => <option key={n} value={n}>Top {n}</option>)}
                    </select>
                </div>
                <button
                    onClick={() => refetch()}
                    className="ml-auto rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                >
                    🔄 Atualizar
                </button>
            </div>

            {/* Table */}
            <div className="rounded-lg bg-white dark:bg-gray-800 shadow overflow-hidden">
                <div className="border-b border-gray-200 dark:border-gray-700 px-5 py-3 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
                        🏆 Ranking de Fornecedores — por {criterioLabels[criterio].label}
                    </h3>
                    {data && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                            {data.total} fornecedor(es) com dados
                        </span>
                    )}
                </div>

                {isLoading && (
                    <div className="flex items-center justify-center py-12 gap-2 text-sm text-gray-500 dark:text-gray-400">
                        <span className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
                        Carregando ranking...
                    </div>
                )}

                {isError && (
                    <div className="p-8 text-center text-sm text-red-600 dark:text-red-400">
                        Erro ao carregar ranking. Verifique se o servidor está rodando.
                    </div>
                )}

                {data && data.fornecedores.length === 0 && (
                    <div className="p-8 text-center text-sm text-gray-500 dark:text-gray-400">
                        Nenhum fornecedor com dados encontrado. Importe notas fiscais primeiro.
                    </div>
                )}

                {data && data.fornecedores.length > 0 && (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                            <thead className="bg-gray-50 dark:bg-gray-700">
                                <tr>
                                    {['#', 'Fornecedor', 'CNPJ', 'Notas', 'Itens', 'Valor Total', 'Score'].map(h => (
                                        <th key={h} className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">
                                            {h}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                {data.fornecedores.map((f, i) => {
                                    const scorePct = Math.round(f.score_confiabilidade * 100)
                                    const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : null
                                    return (
                                        <tr key={f.fornecedor_id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                                            <td className="px-4 py-3 text-sm font-medium text-gray-500 dark:text-gray-400">
                                                {medal ? <span>{medal}</span> : <span className="text-gray-400">#{i + 1}</span>}
                                            </td>
                                            <td className="px-4 py-3">
                                                <p className="text-sm font-medium text-gray-800 dark:text-gray-100 truncate max-w-[200px]">
                                                    {f.razao_social}
                                                </p>
                                            </td>
                                            <td className="px-4 py-3 text-xs font-mono text-gray-500 dark:text-gray-400 whitespace-nowrap">
                                                {f.cnpj}
                                            </td>
                                            <td className="px-4 py-3 text-sm text-center text-gray-700 dark:text-gray-300">
                                                {f.total_notas}
                                            </td>
                                            <td className="px-4 py-3 text-sm text-center text-gray-700 dark:text-gray-300">
                                                {f.total_itens}
                                            </td>
                                            <td className="px-4 py-3 text-sm font-medium text-emerald-700 dark:text-emerald-400 whitespace-nowrap">
                                                {moneyFormatter.format(f.valor_total)}
                                            </td>
                                            <td className="px-4 py-3">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-16 h-1.5 rounded-full bg-gray-200 dark:bg-gray-600">
                                                        <div
                                                            className={`h-1.5 rounded-full ${scorePct >= 75 ? 'bg-emerald-500' :
                                                                scorePct >= 40 ? 'bg-yellow-500' : 'bg-red-400'
                                                                }`}
                                                            style={{ width: `${scorePct}%` }}
                                                        />
                                                    </div>
                                                    <span className="text-xs text-gray-500 dark:text-gray-400 w-7">{scorePct}%</span>
                                                </div>
                                            </td>
                                        </tr>
                                    )
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    )
}

/* ─────────────────────────────────────────────
   TAB: IMPORTAR XML (código original preservado)
───────────────────────────────────────────── */
const TabImportar = () => {
    const [file, setFile] = useState<File | null>(null)
    const [fileKind, setFileKind] = useState<FileKind>('unknown')
    const [dragOver, setDragOver] = useState(false)
    const fileInputRef = useRef<HTMLInputElement>(null)
    const [taskId, setTaskId] = useState<string | null>(null)
    const [taskStatus, setTaskStatus] = useState<OCRTaskStatus['status'] | null>(null)
    const [errorMsg, setErrorMsg] = useState<string | null>(null)
    const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
    const [itens, setItens] = useState<ItemExtraido[]>([])
    const [fornecedorGlobal, setFornecedorGlobal] = useState('')
    const [nomeFantasiaFornecedor, setNomeFantasiaFornecedor] = useState('')
    const [cnpjFornecedor, setCnpjFornecedor] = useState('')
    const [numeroNota, setNumeroNota] = useState('')
    const [dataEmissaoNota, setDataEmissaoNota] = useState('')
    const [valorTotalNota, setValorTotalNota] = useState<number>(0)
    const [fornecedorStatus, setFornecedorStatus] = useState<'novo' | 'existente' | null>(null)
    type Step = 'upload' | 'processing' | 'review' | 'done'
    const [step, setStep] = useState<Step>('upload')

    const handleFileSelect = useCallback((selectedFile: File) => {
        const kind = detectFileKind(selectedFile)
        if (kind === 'unknown') { toast.error('Arquivo não suportado. Envie o XML da NFe.'); return }
        setFile(selectedFile); setFileKind(kind); setErrorMsg(null)
    }, [])

    const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault(); setDragOver(false)
        const dropped = e.dataTransfer.files[0]
        if (dropped) handleFileSelect(dropped)
    }, [handleFileSelect])

    const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const selected = e.target.files?.[0]
        if (selected) handleFileSelect(selected)
    }, [handleFileSelect])

    const handleTaskCompleted = useCallback((data: OCRTaskStatus) => {
        if (!data.result) return
        if (data.result.nota_fiscal) {
            const nf = data.result.nota_fiscal
            setFornecedorGlobal(nf.fornecedor || ''); setNomeFantasiaFornecedor(nf.nome_fantasia_fornecedor || '')
            setCnpjFornecedor(nf.cnpj_fornecedor || ''); setNumeroNota(nf.numero_nota || '')
            setDataEmissaoNota(nf.data_emissao || ''); setValorTotalNota(nf.valor_total || 0)
            setFornecedorStatus(nf.fornecedor_status || null)
            const mapped: ItemExtraido[] = (nf.produtos || []).map((p) => ({
                key: nextKey(), nome: p.nome, quantidade: p.quantidade, preco_unitario: p.preco_unitario,
                unidade: p.unidade || 'UN', codigo_ncm: p.codigo_ncm || '', codigo_barras: p.codigo_barras || '',
                fornecedor: nf.fornecedor || '', selecionado: true,
            }))
            setItens(mapped)
        } else {
            const produtos = data.result.produtos || []; const quantidades = data.result.quantidade || []; const valores = data.result.valor || []
            const mapped: ItemExtraido[] = produtos.map((nome, i) => ({
                key: nextKey(), nome, quantidade: quantidades[i] || 1, preco_unitario: valores[i] || 0,
                unidade: 'UN', codigo_ncm: '', codigo_barras: '', fornecedor: '', selecionado: true,
            }))
            setItens(mapped)
        }
        setStep('review')
    }, [])

    const uploadMutation = useMutation({
        mutationFn: async (fileToUpload: File) => {
            const formData = new FormData(); formData.append('file', fileToUpload)
            const res = await api.post('/ocr/upload-arquivo', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
            return res.data as OCRTaskResponse
        },
        onSuccess: (data) => {
            setTaskId(data.task_id); setTaskStatus('completed')
            api.get(`/ocr/status/${data.task_id}`).then((res) => {
                handleTaskCompleted(res.data as OCRTaskStatus)
                toast.success(data.message || 'XML processado com sucesso!')
            })
        },
        onError: (err: unknown) => {
            const detail = isAxiosError<{ message?: string; detail?: string }>(err)
                ? err.response?.data?.message ?? err.response?.data?.detail ?? 'Erro ao enviar arquivo.'
                : 'Erro ao enviar arquivo.'
            toast.error(detail); setErrorMsg(detail)
        },
    })

    const handleUpload = () => {
        if (!file) { toast.error('Selecione um arquivo primeiro.'); return }
        uploadMutation.mutate(file)
    }

    const pollingStartRef = useRef<number | null>(null)
    const POLLING_TIMEOUT_MS = 3 * 60 * 1000

    useEffect(() => {
        if (!taskId || taskStatus === 'completed' || taskStatus === 'failed') {
            if (pollingRef.current) clearInterval(pollingRef.current)
            pollingStartRef.current = null; return
        }
        if (!pollingStartRef.current) pollingStartRef.current = Date.now()
        const poll = async () => {
            if (pollingStartRef.current && Date.now() - pollingStartRef.current > POLLING_TIMEOUT_MS) {
                if (pollingRef.current) clearInterval(pollingRef.current)
                setErrorMsg('Tempo limite excedido. Tente novamente.'); toast.error('Tempo limite excedido.'); setStep('upload'); pollingStartRef.current = null; return
            }
            try {
                const res = await api.get(`/ocr/status/${taskId}`); const data = res.data as OCRTaskStatus
                setTaskStatus(data.status)
                if (data.status === 'completed' && data.result) { handleTaskCompleted(data); toast.success('Processamento concluído!') }
                if (data.status === 'failed') { setErrorMsg(data.error || 'Falha.'); toast.error(data.error || 'Falha.'); setStep('upload') }
            } catch (err: unknown) {
                if (isAxiosError(err) && err.response?.status === 404) {
                    if (pollingRef.current) clearInterval(pollingRef.current)
                    setErrorMsg('Tarefa não encontrada. Reenvie o arquivo.'); toast.error('Tarefa perdida.'); setStep('upload')
                }
            }
        }
        pollingRef.current = setInterval(poll, POLLING_INTERVAL); poll()
        return () => { if (pollingRef.current) clearInterval(pollingRef.current) }
    }, [taskId, taskStatus, handleTaskCompleted, POLLING_TIMEOUT_MS])

    const updateItem = (key: string, field: keyof ItemExtraido, value: string | number | boolean) => {
        setItens(prev => prev.map(item => (item.key === key ? { ...item, [field]: value } : item)))
    }
    const removeItem = (key: string) => setItens(prev => prev.filter(item => item.key !== key))
    const addItem = () => setItens(prev => [...prev, { key: nextKey(), nome: '', quantidade: 1, preco_unitario: 0, unidade: 'UN', codigo_ncm: '', codigo_barras: '', fornecedor: fornecedorGlobal, selecionado: true }])
    const toggleSelectAll = (checked: boolean) => setItens(prev => prev.map(item => ({ ...item, selecionado: checked })))
    const selectedItems = itens.filter(i => i.selecionado)
    const allSelected = itens.length > 0 && itens.every(i => i.selecionado)

    const importMutation = useMutation({
        mutationFn: async (items: ItemExtraido[]) => {
            const produtos = items.map(item => ({
                nome: item.nome, fornecedor: item.fornecedor || fornecedorGlobal || 'Não informado',
                preco_unitario: item.preco_unitario, preco_liquido: item.preco_unitario,
                codigo_ncm: item.codigo_ncm || undefined, codigo_barras: item.codigo_barras || undefined,
                unidade: item.unidade || 'UN', numero_nota: numeroNota || undefined,
                cnpj_fornecedor: cnpjFornecedor || undefined, quantidade_inicial: item.quantidade,
            }))
            const results = []; const erros: string[] = []
            for (const prod of produtos) {
                try { const res = await api.post('/produtos/', prod); results.push(res.data) }
                catch (err: unknown) { erros.push(isAxiosError<{ message?: string; detail?: string }>(err) ? err.response?.data?.message ?? err.response?.data?.detail ?? `Erro ao cadastrar "${prod.nome}"` : `Erro ao cadastrar "${prod.nome}"`) }
            }
            return { results, erros }
        },
        onSuccess: ({ results, erros }) => {
            if (results.length > 0) toast.success(`${results.length} produto(s) importado(s)!`)
            erros.forEach(e => toast.error(e))
            if (results.length > 0) setStep('done')
        },
        onError: (err: unknown) => toast.error(isAxiosError<{ detail?: string }>(err) ? err.response?.data?.detail ?? 'Erro ao importar.' : 'Erro ao importar.'),
    })

    const handleImport = () => {
        if (selectedItems.length === 0) { toast.error('Selecione pelo menos um item.'); return }
        if (selectedItems.some(i => !i.nome.trim())) { toast.error('Todos os itens devem ter um nome.'); return }
        importMutation.mutate(selectedItems)
    }

    const handleReset = () => {
        setFile(null); setFileKind('unknown'); setTaskId(null); setTaskStatus(null)
        setErrorMsg(null); setItens([]); setFornecedorGlobal(''); setNomeFantasiaFornecedor('')
        setCnpjFornecedor(''); setNumeroNota(''); setDataEmissaoNota(''); setValorTotalNota(0)
        setFornecedorStatus(null); setStep('upload')
        if (fileInputRef.current) fileInputRef.current.value = ''
    }

    const steps = [
        { id: 'upload', label: '1. Upload', icon: '📤' },
        { id: 'processing', label: '2. Processando', icon: '⚙️' },
        { id: 'review', label: '3. Revisão', icon: '✏️' },
        { id: 'done', label: '4. Concluído', icon: '✅' },
    ]
    const stepIndex = steps.findIndex(s => s.id === step)

    return (
        <div className="space-y-6">
            {/* Header row */}
            <div className="flex justify-end">
                {step !== 'upload' && (
                    <button type="button" onClick={handleReset}
                        className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-sm text-gray-700 dark:text-gray-200 transition hover:bg-gray-50 dark:hover:bg-gray-700">
                        Nova Importação
                    </button>
                )}
            </div>

            {/* Steps */}
            <div className="rounded-lg bg-white p-4 shadow dark:bg-gray-800">
                <div className="flex items-center justify-between">
                    {steps.map((s, i) => (
                        <div key={s.id} className="flex items-center flex-1">
                            <div className="flex flex-col items-center flex-1">
                                <div className={`flex h-10 w-10 items-center justify-center rounded-full text-lg transition-all duration-300 ${i <= stepIndex ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30' : 'bg-gray-200 dark:bg-gray-700 text-gray-500'}`}>
                                    {s.icon}
                                </div>
                                <span className={`mt-2 text-xs font-medium ${i <= stepIndex ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400'}`}>{s.label}</span>
                            </div>
                            {i < steps.length - 1 && <div className={`h-0.5 w-full transition-all duration-500 ${i < stepIndex ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'}`} />}
                        </div>
                    ))}
                </div>
            </div>

            {/* STEP 1: Upload */}
            {step === 'upload' && (
                <div className="space-y-4">
                    <div
                        className={`relative cursor-pointer rounded-xl border-2 border-dashed p-12 text-center transition-all duration-300 ${dragOver ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:border-blue-400'}`}
                        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                        onDragLeave={() => setDragOver(false)}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <input ref={fileInputRef} type="file" accept={ACCEPT_STRING} className="hidden" onChange={handleFileInput} />
                        {file ? (
                            <div className="space-y-4">
                                <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-gray-100 dark:bg-gray-700 text-4xl">
                                    {FILE_KIND_LABELS[fileKind].icon}
                                </div>
                                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 dark:bg-emerald-900/40 px-3 py-1 text-xs font-medium text-emerald-700 dark:text-emerald-300">
                                    {FILE_KIND_LABELS[fileKind].label}
                                </span>
                                <p className="text-sm font-medium text-gray-700 dark:text-gray-200">{file.name}</p>
                                <p className="text-xs text-gray-400">Clique ou arraste outro arquivo para substituir</p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/40 text-3xl">📤</div>
                                <p className="text-lg font-medium text-gray-700 dark:text-gray-200">Arraste o XML da NFe aqui</p>
                                <p className="text-sm text-gray-500">ou clique para selecionar</p>
                                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 dark:bg-emerald-900/40 px-3 py-1 text-xs font-medium text-emerald-700 dark:text-emerald-300">📋 XML de NFe</span>
                            </div>
                        )}
                    </div>
                    {errorMsg && <div className="rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 p-4 text-sm text-red-700 dark:text-red-300">{errorMsg}</div>}
                    {file && (
                        <div className="flex justify-end gap-3">
                            <button type="button" onClick={handleReset} className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-200 transition hover:bg-gray-50">Limpar</button>
                            <button type="button" onClick={handleUpload} disabled={uploadMutation.isPending}
                                className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white shadow transition hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2">
                                {uploadMutation.isPending ? <><span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" /> Enviando...</> : <>📋 Processar XML</>}
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* STEP 3: Review */}
            {step === 'review' && (
                <div className="space-y-4">
                    <div className="rounded-lg bg-white p-5 shadow dark:bg-gray-800">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Dados da Nota Fiscal</h2>
                            {fornecedorStatus === 'novo' && <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 dark:bg-emerald-900/40 px-3 py-1 text-xs font-medium text-emerald-700 dark:text-emerald-300">✅ Fornecedor novo cadastrado</span>}
                            {fornecedorStatus === 'existente' && <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-100 dark:bg-blue-900/40 px-3 py-1 text-xs font-medium text-blue-700 dark:text-blue-300">🔍 Fornecedor já cadastrado</span>}
                        </div>
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                            {[
                                { label: 'Fornecedor', val: fornecedorGlobal, set: setFornecedorGlobal, ph: 'Nome do fornecedor' },
                                { label: 'Nome Fantasia', val: nomeFantasiaFornecedor, set: setNomeFantasiaFornecedor, ph: 'Nome fantasia' },
                                { label: 'CNPJ', val: cnpjFornecedor, set: setCnpjFornecedor, ph: '00.000.000/0000-00' },
                                { label: 'Nº Nota', val: numeroNota, set: setNumeroNota, ph: 'Número da nota' },
                                { label: 'Data Emissão', val: dataEmissaoNota, set: setDataEmissaoNota, ph: 'YYYY-MM-DD' },
                            ].map(f => (
                                <div key={f.label}>
                                    <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">{f.label}</label>
                                    <input type="text" value={f.val} onChange={e => f.set(e.target.value)} placeholder={f.ph}
                                        className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                                </div>
                            ))}
                            <div>
                                <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Valor Total</label>
                                <input type="text" value={moneyFormatter.format(valorTotalNota || 0)} readOnly
                                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/70 px-3 py-2 text-sm font-medium text-gray-800 dark:text-gray-100" />
                            </div>
                        </div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-3">
                        <div className="rounded-lg bg-white p-4 shadow dark:bg-gray-800"><p className="text-xs text-gray-500">Itens encontrados</p><p className="text-2xl font-semibold text-gray-800 dark:text-gray-100">{itens.length}</p></div>
                        <div className="rounded-lg bg-white p-4 shadow dark:bg-gray-800"><p className="text-xs text-gray-500">Selecionados</p><p className="text-2xl font-semibold text-blue-600 dark:text-blue-400">{selectedItems.length}</p></div>
                        <div className="rounded-lg bg-white p-4 shadow dark:bg-gray-800"><p className="text-xs text-gray-500">Valor estimado</p><p className="text-2xl font-semibold text-emerald-600 dark:text-emerald-400">{moneyFormatter.format(selectedItems.reduce((s, i) => s + i.preco_unitario * i.quantidade, 0))}</p></div>
                    </div>

                    <div className="overflow-hidden rounded-lg bg-white shadow dark:bg-gray-800">
                        <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-5 py-3">
                            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100">Itens para Importação</h3>
                            <button type="button" onClick={addItem} className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-emerald-700">+ Adicionar Item</button>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                                <thead className="bg-gray-50 dark:bg-gray-700">
                                    <tr>
                                        <th className="px-3 py-3"><input type="checkbox" checked={allSelected} onChange={e => toggleSelectAll(e.target.checked)} className="h-4 w-4 rounded border-gray-300 text-blue-600" /></th>
                                        {['Produto', 'Qtd', 'Unidade', 'Preço Unit.', 'NCM', 'Subtotal', ''].map(h => <th key={h} className="px-3 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">{h}</th>)}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                    {itens.length === 0 ? (
                                        <tr><td colSpan={8} className="px-4 py-8 text-center text-sm text-gray-500">Nenhum item encontrado.</td></tr>
                                    ) : itens.map(item => (
                                        <tr key={item.key} className={`transition-colors ${item.selecionado ? 'bg-white dark:bg-gray-800' : 'bg-gray-50 dark:bg-gray-900 opacity-60'}`}>
                                            <td className="px-3 py-2"><input type="checkbox" checked={item.selecionado} onChange={e => updateItem(item.key, 'selecionado', e.target.checked)} className="h-4 w-4 rounded border-gray-300 text-blue-600" /></td>
                                            <td className="px-3 py-2"><input type="text" value={item.nome} onChange={e => updateItem(item.key, 'nome', e.target.value)} className="w-full min-w-[200px] rounded border border-gray-300 dark:border-gray-600 bg-transparent px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-800 dark:text-gray-100" placeholder="Nome do produto" /></td>
                                            <td className="px-3 py-2"><input type="number" min={1} value={item.quantidade} onChange={e => updateItem(item.key, 'quantidade', parseInt(e.target.value) || 1)} className="w-20 rounded border border-gray-300 dark:border-gray-600 bg-transparent px-2 py-1.5 text-sm text-center focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-800 dark:text-gray-100" /></td>
                                            <td className="px-3 py-2">
                                                <select value={item.unidade} onChange={e => updateItem(item.key, 'unidade', e.target.value)} className="rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1.5 text-sm text-gray-800 dark:text-gray-100 focus:outline-none">
                                                    {['UN', 'CX', 'M', 'KG', 'PC', 'RL'].map(u => <option key={u} value={u}>{u}</option>)}
                                                </select>
                                            </td>
                                            <td className="px-3 py-2"><input type="number" min={0} step={0.01} value={item.preco_unitario} onChange={e => updateItem(item.key, 'preco_unitario', parseFloat(e.target.value) || 0)} className="w-28 rounded border border-gray-300 dark:border-gray-600 bg-transparent px-2 py-1.5 text-sm text-right focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-800 dark:text-gray-100" /></td>
                                            <td className="px-3 py-2"><input type="text" value={item.codigo_ncm} onChange={e => updateItem(item.key, 'codigo_ncm', e.target.value)} className="w-28 rounded border border-gray-300 dark:border-gray-600 bg-transparent px-2 py-1.5 text-sm text-center focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-800 dark:text-gray-100" placeholder="00000000" /></td>
                                            <td className="px-3 py-2 text-right text-sm font-medium text-gray-800 dark:text-gray-100 whitespace-nowrap">{moneyFormatter.format(item.preco_unitario * item.quantidade)}</td>
                                            <td className="px-3 py-2"><button type="button" onClick={() => removeItem(item.key)} aria-label={`Remover item ${item.descricao}`} className="rounded p-1 text-red-500 transition hover:bg-red-50 dark:hover:bg-red-900/30">✕</button></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div className="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 p-4">
                        <div className="flex items-start gap-3">
                            <span className="text-xl">⚠️</span>
                            <p className="text-sm text-amber-800 dark:text-amber-200">Revise nomes, quantidades, preços e NCM antes de importar. Itens desmarcados não serão importados.</p>
                        </div>
                    </div>

                    <div className="flex items-center justify-between">
                        <button type="button" onClick={handleReset} className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-200 transition hover:bg-gray-50">Cancelar</button>
                        <button type="button" onClick={handleImport} disabled={importMutation.isPending || selectedItems.length === 0}
                            className="rounded-lg bg-emerald-600 px-8 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-500/30 transition hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-2">
                            {importMutation.isPending ? <><span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />Importando...</> : <>✅ Importar {selectedItems.length} {selectedItems.length === 1 ? 'Produto' : 'Produtos'}</>}
                        </button>
                    </div>
                </div>
            )}

            {/* STEP 4: Done */}
            {step === 'done' && (
                <div className="flex flex-col items-center justify-center space-y-6 rounded-lg bg-white p-12 shadow dark:bg-gray-800">
                    <div className="flex h-20 w-20 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/40 text-4xl">✅</div>
                    <div className="text-center">
                        <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Importação Concluída!</h2>
                        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">Todos os produtos foram cadastrados com sucesso.</p>
                    </div>
                    <div className="flex gap-3">
                        <button type="button" onClick={handleReset} className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700">📤 Importar Outra Nota</button>
                        <a href="/produtos" className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-6 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-200 transition hover:bg-gray-50">📦 Ver Produtos</a>
                    </div>
                </div>
            )}
        </div>
    )
}

export default ImportarNota
