import { useState } from 'react'

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

interface FiscalAuditPanelProps {
  auditoria: AuditoriaFiscal | null
  validacaoCruzada: ValidacaoCruzadaItem[]
}

const CLASSIFICACAO_CONFIG = {
  baixo: {
    emoji: '🟢',
    label: 'Baixo Risco',
    bg: 'bg-emerald-50 dark:bg-emerald-900/20',
    border: 'border-emerald-200 dark:border-emerald-700',
    text: 'text-emerald-800 dark:text-emerald-200',
  },
  medio: {
    emoji: '🟡',
    label: 'Risco Medio',
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    border: 'border-amber-200 dark:border-amber-700',
    text: 'text-amber-800 dark:text-amber-200',
  },
  alto: {
    emoji: '🔴',
    label: 'Alto Risco',
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-700',
    text: 'text-red-800 dark:text-red-200',
  },
} as const

const SEVERIDADE_CONFIG = {
  erro: {
    emoji: '❌',
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-700',
    text: 'text-red-700 dark:text-red-300',
  },
  alerta: {
    emoji: '⚠️',
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    border: 'border-amber-200 dark:border-amber-700',
    text: 'text-amber-700 dark:text-amber-300',
  },
  info: {
    emoji: 'ℹ️',
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-blue-200 dark:border-blue-700',
    text: 'text-blue-700 dark:text-blue-300',
  },
} as const

const FiscalAuditPanel = ({ auditoria, validacaoCruzada }: FiscalAuditPanelProps) => {
  const [expandido, setExpandido] = useState(false)

  if (!auditoria && validacaoCruzada.length === 0) return null

  const config = auditoria ? CLASSIFICACAO_CONFIG[auditoria.classificacao] : CLASSIFICACAO_CONFIG.baixo
  const erros = validacaoCruzada.filter((item) => item.severidade === 'erro')
  const alertas = validacaoCruzada.filter((item) => item.severidade === 'alerta')
  const infos = validacaoCruzada.filter((item) => item.severidade === 'info')
  const fatoresFalha = auditoria?.fatores.filter((fator) => fator.resultado === 'falha') ?? []

  return (
    <div className={`overflow-hidden rounded-lg border ${config.border} ${config.bg} transition-all`}>
      <button
        type="button"
        onClick={() => setExpandido((prev) => !prev)}
        className="flex w-full items-center justify-between px-5 py-4 transition hover:opacity-90"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{config.emoji}</span>
          <div className="text-left">
            <h3 className={`text-sm font-semibold ${config.text}`}>Auditoria Fiscal — {config.label}</h3>
            <p className={`mt-0.5 text-xs ${config.text} opacity-75`}>
              Score: {auditoria?.score ?? 0}/100 · Confianca: {Math.round((auditoria?.confianca ?? 0) * 100)}%
              {validacaoCruzada.length > 0 ? ` · ${validacaoCruzada.length} verificacao(oes)` : ''}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {erros.length > 0 ? (
            <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700 dark:bg-red-800 dark:text-red-200">
              {erros.length} erro(s)
            </span>
          ) : null}
          {alertas.length > 0 ? (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-800 dark:text-amber-200">
              {alertas.length} alerta(s)
            </span>
          ) : null}
          <span className={`text-sm ${config.text} transition-transform ${expandido ? 'rotate-180' : ''}`}>▼</span>
        </div>
      </button>

      {expandido ? (
        <div className="space-y-3 border-t border-gray-200/50 px-5 pb-4 pt-3 dark:border-gray-700/50">
          {fatoresFalha.length > 0 ? (
            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Regras fiscais com falha
              </h4>
              <div className="space-y-1.5">
                {fatoresFalha.map((fator, index) => (
                  <div key={`${fator.regra}-${index}`} className="flex items-start gap-2 rounded-lg bg-white/60 px-3 py-2 text-sm dark:bg-gray-800/60">
                    <span className="mt-0.5 text-red-500">⚠️</span>
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-gray-700 dark:text-gray-200">{fator.regra.replace(/_/g, ' ')}</p>
                      <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">{fator.detalhe}</p>
                    </div>
                    <span className="whitespace-nowrap text-xs text-gray-400">peso {fator.peso}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {validacaoCruzada.length > 0 ? (
            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Validacao cruzada
              </h4>
              <div className="space-y-1.5">
                {validacaoCruzada.map((item, index) => {
                  const severidade = SEVERIDADE_CONFIG[item.severidade] ?? SEVERIDADE_CONFIG.info
                  return (
                    <div
                      key={`${item.regra}-${index}`}
                      className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-sm ${severidade.bg} ${severidade.border}`}
                    >
                      <span className="mt-0.5">{severidade.emoji}</span>
                      <p className={`flex-1 ${severidade.text}`}>{item.descricao}</p>
                    </div>
                  )
                })}
              </div>
            </div>
          ) : null}

          {fatoresFalha.length === 0 && validacaoCruzada.length === 0 ? (
            <p className="flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400">
              ✅ Nenhuma inconsistência detectada na nota fiscal.
            </p>
          ) : null}

          <p className="pt-1 text-xs text-gray-400 dark:text-gray-500">
            Motor v{auditoria?.versao_engine ?? '?'} · {infos.length > 0 ? `${infos.length} informativo(s)` : 'Sem informativos'}
          </p>
        </div>
      ) : null}
    </div>
  )
}

export default FiscalAuditPanel
