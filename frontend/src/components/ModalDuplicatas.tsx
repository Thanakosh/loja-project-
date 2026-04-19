import { useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'

import type {
  DuplicateResolution,
  DuplicateResolutionMode,
  SimilarItem,
} from '../types/importacaoNota'

interface ModalDuplicatasProps {
  itens: SimilarItem[]
  onConfirmar: (resolutions: DuplicateResolution[]) => void
  onCancelar: () => void
}

interface DuplicateChoiceState {
  key: string
  mode: DuplicateResolutionMode
  customNome: string
}

const normalizeToken = (value: string) =>
  value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^\w]/g, '')
    .toLowerCase()

const tokenizeName = (value: string) =>
  value
    .split(/(\s+|[-/,().])/)
    .map((token) => token.trim())
    .filter(Boolean)

const HighlightedName = ({
  value,
  reference,
  tone,
}: {
  value: string
  reference: string
  tone: 'importado' | 'existente'
}) => {
  const referenceTokens = new Set(tokenizeName(reference).map(normalizeToken))

  return (
    <div className="flex flex-wrap gap-1">
      {tokenizeName(value).map((token, index) => {
        const present = referenceTokens.has(normalizeToken(token))
        const emphasisClass = present
          ? 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200'
          : tone === 'importado'
            ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200'
            : 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200'

        return (
          <span
            key={`${token}-${index}`}
            className={`rounded-md px-2 py-0.5 text-xs font-medium ${emphasisClass}`}
          >
            {token}
          </span>
        )
      })}
    </div>
  )
}

const createInitialChoices = (itens: SimilarItem[]): Record<string, DuplicateChoiceState> =>
  Object.fromEntries(
    itens.map((item) => [
      item.key,
      {
        key: item.key,
        mode: 'importado' satisfies DuplicateResolutionMode,
        customNome: item.nomeImportando,
      },
    ])
  )

const ModalDuplicatas = ({ itens, onConfirmar, onCancelar }: ModalDuplicatasProps) => {
  const [choices, setChoices] = useState<Record<string, DuplicateChoiceState>>(() =>
    createInitialChoices(itens)
  )

  const updateChoice = (
    key: string,
    field: keyof DuplicateChoiceState,
    value: DuplicateChoiceState[keyof DuplicateChoiceState]
  ) => {
    setChoices((prev) => ({
      ...prev,
      [key]: {
        ...prev[key],
        [field]: value,
      },
    }))
  }

  const applyToSameMatch = (sourceItem: SimilarItem) => {
    const sourceChoice = choices[sourceItem.key]
    if (!sourceChoice) return

    setChoices((prev) => {
      const next = { ...prev }
      for (const item of itens) {
        if (item.produtoId !== sourceItem.produtoId) continue
        next[item.key] = {
          ...next[item.key],
          mode: sourceChoice.mode,
          customNome:
            sourceChoice.mode === 'personalizado'
              ? sourceChoice.customNome
              : sourceChoice.mode === 'existente'
                ? item.nomeExistente
                : item.nomeImportando,
        }
      }
      return next
    })
  }

  const hasInvalidCustomName = itens.some((item) => {
    const choice = choices[item.key]
    return choice?.mode === 'personalizado' && !choice.customNome.trim()
  })

  const handleConfirm = () => {
    const resolutions: DuplicateResolution[] = itens.map((item) => {
      const choice = choices[item.key]
      const resolvedName =
        choice.mode === 'existente'
          ? item.nomeExistente
          : choice.mode === 'personalizado'
            ? choice.customNome.trim()
            : item.nomeImportando

      return {
        key: item.key,
        mode: choice.mode,
        resolvedName,
        produtoId: item.produtoId,
      }
    })

    onConfirmar(resolutions)
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onCancelar()}>
      <DialogContent className="max-w-5xl gap-0 overflow-hidden p-0" showCloseButton={false}>
        <DialogHeader className="gap-3 border-b border-amber-200 bg-amber-50 px-6 py-4 dark:border-amber-700 dark:bg-amber-900/30">
          <div className="flex items-start gap-3">
            <div className="flex size-10 items-center justify-center rounded-full bg-amber-100 text-sm font-semibold text-amber-800 dark:bg-amber-800/60 dark:text-amber-100">
              IA
            </div>
            <div className="space-y-1">
              <DialogTitle className="text-amber-900 dark:text-amber-100">
                IA detectou nomes similares
              </DialogTitle>
              <DialogDescription className="text-xs text-amber-700 dark:text-amber-300">
                Escolha como cada item deve ser importado para evitar cadastros duplicados.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="max-h-[70vh] space-y-4 overflow-y-auto px-6 py-4">
          {itens.map((item) => {
            const choice = choices[item.key]
            const resolvedPreview =
              choice.mode === 'existente'
                ? item.nomeExistente
                : choice.mode === 'personalizado'
                  ? choice.customNome
                  : item.nomeImportando

            return (
              <div
                key={item.key}
                className={`rounded-2xl border p-4 ${
                  item.nivel === 'duplicata'
                    ? 'border-red-200 bg-red-50/70 dark:border-red-700 dark:bg-red-900/20'
                    : 'border-amber-200 bg-amber-50/70 dark:border-amber-700 dark:bg-amber-900/20'
                }`}
              >
                <div className="flex flex-col gap-4">
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                    <div className="min-w-0 space-y-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${
                            item.nivel === 'duplicata'
                              ? 'bg-red-100 text-red-700 dark:bg-red-800 dark:text-red-200'
                              : 'bg-amber-100 text-amber-700 dark:bg-amber-800 dark:text-amber-200'
                          }`}
                        >
                          {item.nivel === 'duplicata' ? 'Possivel duplicata' : 'Nome parecido'}
                          {' · '}
                          {Math.round(item.similaridade * 100)}% similar
                        </span>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => applyToSameMatch(item)}
                          className="h-7 bg-white/90 text-xs dark:bg-gray-800"
                        >
                          Aplicar a todos com mesmo match
                        </Button>
                      </div>

                      <div className="grid gap-3 md:grid-cols-2">
                        <div className="rounded-xl border border-blue-200 bg-white/70 p-3 dark:border-blue-800 dark:bg-gray-800/70">
                          <p className="mb-2 text-xs text-gray-500 dark:text-gray-400">Nome importado</p>
                          <HighlightedName
                            value={item.nomeImportando}
                            reference={item.nomeExistente}
                            tone="importado"
                          />
                        </div>
                        <div className="rounded-xl border border-amber-200 bg-white/70 p-3 dark:border-amber-800 dark:bg-gray-800/70">
                          <p className="mb-2 text-xs text-gray-500 dark:text-gray-400">Nome existente</p>
                          <HighlightedName
                            value={item.nomeExistente}
                            reference={item.nomeImportando}
                            tone="existente"
                          />
                        </div>
                      </div>
                    </div>

                    <div className="rounded-xl border border-gray-200 bg-white/80 px-4 py-3 dark:border-gray-700 dark:bg-gray-900/40 lg:w-64">
                      <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                        Nome final
                      </p>
                      <p className="mt-2 break-words text-sm font-semibold text-gray-800 dark:text-gray-100">
                        {resolvedPreview || 'Defina um nome'}
                      </p>
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        {choice.mode === 'existente'
                          ? 'O backend vai somar o estoque ao produto ja cadastrado.'
                          : choice.mode === 'personalizado'
                            ? 'O item sera enviado com o nome digitado abaixo.'
                            : 'O item sera importado com o nome vindo do XML.'}
                      </p>
                    </div>
                  </div>

                  <div className="grid gap-3 lg:grid-cols-[1fr_1fr_1.4fr]">
                    <label className="rounded-xl border border-gray-200 bg-white/80 p-3 text-sm text-gray-700 dark:border-gray-700 dark:bg-gray-900/40 dark:text-gray-200">
                      <div className="flex items-start gap-2">
                        <input
                          type="radio"
                          name={`modo-${item.key}`}
                          checked={choice.mode === 'importado'}
                          onChange={() => updateChoice(item.key, 'mode', 'importado')}
                          className="mt-1 h-4 w-4 border-gray-300 text-blue-600"
                        />
                        <div>
                          <p className="font-semibold">Usar nome importado</p>
                          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                            Mantem o nome do XML e cria um cadastro novo se nao houver match exato.
                          </p>
                        </div>
                      </div>
                    </label>

                    <label className="rounded-xl border border-gray-200 bg-white/80 p-3 text-sm text-gray-700 dark:border-gray-700 dark:bg-gray-900/40 dark:text-gray-200">
                      <div className="flex items-start gap-2">
                        <input
                          type="radio"
                          name={`modo-${item.key}`}
                          checked={choice.mode === 'existente'}
                          onChange={() => updateChoice(item.key, 'mode', 'existente')}
                          className="mt-1 h-4 w-4 border-gray-300 text-blue-600"
                        />
                        <div>
                          <p className="font-semibold">Usar nome existente</p>
                          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                            Reaproveita o cadastro encontrado e deixa o merge de estoque acontecer no backend.
                          </p>
                        </div>
                      </div>
                    </label>

                    <div className="rounded-xl border border-gray-200 bg-white/80 p-3 text-sm text-gray-700 dark:border-gray-700 dark:bg-gray-900/40 dark:text-gray-200">
                      <label className="flex items-start gap-2">
                        <input
                          type="radio"
                          name={`modo-${item.key}`}
                          checked={choice.mode === 'personalizado'}
                          onChange={() => updateChoice(item.key, 'mode', 'personalizado')}
                          className="mt-1 h-4 w-4 border-gray-300 text-blue-600"
                        />
                        <div className="flex-1">
                          <p className="font-semibold">Digitar nome personalizado</p>
                          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                            Define manualmente o nome final deste item antes de enviar.
                          </p>
                          <Input
                            type="text"
                            value={choice.customNome}
                            onChange={(event) => updateChoice(item.key, 'customNome', event.target.value)}
                            onFocus={() => updateChoice(item.key, 'mode', 'personalizado')}
                            placeholder="Digite o nome final"
                            className="mt-3 bg-white dark:bg-gray-800"
                          />
                        </div>
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        <DialogFooter className="flex flex-col gap-3 border-t border-gray-200 bg-gray-50 px-6 py-4 dark:border-gray-700 dark:bg-gray-700/50 sm:items-center sm:justify-between">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Revise os nomes finais antes de confirmar. A opcao &quot;Usar nome existente&quot; apenas troca o
            nome enviado para ativar o merge automatico ja existente no backend.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Button type="button" variant="outline" onClick={onCancelar}>
              Voltar para revisao
            </Button>
            <Button type="button" onClick={handleConfirm} disabled={hasInvalidCustomName}>
              Confirmar resolucoes e importar
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default ModalDuplicatas
