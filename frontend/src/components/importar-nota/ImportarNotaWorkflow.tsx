import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import toast from 'react-hot-toast'

import ModalDuplicatas from '../ModalDuplicatas'
import api from '../../services/api'
import type { DuplicateResolution, SimilarItem } from '../../types/importacaoNota'

/* Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
   TYPES
Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬ */
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
    // IA
    aiStatus?: 'checking' | 'duplicata_exata' | 'similar' | 'ok' | 'erro'
    aiNomeExistente?: string
    aiProdutoId?: number
    aiSimilaridade?: number
    aiNivel?: 'duplicata' | 'alerta'
}

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

interface AuditoriaFiscalFator {
    regra: string
    resultado: 'passou' | 'falha'
    peso: number
    detalhe: string
}

interface AuditoriaFiscal {
    classificacao: 'baixo' | 'medio' | 'alto'
    score: number
    confianca: number
    explicacao: string
    fatores: AuditoriaFiscalFator[]
    versao_engine: string
}

interface ValidacaoCruzadaItem {
    regra: string
    severidade: 'erro' | 'alerta' | 'info'
    item_sequencia: number | null
    descricao: string
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
        auditoria_fiscal?: AuditoriaFiscal | null
        validacao_cruzada?: ValidacaoCruzadaItem[]
        produtos?: string[]; quantidade?: number[]; valor?: number[]
    }
    error?: string
}

/* Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
   HELPERS
Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬ */
const moneyFormatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
let keyCounter = 0
const nextKey = () => `item-${++keyCounter}`
const POLLING_INTERVAL = 2000
const ACCEPT_STRING = '.xml,text/xml,application/xml'
const normalizeProductName = (value: string) => value.trim().toLowerCase()
const normalizeForAutoMerge = (value: string) =>
    value
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^\w]/g, '')
        .toLowerCase()
type FileKind = 'xml' | 'unknown'
function detectFileKind(file: File): FileKind {
    const name = file.name.toLowerCase()
    if (name.endsWith('.xml') || file.type.includes('xml')) return 'xml'
    return 'unknown'
}
const FILE_KIND_LABELS: Record<FileKind, { icon: string; label: string }> = {
    xml: { icon: 'Ã°Å¸â€œâ€¹', label: 'XML de NFe' },
    unknown: { icon: 'Ã¢Ââ€œ', label: 'Desconhecido' },
}

/* Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
   MODAL DE CONFIRMAÃƒâ€¡ÃƒÆ’O DE DUPLICATAS SIMILARES
Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬ */
const CLASSIFICACAO_CONFIG = {
    baixo: { emoji: 'Ã°Å¸Å¸Â¢', label: 'Baixo Risco', bg: 'bg-emerald-50 dark:bg-emerald-900/20', border: 'border-emerald-200 dark:border-emerald-700', text: 'text-emerald-800 dark:text-emerald-200', badge: 'bg-emerald-100 dark:bg-emerald-800 text-emerald-700 dark:text-emerald-200' },
    medio: { emoji: 'Ã°Å¸Å¸Â¡', label: 'Risco MÃƒÂ©dio', bg: 'bg-amber-50 dark:bg-amber-900/20', border: 'border-amber-200 dark:border-amber-700', text: 'text-amber-800 dark:text-amber-200', badge: 'bg-amber-100 dark:bg-amber-800 text-amber-700 dark:text-amber-200' },
    alto: { emoji: 'Ã°Å¸â€Â´', label: 'Alto Risco', bg: 'bg-red-50 dark:bg-red-900/20', border: 'border-red-200 dark:border-red-700', text: 'text-red-800 dark:text-red-200', badge: 'bg-red-100 dark:bg-red-800 text-red-700 dark:text-red-200' },
} as const

const SEVERIDADE_CONFIG = {
    erro: { emoji: 'Ã¢ÂÅ’', bg: 'bg-red-50 dark:bg-red-900/20', border: 'border-red-200 dark:border-red-700', text: 'text-red-700 dark:text-red-300' },
    alerta: { emoji: 'Ã¢Å¡Â Ã¯Â¸Â', bg: 'bg-amber-50 dark:bg-amber-900/20', border: 'border-amber-200 dark:border-amber-700', text: 'text-amber-700 dark:text-amber-300' },
    info: { emoji: 'Ã¢â€žÂ¹Ã¯Â¸Â', bg: 'bg-blue-50 dark:bg-blue-900/20', border: 'border-blue-200 dark:border-blue-700', text: 'text-blue-700 dark:text-blue-300' },
} as const

interface PainelAuditoriaFiscalProps {
    auditoria: AuditoriaFiscal | null
    validacaoCruzada: ValidacaoCruzadaItem[]
}

const PainelAuditoriaFiscal = ({ auditoria, validacaoCruzada }: PainelAuditoriaFiscalProps) => {
    const [expandido, setExpandido] = useState(false)

    if (!auditoria && validacaoCruzada.length === 0) return null

    const config = auditoria ? CLASSIFICACAO_CONFIG[auditoria.classificacao] : CLASSIFICACAO_CONFIG.baixo
    const erros = validacaoCruzada.filter(v => v.severidade === 'erro')
    const alertas = validacaoCruzada.filter(v => v.severidade === 'alerta')
    const infos = validacaoCruzada.filter(v => v.severidade === 'info')
    const fatoresFalha = auditoria?.fatores.filter(f => f.resultado === 'falha') ?? []

    return (
        <div className={`rounded-lg border ${config.border} ${config.bg} overflow-hidden transition-all`}>
            {/* Header */}
            <button
                type="button"
                onClick={() => setExpandido(!expandido)}
                className="w-full px-5 py-4 flex items-center justify-between hover:opacity-90 transition"
            >
                <div className="flex items-center gap-3">
                    <span className="text-2xl">{config.emoji}</span>
                    <div className="text-left">
                        <h3 className={`text-sm font-semibold ${config.text}`}>Auditoria Fiscal Ã¢â‚¬â€ {config.label}</h3>
                        <p className={`text-xs mt-0.5 ${config.text} opacity-75`}>
                            Score: {auditoria?.score ?? 0}/100 Ã‚Â· ConfianÃƒÂ§a: {Math.round((auditoria?.confianca ?? 0) * 100)}%
                            {validacaoCruzada.length > 0 && ` Ã‚Â· ${validacaoCruzada.length} verificaÃƒÂ§ÃƒÂ£o(ÃƒÂµes)`}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {erros.length > 0 && <span className="inline-flex items-center gap-1 rounded-full bg-red-100 dark:bg-red-800 px-2 py-0.5 text-xs font-medium text-red-700 dark:text-red-200">{erros.length} erro(s)</span>}
                    {alertas.length > 0 && <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 dark:bg-amber-800 px-2 py-0.5 text-xs font-medium text-amber-700 dark:text-amber-200">{alertas.length} alerta(s)</span>}
                    <span className={`text-sm ${config.text} transition-transform ${expandido ? 'rotate-180' : ''}`}>Ã¢â€“Â¼</span>
                </div>
            </button>

            {/* ConteÃƒÂºdo expandido */}
            {expandido && (
                <div className="px-5 pb-4 space-y-3 border-t border-gray-200/50 dark:border-gray-700/50 pt-3">
                    {/* Fatores de risco do engine */}
                    {fatoresFalha.length > 0 && (
                        <div>
                            <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Regras fiscais com falha</h4>
                            <div className="space-y-1.5">
                                {fatoresFalha.map((f, i) => (
                                    <div key={i} className="flex items-start gap-2 rounded-lg bg-white/60 dark:bg-gray-800/60 px-3 py-2 text-sm">
                                        <span className="text-red-500 mt-0.5">Ã¢Å¡Â Ã¯Â¸Â</span>
                                        <div className="flex-1 min-w-0">
                                            <p className="font-medium text-gray-700 dark:text-gray-200">{f.regra.replace(/_/g, ' ')}</p>
                                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{f.detalhe}</p>
                                        </div>
                                        <span className="text-xs text-gray-400 whitespace-nowrap">peso {f.peso}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* ValidaÃƒÂ§ÃƒÂ£o cruzada */}
                    {validacaoCruzada.length > 0 && (
                        <div>
                            <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">ValidaÃƒÂ§ÃƒÂ£o cruzada</h4>
                            <div className="space-y-1.5">
                                {validacaoCruzada.map((v, i) => {
                                    const sev = SEVERIDADE_CONFIG[v.severidade] ?? SEVERIDADE_CONFIG.info
                                    return (
                                        <div key={i} className={`flex items-start gap-2 rounded-lg ${sev.bg} border ${sev.border} px-3 py-2 text-sm`}>
                                            <span className="mt-0.5">{sev.emoji}</span>
                                            <p className={`flex-1 ${sev.text}`}>{v.descricao}</p>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    )}

                    {/* Sem problemas */}
                    {fatoresFalha.length === 0 && validacaoCruzada.length === 0 && (
                        <p className="text-sm text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
                            Ã¢Å“â€¦ Nenhuma inconsistÃƒÂªncia detectada na nota fiscal.
                        </p>
                    )}

                    <p className="text-xs text-gray-400 dark:text-gray-500 pt-1">
                        Motor v{auditoria?.versao_engine ?? '?'} Ã‚Â· {infos.length > 0 ? `${infos.length} informativo(s)` : 'Sem informativos'}
                    </p>
                </div>
            )}
        </div>
    )
}

/* Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
   COMPONENT
Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬ */
const ImportarNota = () => {
    return (
        <div className="container mx-auto space-y-6">
            <div>
                <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Importar Nota Fiscal</h1>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    Importe o XML da NFe, revise os itens extraÃƒÂ­dos e cadastre os produtos no estoque
                </p>
            </div>
            <TabImportar />
        </div>
    )
}

/* Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
   TAB: IMPORTAR XML
Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬ */
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
    const [aiChecking, setAiChecking] = useState(false)

    // Auditoria fiscal
    const [auditoriaFiscal, setAuditoriaFiscal] = useState<AuditoriaFiscal | null>(null)
    const [validacaoCruzada, setValidacaoCruzada] = useState<ValidacaoCruzadaItem[]>([])

    // Modal de duplicatas similares
    const [modalItens, setModalItens] = useState<SimilarItem[]>([])
    const [showModal, setShowModal] = useState(false)
    const pendingImportRef = useRef<ItemExtraido[]>([])
    const runAiCheckRef = useRef<(itemsList: ItemExtraido[]) => Promise<void>>(async () => {})

    type Step = 'upload' | 'processing' | 'review' | 'done'
    const [step, setStep] = useState<Step>('upload')

    const handleFileSelect = useCallback((selectedFile: File) => {
        const kind = detectFileKind(selectedFile)
        if (kind === 'unknown') { toast.error('Arquivo nÃƒÂ£o suportado. Envie o XML da NFe.'); return }
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
        let mapped: ItemExtraido[] = []
        // Extrair dados de auditoria fiscal (independente do bloco nota_fiscal)
        if (data.result.auditoria_fiscal) {
            setAuditoriaFiscal(data.result.auditoria_fiscal)
        }
        if (data.result.validacao_cruzada) {
            setValidacaoCruzada(data.result.validacao_cruzada)
        }
        if (data.result.nota_fiscal) {
            const nf = data.result.nota_fiscal
            setFornecedorGlobal(nf.fornecedor || ''); setNomeFantasiaFornecedor(nf.nome_fantasia_fornecedor || '')
            setCnpjFornecedor(nf.cnpj_fornecedor || ''); setNumeroNota(nf.numero_nota || '')
            setDataEmissaoNota(nf.data_emissao || ''); setValorTotalNota(nf.valor_total || 0)
            setFornecedorStatus(nf.fornecedor_status || null)
            mapped = (nf.produtos || []).map((p) => ({
                key: nextKey(), nome: p.nome, quantidade: p.quantidade, preco_unitario: p.preco_unitario,
                unidade: p.unidade || 'UN', codigo_ncm: p.codigo_ncm || '', codigo_barras: p.codigo_barras || '',
                fornecedor: nf.fornecedor || '', selecionado: true,
            }))
        } else {
            const produtos = data.result.produtos || []; const quantidades = data.result.quantidade || []; const valores = data.result.valor || []
            mapped = produtos.map((nome, i) => ({
                key: nextKey(), nome, quantidade: quantidades[i] || 1, preco_unitario: valores[i] || 0,
                unidade: 'UN', codigo_ncm: '', codigo_barras: '', fornecedor: '', selecionado: true,
            }))
        }
        setItens(mapped)
        setStep('review')

        // Disparar verificaÃƒÂ§ÃƒÂ£o de IA logo apÃƒÂ³s carregar os itens
        if (mapped.length > 0) {
            setTimeout(() => {
                void runAiCheckRef.current(mapped)
            }, 300)
        }
    }, [])

    /* Ã¢â€â‚¬Ã¢â€â‚¬ VerificaÃƒÂ§ÃƒÂ£o de IA para todos os itens Ã¢â€â‚¬Ã¢â€â‚¬ */
    const runAiCheck = useCallback(async (itemsList: ItemExtraido[]) => {
        setAiChecking(true)
        const atualizados = [...itemsList]

        // Marcar todos como "verificando"
        setItens(prev => prev.map(it => ({ ...it, aiStatus: 'checking' })))

        for (let i = 0; i < atualizados.length; i++) {
            const item = atualizados[i]
            if (!item.nome.trim()) {
                atualizados[i] = { ...item, aiStatus: 'ok' }
                continue
            }
            try {
                const payload: Record<string, unknown> = { descricao: item.nome, limite: 3 }
                if (item.codigo_barras) payload.codigo_barras = item.codigo_barras

                const res = await api.post<DuplicateCheckResponse>('/ai/check-duplicate', payload)
                const data = res.data

                if (data.candidatos.length === 0) {
                    atualizados[i] = { ...item, aiStatus: 'ok' }
                } else {
                    const top = data.candidatos[0]
                    const nomeEquivalente =
                        normalizeForAutoMerge(top.produto_nome) === normalizeForAutoMerge(item.nome)
                    const mergeAutomatico =
                        data.metodo === 'barcode_exato' ||
                        data.metodo === 'nome_exato' ||
                        nomeEquivalente

                    if (mergeAutomatico) {
                        atualizados[i] = {
                            ...item,
                            aiStatus: 'duplicata_exata',
                            aiNomeExistente: top.produto_nome,
                            aiProdutoId: top.produto_id,
                            aiSimilaridade: top.similaridade,
                            aiNivel: top.nivel,
                        }
                    } else {
                        atualizados[i] = {
                            ...item,
                            aiStatus: 'similar',
                            aiNomeExistente: top.produto_nome,
                            aiProdutoId: top.produto_id,
                            aiSimilaridade: top.similaridade,
                            aiNivel: top.nivel,
                        }
                    }
                }
            } catch {
                atualizados[i] = { ...item, aiStatus: 'ok' }
            }
        }

        setItens(prev => prev.map(it => {
            const atualizado = atualizados.find(a => a.key === it.key)
            return atualizado ? { ...it, ...atualizado } : it
        }))
        setAiChecking(false)
    }, [])

    useEffect(() => {
        runAiCheckRef.current = runAiCheck
    }, [runAiCheck])

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
                if (data.status === 'completed' && data.result) { handleTaskCompleted(data); toast.success('Processamento concluÃƒÂ­do!') }
                if (data.status === 'failed') { setErrorMsg(data.error || 'Falha.'); toast.error(data.error || 'Falha.'); setStep('upload') }
            } catch (err: unknown) {
                if (isAxiosError(err) && err.response?.status === 404) {
                    if (pollingRef.current) clearInterval(pollingRef.current)
                    setErrorMsg('Tarefa nÃƒÂ£o encontrada. Reenvie o arquivo.'); toast.error('Tarefa perdida.'); setStep('upload')
                }
            }
        }
        pollingRef.current = setInterval(poll, POLLING_INTERVAL); poll()
        return () => { if (pollingRef.current) clearInterval(pollingRef.current) }
    }, [taskId, taskStatus, handleTaskCompleted, POLLING_TIMEOUT_MS])

    const updateItem = (key: string, field: keyof ItemExtraido, value: string | number | boolean) => {
        setItens(prev => prev.map(item => {
            if (item.key !== key) return item
            const updated = { ...item, [field]: value }
            // Se o nome foi alterado, limpar status de IA para re-verificar
            if (field === 'nome') {
                updated.aiStatus = undefined
                updated.aiNomeExistente = undefined
                updated.aiProdutoId = undefined
                updated.aiSimilaridade = undefined
                updated.aiNivel = undefined
            }
            return updated
        }))
    }

    const applyDuplicateResolution = (item: ItemExtraido, resolution: DuplicateResolution) => {
        if (resolution.mode === 'importado') return item

        const resolvedName = resolution.resolvedName.trim()
        if (!resolvedName) return item

        const matchesExisting =
            !!item.aiNomeExistente &&
            normalizeProductName(resolvedName) === normalizeProductName(item.aiNomeExistente)

        return {
            ...item,
            nome: resolvedName,
            aiStatus: matchesExisting ? 'duplicata_exata' : 'ok',
            aiNomeExistente: matchesExisting ? item.aiNomeExistente : undefined,
            aiProdutoId: matchesExisting ? item.aiProdutoId : undefined,
            aiSimilaridade: matchesExisting ? item.aiSimilaridade : undefined,
            aiNivel: matchesExisting ? item.aiNivel : undefined,
        }
    }

    const removeItem = (key: string) => setItens(prev => prev.filter(item => item.key !== key))
    const addItem = () => setItens(prev => [...prev, { key: nextKey(), nome: '', quantidade: 1, preco_unitario: 0, unidade: 'UN', codigo_ncm: '', codigo_barras: '', fornecedor: fornecedorGlobal, selecionado: true }])
    const toggleSelectAll = (checked: boolean) => setItens(prev => prev.map(item => ({ ...item, selecionado: checked })))
    const selectedItems = itens.filter(i => i.selecionado)
    const allSelected = itens.length > 0 && itens.every(i => i.selecionado)

    const importMutation = useMutation({
        mutationFn: async (items: ItemExtraido[]) => {
            const produtos = items.map(item => ({
                nome: item.nome, fornecedor: item.fornecedor || fornecedorGlobal || 'NÃƒÂ£o informado',
                preco_unitario: item.preco_unitario, preco_liquido: item.preco_unitario,
                codigo_ncm: item.codigo_ncm || undefined, codigo_barras: item.codigo_barras || undefined,
                unidade: item.unidade || 'UN', numero_nota: numeroNota || undefined,
                cnpj_fornecedor: cnpjFornecedor || undefined, quantidade_inicial: item.quantidade,
            }))
            const results: { produto: unknown; acao: string; barcodeStatus?: string }[] = []
            const erros: string[] = []
            for (const prod of produtos) {
                try {
                    const res = await api.post('/produtos/', prod)
                    const acao = res.headers['x-produto-acao'] ?? 'criado'
                    const barcodeStatus = res.headers['x-produto-barcode-status']
                    results.push({ produto: res.data, acao, barcodeStatus })
                } catch (err: unknown) {
                    erros.push(isAxiosError<{ message?: string; detail?: string }>(err)
                        ? err.response?.data?.message ?? err.response?.data?.detail ?? `Erro ao cadastrar "${prod.nome}"`
                        : `Erro ao cadastrar "${prod.nome}"`)
                }
            }
            return { results, erros }
        },
        onSuccess: ({ results, erros }) => {
            const criados = results.filter(r => r.acao === 'criado').length
            const somados = results.filter(r => r.acao === 'estoque_somado').length
            const barcodesPreenchidos = results.filter(r => r.barcodeStatus === 'preenchido').length
            const conflitosPreservados = results.filter(r => r.barcodeStatus === 'conflito_preservado').length
            const conflitosOutroProduto = results.filter(r => r.barcodeStatus === 'conflito_outro_produto').length
            if (criados > 0) toast.success(`${criados} produto(s) novo(s) cadastrado(s)!`)
            if (somados > 0) toast.success(`${somados} produto(s) com estoque somado ao existente!`)
            if (barcodesPreenchidos > 0) toast.success(`${barcodesPreenchidos} produto(s) existente(s) receberam codigo de barras da nota.`)
            if (conflitosPreservados > 0) toast(`${conflitosPreservados} produto(s) ja tinham codigo de barras diferente. O valor atual foi mantido.`)
            if (conflitosOutroProduto > 0) toast(`${conflitosOutroProduto} codigo(s) de barras da nota ja pertencem a outro produto e nao foram aplicados.`)
            erros.forEach(e => toast.error(e))
            if (results.length > 0) setStep('done')
        },
        onError: (err: unknown) => toast.error(isAxiosError<{ detail?: string }>(err)
            ? err.response?.data?.detail ?? 'Erro ao importar.' : 'Erro ao importar.'),
    })

    /* Ã¢â€â‚¬Ã¢â€â‚¬ Fluxo de importaÃƒÂ§ÃƒÂ£o com verificaÃƒÂ§ÃƒÂ£o de IA Ã¢â€â‚¬Ã¢â€â‚¬ */
    const handleImport = async () => {
        if (selectedItems.length === 0) { toast.error('Selecione pelo menos um item.'); return }
        if (selectedItems.some(i => !i.nome.trim())) { toast.error('Todos os itens devem ter um nome.'); return }

        // Coletar itens SIMILARES (nÃƒÂ£o exatos) que precisam de confirmaÃƒÂ§ÃƒÂ£o
        const itensSimilares: SimilarItem[] = selectedItems
            .filter(i => i.aiStatus === 'similar')
            .map(i => ({
                key: i.key,
                nomeImportando: i.nome,
                nomeExistente: i.aiNomeExistente!,
                produtoId: i.aiProdutoId!,
                similaridade: i.aiSimilaridade!,
                nivel: i.aiNivel!,
            }))

        if (itensSimilares.length > 0) {
            // Mostrar modal de confirmaÃƒÂ§ÃƒÂ£o
            pendingImportRef.current = selectedItems
            setModalItens(itensSimilares)
            setShowModal(true)
            return
        }

        // Sem similares problemÃƒÂ¡ticos Ã¢â€ â€™ importar direto
        importMutation.mutate(selectedItems)
    }

    const handleModalConfirmar = (resolutions: DuplicateResolution[]) => {
        const resolutionsByKey = new Map(resolutions.map((resolution) => [resolution.key, resolution]))
        const resolvedItems = pendingImportRef.current.map((item) => {
            const resolution = resolutionsByKey.get(item.key)
            return resolution ? applyDuplicateResolution(item, resolution) : item
        })

        setItens((prev) =>
            prev.map((item) => {
                const resolution = resolutionsByKey.get(item.key)
                return resolution ? applyDuplicateResolution(item, resolution) : item
            })
        )
        setShowModal(false)
        setModalItens([])
        pendingImportRef.current = []
        importMutation.mutate(resolvedItems)
    }

    const handleModalCancelar = () => {
        setShowModal(false)
        setModalItens([])
        pendingImportRef.current = []
    }

    const handleReset = () => {
        setFile(null); setFileKind('unknown'); setTaskId(null); setTaskStatus(null)
        setErrorMsg(null); setItens([]); setFornecedorGlobal(''); setNomeFantasiaFornecedor('')
        setCnpjFornecedor(''); setNumeroNota(''); setDataEmissaoNota(''); setValorTotalNota(0)
        setFornecedorStatus(null); setStep('upload'); setAiChecking(false)
        setShowModal(false); setModalItens([]); pendingImportRef.current = []
        setAuditoriaFiscal(null); setValidacaoCruzada([])
        if (fileInputRef.current) fileInputRef.current.value = ''
    }

    const steps = [
        { id: 'upload', label: '1. Upload', icon: 'Ã°Å¸â€œÂ¤' },
        { id: 'processing', label: '2. Processando', icon: 'Ã¢Å¡â„¢Ã¯Â¸Â' },
        { id: 'review', label: '3. RevisÃƒÂ£o', icon: 'Ã¢Å“ÂÃ¯Â¸Â' },
        { id: 'done', label: '4. ConcluÃƒÂ­do', icon: 'Ã¢Å“â€¦' },
    ]
    const stepIndex = steps.findIndex(s => s.id === step)

    // Contadores de status de IA
    const aiExatos = itens.filter(i => i.aiStatus === 'duplicata_exata').length
    const aiSimilares = itens.filter(i => i.aiStatus === 'similar').length

    return (
        <div className="space-y-6">
            {/* Modal de duplicatas similares */}
            {showModal && (
                <ModalDuplicatas
                    itens={modalItens}
                    onConfirmar={handleModalConfirmar}
                    onCancelar={handleModalCancelar}
                />
            )}

            {/* Header row */}
            <div className="flex justify-end">
                {step !== 'upload' && (
                    <button type="button" onClick={handleReset}
                        className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-sm text-gray-700 dark:text-gray-200 transition hover:bg-gray-50 dark:hover:bg-gray-700">
                        Nova ImportaÃƒÂ§ÃƒÂ£o
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
                                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/40 text-3xl">Ã°Å¸â€œÂ¤</div>
                                <p className="text-lg font-medium text-gray-700 dark:text-gray-200">Arraste o XML da NFe aqui</p>
                                <p className="text-sm text-gray-500">ou clique para selecionar</p>
                                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 dark:bg-emerald-900/40 px-3 py-1 text-xs font-medium text-emerald-700 dark:text-emerald-300">Ã°Å¸â€œâ€¹ XML de NFe</span>
                            </div>
                        )}
                    </div>
                    {errorMsg && <div className="rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 p-4 text-sm text-red-700 dark:text-red-300">{errorMsg}</div>}
                    {file && (
                        <div className="flex justify-end gap-3">
                            <button type="button" onClick={handleReset} className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-200 transition hover:bg-gray-50">Limpar</button>
                            <button type="button" onClick={handleUpload} disabled={uploadMutation.isPending}
                                className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white shadow transition hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2">
                                {uploadMutation.isPending ? <><span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" /> Enviando...</> : <>Ã°Å¸â€œâ€¹ Processar XML</>}
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* STEP 3: Review */}
            {step === 'review' && (
                <div className="space-y-4">
                    {/* Dados da Nota */}
                    <div className="rounded-lg bg-white p-5 shadow dark:bg-gray-800">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Dados da Nota Fiscal</h2>
                            {fornecedorStatus === 'novo' && <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 dark:bg-emerald-900/40 px-3 py-1 text-xs font-medium text-emerald-700 dark:text-emerald-300">Ã¢Å“â€¦ Fornecedor novo cadastrado</span>}
                            {fornecedorStatus === 'existente' && <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-100 dark:bg-blue-900/40 px-3 py-1 text-xs font-medium text-blue-700 dark:text-blue-300">Ã°Å¸â€Â Fornecedor jÃƒÂ¡ cadastrado</span>}
                        </div>
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                            {[
                                { label: 'Fornecedor', val: fornecedorGlobal, set: setFornecedorGlobal, ph: 'Nome do fornecedor' },
                                { label: 'Nome Fantasia', val: nomeFantasiaFornecedor, set: setNomeFantasiaFornecedor, ph: 'Nome fantasia' },
                                { label: 'CNPJ', val: cnpjFornecedor, set: setCnpjFornecedor, ph: '00.000.000/0000-00' },
                                { label: 'NÃ‚Âº Nota', val: numeroNota, set: setNumeroNota, ph: 'NÃƒÂºmero da nota' },
                                { label: 'Data EmissÃƒÂ£o', val: dataEmissaoNota, set: setDataEmissaoNota, ph: 'YYYY-MM-DD' },
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

                    {/* Cards de resumo */}
                    <div className="grid gap-4 md:grid-cols-4">
                        <div className="rounded-lg bg-white p-4 shadow dark:bg-gray-800"><p className="text-xs text-gray-500">Itens encontrados</p><p className="text-2xl font-semibold text-gray-800 dark:text-gray-100">{itens.length}</p></div>
                        <div className="rounded-lg bg-white p-4 shadow dark:bg-gray-800"><p className="text-xs text-gray-500">Selecionados</p><p className="text-2xl font-semibold text-blue-600 dark:text-blue-400">{selectedItems.length}</p></div>
                        <div className="rounded-lg bg-white p-4 shadow dark:bg-gray-800"><p className="text-xs text-gray-500">Valor estimado</p><p className="text-2xl font-semibold text-emerald-600 dark:text-emerald-400">{moneyFormatter.format(selectedItems.reduce((s, i) => s + i.preco_unitario * i.quantidade, 0))}</p></div>
                        <div className={`rounded-lg p-4 shadow ${aiChecking ? 'bg-blue-50 dark:bg-blue-900/20' : aiSimilares > 0 ? 'bg-amber-50 dark:bg-amber-900/20' : aiExatos > 0 ? 'bg-sky-50 dark:bg-sky-900/20' : 'bg-white dark:bg-gray-800'}`}>
                            <p className="text-xs text-gray-500">IA Ã¢â‚¬â€ VerificaÃƒÂ§ÃƒÂ£o</p>
                            {aiChecking
                                ? <p className="text-sm font-medium text-blue-600 dark:text-blue-400 flex items-center gap-1.5 mt-1"><span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" /> Verificando...</p>
                                : aiSimilares > 0
                                    ? <p className="text-sm font-semibold text-amber-700 dark:text-amber-300 mt-1">Ã¢Å¡Â Ã¯Â¸Â {aiSimilares} nome(s) parecido(s)</p>
                                    : aiExatos > 0
                                        ? <p className="text-sm font-semibold text-sky-700 dark:text-sky-300 mt-1">Ã°Å¸â€â€ž {aiExatos} jÃƒÂ¡ no estoque</p>
                                        : <p className="text-sm font-semibold text-emerald-600 dark:text-emerald-400 mt-1">Ã¢Å“â€¦ Sem duplicatas</p>
                            }
                        </div>
                    </div>

                    {/* Painel de Auditoria Fiscal */}
                    <PainelAuditoriaFiscal auditoria={auditoriaFiscal} validacaoCruzada={validacaoCruzada} />

                    {/* Banner de alerta de IA */}
                    {!aiChecking && (aiExatos > 0 || aiSimilares > 0) && (
                        <div className="rounded-lg border border-blue-200 dark:border-blue-700 bg-blue-50 dark:bg-blue-900/20 p-4">
                            <div className="flex items-start gap-3">
                                <span className="text-xl">Ã°Å¸Â¤â€“</span>
                                <div className="flex-1">
                                    <p className="text-sm font-semibold text-blue-800 dark:text-blue-200 mb-1">AnÃƒÂ¡lise de IA</p>
                                    <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-0.5">
                                        {aiExatos > 0 && <li>Ã¢â‚¬Â¢ <strong>{aiExatos} item(s) com nome idÃƒÂªntico</strong> ao jÃƒÂ¡ existente Ã¢â‚¬â€ o estoque serÃƒÂ¡ somado automaticamente, sem criar duplicata.</li>}
                                        {aiSimilares > 0 && <li>Ã¢â‚¬Â¢ <strong>{aiSimilares} item(s) com nome similar</strong> Ã¢â‚¬â€ vocÃƒÂª serÃƒÂ¡ alertado antes de confirmar a importaÃƒÂ§ÃƒÂ£o.</li>}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Tabela de itens */}
                    <div className="overflow-hidden rounded-lg bg-white shadow dark:bg-gray-800">
                        <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-5 py-3">
                            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100">Itens para ImportaÃƒÂ§ÃƒÂ£o</h3>
                            <button type="button" onClick={addItem} className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-emerald-700">+ Adicionar Item</button>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                                <thead className="bg-gray-50 dark:bg-gray-700">
                                    <tr>
                                        <th className="px-3 py-3"><input type="checkbox" checked={allSelected} onChange={e => toggleSelectAll(e.target.checked)} className="h-4 w-4 rounded border-gray-300 text-blue-600" /></th>
                                        {['Produto', 'Qtd', 'Unidade', 'PreÃƒÂ§o Unit.', 'NCM', 'Subtotal', 'Status IA', ''].map(h => <th key={h} className="px-3 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">{h}</th>)}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                    {itens.length === 0 ? (
                                        <tr><td colSpan={9} className="px-4 py-8 text-center text-sm text-gray-500">Nenhum item encontrado.</td></tr>
                                    ) : itens.map(item => (
                                        <tr key={item.key} className={`transition-colors ${item.selecionado ? 'bg-white dark:bg-gray-800' : 'bg-gray-50 dark:bg-gray-900 opacity-60'}`}>
                                            <td className="px-3 py-2"><input type="checkbox" checked={item.selecionado} onChange={e => updateItem(item.key, 'selecionado', e.target.checked)} className="h-4 w-4 rounded border-gray-300 text-blue-600" /></td>
                                            <td className="px-3 py-2">
                                                <input type="text" value={item.nome} onChange={e => updateItem(item.key, 'nome', e.target.value)}
                                                    className={`w-full min-w-[200px] rounded border px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-800 dark:text-gray-100 bg-transparent ${item.aiStatus === 'similar' ? 'border-amber-400 dark:border-amber-500' : item.aiStatus === 'duplicata_exata' ? 'border-sky-400 dark:border-sky-500' : 'border-gray-300 dark:border-gray-600'}`}
                                                    placeholder="Nome do produto" />
                                            </td>
                                            <td className="px-3 py-2"><input type="number" min={1} value={item.quantidade} onChange={e => updateItem(item.key, 'quantidade', parseInt(e.target.value) || 1)} className="w-20 rounded border border-gray-300 dark:border-gray-600 bg-transparent px-2 py-1.5 text-sm text-center focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-800 dark:text-gray-100" /></td>
                                            <td className="px-3 py-2">
                                                <select value={item.unidade} onChange={e => updateItem(item.key, 'unidade', e.target.value)} className="rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1.5 text-sm text-gray-800 dark:text-gray-100 focus:outline-none">
                                                    {['UN', 'CX', 'M', 'KG', 'PC', 'RL'].map(u => <option key={u} value={u}>{u}</option>)}
                                                </select>
                                            </td>
                                            <td className="px-3 py-2"><input type="number" min={0} step={0.01} value={item.preco_unitario} onChange={e => updateItem(item.key, 'preco_unitario', parseFloat(e.target.value) || 0)} className="w-28 rounded border border-gray-300 dark:border-gray-600 bg-transparent px-2 py-1.5 text-sm text-right focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-800 dark:text-gray-100" /></td>
                                            <td className="px-3 py-2"><input type="text" value={item.codigo_ncm} onChange={e => updateItem(item.key, 'codigo_ncm', e.target.value)} className="w-28 rounded border border-gray-300 dark:border-gray-600 bg-transparent px-2 py-1.5 text-sm text-center focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-800 dark:text-gray-100" placeholder="00000000" /></td>
                                            <td className="px-3 py-2 text-right text-sm font-medium text-gray-800 dark:text-gray-100 whitespace-nowrap">{moneyFormatter.format(item.preco_unitario * item.quantidade)}</td>
                                            {/* Coluna Status IA */}
                                            <td className="px-3 py-2 min-w-[130px]">
                                                {item.aiStatus === 'checking' && (
                                                    <span className="flex items-center gap-1 text-xs text-blue-500"><span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />verificando</span>
                                                )}
                                                {item.aiStatus === 'ok' && (
                                                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 dark:bg-emerald-900/40 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-300">Ã¢Å“â€¦ Novo</span>
                                                )}
                                                {item.aiStatus === 'duplicata_exata' && (
                                                    <div className="max-w-[220px]">
                                                        <span className="inline-flex items-center gap-1 rounded-full bg-sky-100 dark:bg-sky-900/40 px-2 py-0.5 text-xs font-medium text-sky-700 dark:text-sky-300">Soma estoque</span>
                                                        <p className="mt-1 text-xs leading-4 text-gray-400 dark:text-gray-500 whitespace-normal break-words" title={item.aiNomeExistente}>{item.aiNomeExistente}</p>
                                                    </div>
                                                )}
                                                {item.aiStatus === 'similar' && (
                                                    <div className="max-w-[220px]">
                                                        <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 dark:bg-amber-900/40 px-2 py-0.5 text-xs font-medium text-amber-700 dark:text-amber-300">Parecido</span>
                                                        <p className="mt-1 text-xs leading-4 text-gray-400 dark:text-gray-500 whitespace-normal break-words" title={item.aiNomeExistente}>{item.aiNomeExistente}</p>
                                                    </div>
                                                )}
                                                {!item.aiStatus && (
                                                    <span className="text-xs text-gray-300 dark:text-gray-600">Ã¢â‚¬â€</span>
                                                )}
                                            </td>
                                            <td className="px-3 py-2"><button type="button" onClick={() => removeItem(item.key)} aria-label={`Remover item ${item.nome}`} className="rounded p-1 text-red-500 transition hover:bg-red-50 dark:hover:bg-red-900/30">Ã¢Å“â€¢</button></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div className="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 p-4">
                        <div className="flex items-start gap-3">
                            <span className="text-xl">Ã¢Å¡Â Ã¯Â¸Â</span>
                            <p className="text-sm text-amber-800 dark:text-amber-200">Revise nomes, quantidades, preÃƒÂ§os e NCM antes de importar. Itens desmarcados nÃƒÂ£o serÃƒÂ£o importados.</p>
                        </div>
                    </div>

                    <div className="flex items-center justify-between">
                        <button type="button" onClick={handleReset} className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-200 transition hover:bg-gray-50">Cancelar</button>
                        <div className="flex items-center gap-3">
                            {itens.some(i => !i.aiStatus) && !aiChecking && (
                                <button type="button" onClick={() => runAiCheck(itens)}
                                    className="rounded-lg border border-blue-300 dark:border-blue-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm font-medium text-blue-600 dark:text-blue-400 transition hover:bg-blue-50 flex items-center gap-2">
                                    Ã°Å¸Â¤â€“ Re-verificar IA
                                </button>
                            )}
                            <button type="button" onClick={handleImport}
                                disabled={importMutation.isPending || selectedItems.length === 0 || aiChecking}
                                className="rounded-lg bg-emerald-600 px-8 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-500/30 transition hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-2">
                                {importMutation.isPending
                                    ? <><span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />Importando...</>
                                    : aiChecking
                                        ? <><span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />Verificando IA...</>
                                        : <>Ã¢Å“â€¦ Importar {selectedItems.length} {selectedItems.length === 1 ? 'Produto' : 'Produtos'}</>
                                }
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* STEP 4: Done */}
            {step === 'done' && (
                <div className="flex flex-col items-center justify-center space-y-6 rounded-lg bg-white p-12 shadow dark:bg-gray-800">
                    <div className="flex h-20 w-20 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/40 text-4xl">Ã¢Å“â€¦</div>
                    <div className="text-center">
                        <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">ImportaÃƒÂ§ÃƒÂ£o ConcluÃƒÂ­da!</h2>
                        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">Produtos novos foram cadastrados e os jÃƒÂ¡ existentes tiveram o estoque atualizado.</p>
                    </div>
                    <div className="flex gap-3">
                        <button type="button" onClick={handleReset} className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700">Ã°Å¸â€œÂ¤ Importar Outra Nota</button>
                        <Link to="/produtos" className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-6 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-200 transition hover:bg-gray-50">Ver Produtos</Link>
                    </div>
                </div>
            )}
        </div>
    )
}

export default ImportarNota
