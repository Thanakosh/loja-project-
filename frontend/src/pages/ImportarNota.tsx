import { useCallback, useEffect, useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import api from '../services/api'

/* ─── Types ─── */
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

interface OCRTaskResponse {
    task_id: string
    status: string
    message: string
}

interface OCRTaskStatus {
    task_id: string
    status: 'pending' | 'processing' | 'completed' | 'failed'
    result?: {
        texto: string
        nota_fiscal?: {
            fornecedor: string
            nome_fantasia_fornecedor?: string
            cnpj_fornecedor?: string
            numero_nota?: string
            data_emissao?: string
            produtos: Array<{
                nome: string
                quantidade: number
                preco_unitario: number
                unidade?: string
                codigo_ncm?: string
                codigo_barras?: string
            }>
            valor_total: number
            fornecedor_status?: 'novo' | 'existente' | null
            fornecedor_id?: number | null
        }
        produtos?: string[]
        quantidade?: number[]
        valor?: number[]
    }
    error?: string
}

/* ─── Helpers ─── */
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

const FILE_KIND_LABELS: Record<FileKind, { icon: string; label: string; color: string }> = {
    xml: { icon: '📋', label: 'XML de NFe', color: 'text-emerald-600 dark:text-emerald-400' },
    unknown: { icon: '❓', label: 'Desconhecido', color: 'text-gray-500' },
}

/* ─── Component ─── */
const ImportarNota = () => {
    /* State — upload */
    const [file, setFile] = useState<File | null>(null)
    const [preview, setPreview] = useState<string | null>(null)
    const [fileKind, setFileKind] = useState<FileKind>('unknown')
    const [dragOver, setDragOver] = useState(false)
    const fileInputRef = useRef<HTMLInputElement>(null)

    /* State — OCR task */
    const [taskId, setTaskId] = useState<string | null>(null)
    const [taskStatus, setTaskStatus] = useState<OCRTaskStatus['status'] | null>(null)
    const [errorMsg, setErrorMsg] = useState<string | null>(null)
    const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

    /* State — items to review */
    const [itens, setItens] = useState<ItemExtraido[]>([])
    const [fornecedorGlobal, setFornecedorGlobal] = useState('')
    const [nomeFantasiaFornecedor, setNomeFantasiaFornecedor] = useState('')
    const [cnpjFornecedor, setCnpjFornecedor] = useState('')
    const [numeroNota, setNumeroNota] = useState('')
    const [dataEmissaoNota, setDataEmissaoNota] = useState('')
    const [valorTotalNota, setValorTotalNota] = useState<number>(0)
    const [fornecedorStatus, setFornecedorStatus] = useState<'novo' | 'existente' | null>(null)
    const [fornecedorId, setFornecedorId] = useState<number | null>(null)

    /* State — step tracker */
    type Step = 'upload' | 'processing' | 'review' | 'done'
    const [step, setStep] = useState<Step>('upload')

    /* ─── File handling ─── */
    const handleFileSelect = useCallback((selectedFile: File) => {
        const kind = detectFileKind(selectedFile)
        if (kind === 'unknown') {
            toast.error('Arquivo não suportado. Envie o XML da NFe.')
            return
        }
        setFile(selectedFile)
        setFileKind(kind)
        setPreview(null)
        setErrorMsg(null)
    }, [])

    const handleDrop = useCallback(
        (e: React.DragEvent<HTMLDivElement>) => {
            e.preventDefault()
            setDragOver(false)
            const dropped = e.dataTransfer.files[0]
            if (dropped) handleFileSelect(dropped)
        },
        [handleFileSelect]
    )

    const handleFileInput = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            const selected = e.target.files?.[0]
            if (selected) handleFileSelect(selected)
        },
        [handleFileSelect]
    )

    /* ─── Helper: process completed task data ─── */
    const handleTaskCompleted = useCallback((data: OCRTaskStatus) => {
        if (!data.result) return

        if (data.result.nota_fiscal) {
            const nf = data.result.nota_fiscal
            setFornecedorGlobal(nf.fornecedor || '')
            setNomeFantasiaFornecedor(nf.nome_fantasia_fornecedor || '')
            setCnpjFornecedor(nf.cnpj_fornecedor || '')
            setNumeroNota(nf.numero_nota || '')
            setDataEmissaoNota(nf.data_emissao || '')
            setValorTotalNota(nf.valor_total || 0)
            setFornecedorStatus(nf.fornecedor_status || null)
            setFornecedorId(nf.fornecedor_id || null)

            const mapped: ItemExtraido[] = (nf.produtos || []).map((p) => ({
                key: nextKey(),
                nome: p.nome,
                quantidade: p.quantidade,
                preco_unitario: p.preco_unitario,
                unidade: p.unidade || 'UN',
                codigo_ncm: p.codigo_ncm || '',
                codigo_barras: p.codigo_barras || '',
                fornecedor: nf.fornecedor || '',
                selecionado: true,
            }))
            setItens(mapped)
        } else {
            const produtos = data.result.produtos || []
            const quantidades = data.result.quantidade || []
            const valores = data.result.valor || []
            const mapped: ItemExtraido[] = produtos.map((nome, i) => ({
                key: nextKey(),
                nome,
                quantidade: quantidades[i] || 1,
                preco_unitario: valores[i] || 0,
                unidade: 'UN',
                codigo_ncm: '',
                codigo_barras: '',
                fornecedor: '',
                selecionado: true,
            }))
            setItens(mapped)
        }

        setStep('review')
    }, [])

    /* ─── Upload mutation ─── */
    const uploadMutation = useMutation({
        mutationFn: async (fileToUpload: File) => {
            const formData = new FormData()
            formData.append('file', fileToUpload)

            const res = await api.post('/ocr/upload-arquivo', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            })
            return res.data as OCRTaskResponse
        },
        onSuccess: (data) => {
            setTaskId(data.task_id)
            setTaskStatus('completed')
            api.get(`/ocr/status/${data.task_id}`).then((res) => {
                handleTaskCompleted(res.data as OCRTaskStatus)
                toast.success(data.message || 'XML processado com sucesso!')
            })
        },
        onError: (err: any) => {
            const detail = err?.response?.data?.message ?? err?.response?.data?.detail ?? 'Erro ao enviar arquivo. Tente novamente.'
            toast.error(detail)
            setErrorMsg(detail)
        },
    })

    const handleUpload = () => {
        if (!file) {
            toast.error('Selecione um arquivo primeiro.')
            return
        }
        uploadMutation.mutate(file)
    }

    /* ─── Polling ─── */
    const pollingStartRef = useRef<number | null>(null)
    const POLLING_TIMEOUT_MS = 3 * 60 * 1000 // 3 minutos

    useEffect(() => {
        if (!taskId || taskStatus === 'completed' || taskStatus === 'failed') {
            if (pollingRef.current) clearInterval(pollingRef.current)
            pollingStartRef.current = null
            return
        }

        if (!pollingStartRef.current) {
            pollingStartRef.current = Date.now()
        }

        const poll = async () => {
            // Timeout de segurança: se passar 3 minutos sem resposta, aborta
            if (pollingStartRef.current && Date.now() - pollingStartRef.current > POLLING_TIMEOUT_MS) {
                if (pollingRef.current) clearInterval(pollingRef.current)
                setErrorMsg('Tempo limite excedido. O servidor pode ter reiniciado durante o processamento. Tente novamente.')
                toast.error('Tempo limite de processamento excedido.')
                setStep('upload')
                pollingStartRef.current = null
                return
            }

            try {
                const res = await api.get(`/ocr/status/${taskId}`)
                const data = res.data as OCRTaskStatus

                setTaskStatus(data.status)

                if (data.status === 'completed' && data.result) {
                    handleTaskCompleted(data)
                    toast.success('Processamento concluído! Revise os itens antes de importar.')
                }

                if (data.status === 'failed') {
                    setErrorMsg(data.error || 'Falha no processamento.')
                    toast.error(data.error || 'Falha no processamento.')
                    setStep('upload')
                }
            } catch (err: any) {
                // 404 significa que a task sumiu (servidor reiniciou)
                if (err?.response?.status === 404) {
                    if (pollingRef.current) clearInterval(pollingRef.current)
                    setErrorMsg('Tarefa não encontrada. O servidor pode ter reiniciado. Tente enviar o arquivo novamente.')
                    toast.error('Tarefa perdida — envie o arquivo novamente.')
                    setStep('upload')
                }
                // outros erros: silently retry
            }
        }

        pollingRef.current = setInterval(poll, POLLING_INTERVAL)
        poll() // immediate first call
        return () => {
            if (pollingRef.current) clearInterval(pollingRef.current)
        }
    }, [taskId, taskStatus, handleTaskCompleted])

    /* ─── Item editing ─── */
    const updateItem = (key: string, field: keyof ItemExtraido, value: string | number | boolean) => {
        setItens((prev) =>
            prev.map((item) => (item.key === key ? { ...item, [field]: value } : item))
        )
    }

    const removeItem = (key: string) => {
        setItens((prev) => prev.filter((item) => item.key !== key))
    }

    const addItem = () => {
        setItens((prev) => [
            ...prev,
            {
                key: nextKey(),
                nome: '',
                quantidade: 1,
                preco_unitario: 0,
                unidade: 'UN',
                codigo_ncm: '',
                codigo_barras: '',
                fornecedor: fornecedorGlobal,
                selecionado: true,
            },
        ])
    }

    const toggleSelectAll = (checked: boolean) => {
        setItens((prev) => prev.map((item) => ({ ...item, selecionado: checked })))
    }

    const selectedItems = itens.filter((i) => i.selecionado)
    const allSelected = itens.length > 0 && itens.every((i) => i.selecionado)

    /* ─── Import mutation ─── */
    const importMutation = useMutation({
        mutationFn: async (items: ItemExtraido[]) => {
            const produtos = items.map((item) => ({
                nome: item.nome,
                fornecedor: item.fornecedor || fornecedorGlobal || 'Não informado',
                preco_unitario: item.preco_unitario,
                preco_liquido: item.preco_unitario,
                codigo_ncm: item.codigo_ncm || undefined,
                codigo_barras: item.codigo_barras || undefined,
                unidade: item.unidade || 'UN',
                numero_nota: numeroNota || undefined,
                cnpj_fornecedor: cnpjFornecedor || undefined,
                quantidade_inicial: item.quantidade,
            }))

            const results = []
            const erros: string[] = []

            for (const prod of produtos) {
                try {
                    const res = await api.post('/produtos/', prod)
                    results.push(res.data)
                } catch (err: any) {
                    const detail = err?.response?.data?.message ?? err?.response?.data?.detail ?? `Erro ao cadastrar "${prod.nome}"`
                    erros.push(detail)
                }
            }

            return { results, erros }
        },
        onSuccess: ({ results, erros }) => {
            if (results.length > 0) {
                toast.success(`${results.length} produto(s) importado(s) com sucesso!`)
            }
            if (erros.length > 0) {
                erros.forEach((e) => toast.error(e))
            }
            if (results.length > 0) {
                setStep('done')
            }
        },
        onError: (err: any) => {
            const detail = err?.response?.data?.message ?? err?.response?.data?.detail ?? 'Erro ao importar produtos.'
            toast.error(detail)
        },
    })

    const handleImport = () => {
        if (selectedItems.length === 0) {
            toast.error('Selecione pelo menos um item para importar.')
            return
        }

        const hasEmpty = selectedItems.some((i) => !i.nome.trim())
        if (hasEmpty) {
            toast.error('Todos os itens devem ter um nome preenchido.')
            return
        }

        importMutation.mutate(selectedItems)
    }

    const handleReset = () => {
        setFile(null)
        setPreview(null)
        setFileKind('unknown')
        setTaskId(null)
        setTaskStatus(null)
        setErrorMsg(null)
        setItens([])
        setFornecedorGlobal('')
        setNomeFantasiaFornecedor('')
        setCnpjFornecedor('')
        setNumeroNota('')
        setDataEmissaoNota('')
        setValorTotalNota(0)
        setFornecedorStatus(null)
        setFornecedorId(null)
        setStep('upload')
        if (fileInputRef.current) fileInputRef.current.value = ''
    }

    /* ─── Step indicator ─── */
    const steps = [
        { id: 'upload', label: '1. Upload', icon: '📤' },
        { id: 'processing', label: '2. Processando', icon: '⚙️' },
        { id: 'review', label: '3. Revisão', icon: '✏️' },
        { id: 'done', label: '4. Concluído', icon: '✅' },
    ]

    const stepIndex = steps.findIndex((s) => s.id === step)

    return (
        <div className="container mx-auto space-y-6">
            {/* Header */}
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">
                        Importar Nota Fiscal
                    </h1>
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                        Envie o XML da NFe — os itens serão extraídos automaticamente para revisão
                    </p>
                </div>
                {step !== 'upload' && (
                    <button
                        type="button"
                        onClick={handleReset}
                        className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-sm text-gray-700 dark:text-gray-200 transition hover:bg-gray-50 dark:hover:bg-gray-700"
                    >
                        Nova Importação
                    </button>
                )}
            </div>

            {/* Steps indicator */}
            <div className="rounded-lg bg-white p-4 shadow dark:bg-gray-800">
                <div className="flex items-center justify-between">
                    {steps.map((s, i) => (
                        <div key={s.id} className="flex items-center flex-1">
                            <div className="flex flex-col items-center flex-1">
                                <div
                                    className={`flex h-10 w-10 items-center justify-center rounded-full text-lg transition-all duration-300 ${i <= stepIndex
                                        ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                                        : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                                        }`}
                                >
                                    {s.icon}
                                </div>
                                <span
                                    className={`mt-2 text-xs font-medium ${i <= stepIndex
                                        ? 'text-blue-600 dark:text-blue-400'
                                        : 'text-gray-400 dark:text-gray-500'
                                        }`}
                                >
                                    {s.label}
                                </span>
                            </div>
                            {i < steps.length - 1 && (
                                <div
                                    className={`h-0.5 w-full transition-all duration-500 ${i < stepIndex ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                                        }`}
                                />
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* ─── STEP 1: Upload ─── */}
            {step === 'upload' && (
                <div className="space-y-4">
                    {/* Drop Zone */}
                    <div
                        className={`relative cursor-pointer rounded-xl border-2 border-dashed p-12 text-center transition-all duration-300 ${dragOver
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                            : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:border-blue-400 hover:bg-gray-50 dark:hover:bg-gray-750'
                            }`}
                        onDragOver={(e) => {
                            e.preventDefault()
                            setDragOver(true)
                        }}
                        onDragLeave={() => setDragOver(false)}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept={ACCEPT_STRING}
                            className="hidden"
                            onChange={handleFileInput}
                        />

                        {file ? (
                            <div className="space-y-4">
                                {preview ? (
                                    <img
                                        src={preview}
                                        alt="Preview da nota fiscal"
                                        className="mx-auto max-h-64 rounded-lg shadow-md"
                                    />
                                ) : (
                                    <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-gray-100 dark:bg-gray-700 text-4xl">
                                        {FILE_KIND_LABELS[fileKind].icon}
                                    </div>
                                )}
                                <div className="flex items-center justify-center gap-2">
                                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${fileKind === 'xml' ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300' : fileKind === 'pdf' ? 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300' : 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300'}`}>
                                        {FILE_KIND_LABELS[fileKind].label}
                                    </span>
                                </div>
                                <p className="text-sm font-medium text-gray-700 dark:text-gray-200">
                                    {file.name}
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                    Dados serão extraídos diretamente do XML da NFe
                                </p>
                                <p className="text-xs text-gray-400 dark:text-gray-500">
                                    Clique ou arraste outro arquivo para substituir
                                </p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/40 text-3xl">
                                    �
                                </div>
                                <p className="text-lg font-medium text-gray-700 dark:text-gray-200">
                                    Arraste o arquivo da nota fiscal aqui
                                </p>
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                    ou clique para selecionar
                                </p>
                                <div className="flex flex-col items-center gap-2 pt-1">
                                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 dark:bg-emerald-900/40 px-3 py-1 text-xs font-medium text-emerald-700 dark:text-emerald-300">
                                        📋 XML de NFe
                                    </span>
                                    <p className="text-xs text-gray-400 dark:text-gray-500">
                                        Importação via imagem ou PDF estará disponível em breve
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>

                    {errorMsg && (
                        <div className="rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 p-4 text-sm text-red-700 dark:text-red-300">
                            {errorMsg}
                        </div>
                    )}

                    {file && (
                        <div className="flex justify-end gap-3">
                            <button
                                type="button"
                                onClick={handleReset}
                                className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-200 transition hover:bg-gray-50 dark:hover:bg-gray-700"
                            >
                                Limpar
                            </button>
                            <button
                                type="button"
                                onClick={handleUpload}
                                disabled={uploadMutation.isPending}
                                className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white shadow transition hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                            >
                                {uploadMutation.isPending ? (
                                <>
                                <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                                Enviando...
                                </>
                                ) : (
                                <>📋 Processar XML</>
                                )}
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Etapa de processamento removida — XML é processado de forma síncrona e instantânea */}

            {/* ─── STEP 3: Review ─── */}
            {step === 'review' && (
                <div className="space-y-4">
                    {/* Invoice header info */}
                    <div className="rounded-lg bg-white p-5 shadow dark:bg-gray-800">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Dados da Nota Fiscal</h2>
                            {fornecedorStatus === 'novo' && (
                                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 dark:bg-emerald-900/40 px-3 py-1 text-xs font-medium text-emerald-700 dark:text-emerald-300">
                                    ✅ Fornecedor novo — cadastrado automaticamente
                                </span>
                            )}
                            {fornecedorStatus === 'existente' && (
                                <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-100 dark:bg-blue-900/40 px-3 py-1 text-xs font-medium text-blue-700 dark:text-blue-300">
                                    🔍 Fornecedor já cadastrado
                                    {fornecedorId && (
                                        <a href={`/fornecedores`} className="underline opacity-70 hover:opacity-100">ver</a>
                                    )}
                                </span>
                            )}
                        </div>
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                            <div>
                                <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                                    Fornecedor
                                </label>
                                <input
                                    type="text"
                                    value={fornecedorGlobal}
                                    onChange={(e) => setFornecedorGlobal(e.target.value)}
                                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="Nome do fornecedor"
                                />
                            </div>
                            <div>
                                <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                                    Nome Fantasia
                                </label>
                                <input
                                    type="text"
                                    value={nomeFantasiaFornecedor}
                                    onChange={(e) => setNomeFantasiaFornecedor(e.target.value)}
                                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="Nome fantasia (se houver)"
                                />
                            </div>
                            <div>
                                <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                                    CNPJ
                                </label>
                                <input
                                    type="text"
                                    value={cnpjFornecedor}
                                    onChange={(e) => setCnpjFornecedor(e.target.value)}
                                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="00.000.000/0000-00"
                                />
                            </div>
                            <div>
                                <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                                    Nº Nota Fiscal
                                </label>
                                <input
                                    type="text"
                                    value={numeroNota}
                                    onChange={(e) => setNumeroNota(e.target.value)}
                                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="Número da nota"
                                />
                            </div>
                            <div>
                                <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                                    Data de Emissão
                                </label>
                                <input
                                    type="text"
                                    value={dataEmissaoNota}
                                    onChange={(e) => setDataEmissaoNota(e.target.value)}
                                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="YYYY-MM-DD"
                                />
                            </div>
                            <div>
                                <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                                    Valor Total da Nota
                                </label>
                                <input
                                    type="text"
                                    value={moneyFormatter.format(valorTotalNota || 0)}
                                    readOnly
                                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/70 px-3 py-2 text-sm font-medium text-gray-800 dark:text-gray-100"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Summary cards */}
                    <div className="grid gap-4 md:grid-cols-3">
                        <div className="rounded-lg bg-white p-4 shadow dark:bg-gray-800">
                            <p className="text-xs text-gray-500 dark:text-gray-400">Itens encontrados</p>
                            <p className="text-2xl font-semibold text-gray-800 dark:text-gray-100">{itens.length}</p>
                        </div>
                        <div className="rounded-lg bg-white p-4 shadow dark:bg-gray-800">
                            <p className="text-xs text-gray-500 dark:text-gray-400">Selecionados para importar</p>
                            <p className="text-2xl font-semibold text-blue-600 dark:text-blue-400">
                                {selectedItems.length}
                            </p>
                        </div>
                        <div className="rounded-lg bg-white p-4 shadow dark:bg-gray-800">
                            <p className="text-xs text-gray-500 dark:text-gray-400">Valor total estimado</p>
                            <p className="text-2xl font-semibold text-emerald-600 dark:text-emerald-400">
                                {moneyFormatter.format(
                                    selectedItems.reduce((sum, i) => sum + i.preco_unitario * i.quantidade, 0)
                                )}
                            </p>
                        </div>
                    </div>

                    {/* Items table */}
                    <div className="overflow-hidden rounded-lg bg-white shadow dark:bg-gray-800">
                        <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-5 py-3">
                            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
                                Itens para Importação
                            </h3>
                            <button
                                type="button"
                                onClick={addItem}
                                className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-emerald-700"
                            >
                                + Adicionar Item
                            </button>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                                <thead className="bg-gray-50 dark:bg-gray-700">
                                    <tr>
                                        <th className="px-3 py-3 text-left">
                                            <input
                                                type="checkbox"
                                                checked={allSelected}
                                                onChange={(e) => toggleSelectAll(e.target.checked)}
                                                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                            />
                                        </th>
                                        {['Produto', 'Qtd', 'Unidade', 'Preço Unit.', 'NCM', 'Subtotal', ''].map(
                                            (header) => (
                                                <th
                                                    key={header}
                                                    className="px-3 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300"
                                                >
                                                    {header}
                                                </th>
                                            )
                                        )}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                    {itens.length === 0 ? (
                                        <tr>
                                            <td
                                                colSpan={8}
                                                className="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400"
                                            >
                                                Nenhum item encontrado. Clique em "+ Adicionar Item" para inserir manualmente.
                                            </td>
                                        </tr>
                                    ) : (
                                        itens.map((item) => (
                                            <tr
                                                key={item.key}
                                                className={`transition-colors ${item.selecionado
                                                    ? 'bg-white dark:bg-gray-800'
                                                    : 'bg-gray-50 dark:bg-gray-900 opacity-60'
                                                    }`}
                                            >
                                                <td className="px-3 py-2">
                                                    <input
                                                        type="checkbox"
                                                        checked={item.selecionado}
                                                        onChange={(e) => updateItem(item.key, 'selecionado', e.target.checked)}
                                                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                                    />
                                                </td>
                                                <td className="px-3 py-2">
                                                    <input
                                                        type="text"
                                                        value={item.nome}
                                                        onChange={(e) => updateItem(item.key, 'nome', e.target.value)}
                                                        className="w-full min-w-[200px] rounded border border-gray-300 dark:border-gray-600 bg-transparent px-2 py-1.5 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                        placeholder="Nome do produto"
                                                    />
                                                </td>
                                                <td className="px-3 py-2">
                                                    <input
                                                        type="number"
                                                        min={1}
                                                        value={item.quantidade}
                                                        onChange={(e) =>
                                                            updateItem(item.key, 'quantidade', parseInt(e.target.value) || 1)
                                                        }
                                                        className="w-20 rounded border border-gray-300 dark:border-gray-600 bg-transparent px-2 py-1.5 text-sm text-gray-800 dark:text-gray-100 text-center focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                    />
                                                </td>
                                                <td className="px-3 py-2">
                                                    <select
                                                        value={item.unidade}
                                                        onChange={(e) => updateItem(item.key, 'unidade', e.target.value)}
                                                        className="rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1.5 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                    >
                                                        <option value="UN">UN</option>
                                                        <option value="CX">CX</option>
                                                        <option value="M">M</option>
                                                        <option value="KG">KG</option>
                                                        <option value="PC">PC</option>
                                                        <option value="RL">RL</option>
                                                    </select>
                                                </td>
                                                <td className="px-3 py-2">
                                                    <input
                                                        type="number"
                                                        min={0}
                                                        step={0.01}
                                                        value={item.preco_unitario}
                                                        onChange={(e) =>
                                                            updateItem(
                                                                item.key,
                                                                'preco_unitario',
                                                                parseFloat(e.target.value) || 0
                                                            )
                                                        }
                                                        className="w-28 rounded border border-gray-300 dark:border-gray-600 bg-transparent px-2 py-1.5 text-sm text-gray-800 dark:text-gray-100 text-right focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                    />
                                                </td>
                                                <td className="px-3 py-2">
                                                    <input
                                                        type="text"
                                                        value={item.codigo_ncm}
                                                        onChange={(e) => updateItem(item.key, 'codigo_ncm', e.target.value)}
                                                        className="w-28 rounded border border-gray-300 dark:border-gray-600 bg-transparent px-2 py-1.5 text-sm text-gray-800 dark:text-gray-100 text-center focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                        placeholder="00000000"
                                                    />
                                                </td>
                                                <td className="px-3 py-2 text-right text-sm font-medium text-gray-800 dark:text-gray-100 whitespace-nowrap">
                                                    {moneyFormatter.format(item.preco_unitario * item.quantidade)}
                                                </td>
                                                <td className="px-3 py-2">
                                                    <button
                                                        type="button"
                                                        onClick={() => removeItem(item.key)}
                                                        className="rounded p-1 text-red-500 transition hover:bg-red-50 dark:hover:bg-red-900/30 hover:text-red-700"
                                                        title="Remover item"
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
                    </div>

                    {/* Alert about review */}
                    <div className="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 p-4">
                        <div className="flex items-start gap-3">
                            <span className="text-xl">⚠️</span>
                            <div>
                                <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                                    Revise todos os itens antes de importar
                                </p>
                                <p className="mt-1 text-xs text-amber-700 dark:text-amber-300">
                                Confira nomes, quantidades, preços e NCM antes de importar.
                                Itens desmarcados não serão importados. Cada item será cadastrado como um novo produto com estoque inicial.
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Action buttons */}
                    <div className="flex items-center justify-between">
                        <button
                            type="button"
                            onClick={handleReset}
                            className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-200 transition hover:bg-gray-50 dark:hover:bg-gray-700"
                        >
                            Cancelar
                        </button>
                        <button
                            type="button"
                            onClick={handleImport}
                            disabled={importMutation.isPending || selectedItems.length === 0}
                            className="rounded-lg bg-emerald-600 px-8 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-500/30 transition hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        >
                            {importMutation.isPending ? (
                                <>
                                    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                                    Importando...
                                </>
                            ) : (
                                <>
                                    ✅ Importar {selectedItems.length} {selectedItems.length === 1 ? 'Produto' : 'Produtos'}
                                </>
                            )}
                        </button>
                    </div>
                </div>
            )}

            {/* ─── STEP 4: Done ─── */}
            {step === 'done' && (
                <div className="flex flex-col items-center justify-center space-y-6 rounded-lg bg-white p-12 shadow dark:bg-gray-800">
                    <div className="flex h-20 w-20 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/40 text-4xl">
                        ✅
                    </div>
                    <div className="text-center">
                        <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">
                            Importação Concluída!
                        </h2>
                        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                            Todos os produtos foram cadastrados com sucesso, incluindo o estoque inicial.
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            type="button"
                            onClick={handleReset}
                            className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700"
                        >
                            📤 Importar Outra Nota
                        </button>
                        <a
                            href="/produtos"
                            className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-6 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-200 transition hover:bg-gray-50 dark:hover:bg-gray-700"
                        >
                            📦 Ver Produtos
                        </a>
                    </div>
                </div>
            )}
        </div>
    )
}

export default ImportarNota
