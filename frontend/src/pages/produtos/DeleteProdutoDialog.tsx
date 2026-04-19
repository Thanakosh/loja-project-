import { useId, useState } from 'react'
import { AlertTriangle, Loader2 } from 'lucide-react'

import type { Produto } from '../../types/produtos'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

interface DeleteProdutoDialogProps {
  produto: Produto | null
  isPending: boolean
  onConfirmar: (produtoId: number) => void
  onClose: () => void
}

export function DeleteProdutoDialog({
  produto,
  isPending,
  onConfirmar,
  onClose,
}: DeleteProdutoDialogProps) {
  const [confirmacaoTexto, setConfirmacaoTexto] = useState('')
  const inputId = useId()

  if (!produto) return null

  const nomeEsperado = produto.nome.trim()
  const confirmacaoCorreta = confirmacaoTexto.trim() === nomeEsperado

  return (
    <Dialog
      open={Boolean(produto)}
      onOpenChange={(open) => {
        if (!open && !isPending) onClose()
      }}
    >
      <DialogContent
        showCloseButton={false}
        className="sm:max-w-lg"
        onEscapeKeyDown={(event) => {
          if (isPending) event.preventDefault()
        }}
        onInteractOutside={(event) => {
          if (isPending) event.preventDefault()
        }}
      >
        <DialogHeader>
          <div className="mb-2 inline-flex size-10 items-center justify-center rounded-lg bg-destructive/10 text-destructive">
            <AlertTriangle className="size-5" />
          </div>
          <DialogTitle>Excluir produto permanentemente</DialogTitle>
          <DialogDescription>
            Esta acao remove o cadastro, o historico de movimentacoes e os dados associados.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <Card size="sm" className="bg-muted/40">
            <CardContent className="space-y-1 pt-4">
              <p className="font-medium">{produto.nome}</p>
              <p className="text-xs text-muted-foreground">Fornecedor: {produto.fornecedor}</p>
              <p className="text-xs text-muted-foreground">
                Estoque atual:{' '}
                <span className={cn('font-semibold', produto.estoque_atual > 0 && 'text-amber-600 dark:text-amber-400')}>
                  {produto.estoque_atual}
                </span>
              </p>
            </CardContent>
          </Card>

          <Alert variant="destructive">
            <AlertTitle>O que sera removido</AlertTitle>
            <AlertDescription>
              <ul className="list-disc space-y-1 pl-4">
                <li>Cadastro do produto</li>
                <li>Historico de movimentacoes de estoque</li>
                <li>Embeddings e dados de IA associados</li>
              </ul>
            </AlertDescription>
          </Alert>

          <div className="space-y-2">
            <Label htmlFor={inputId}>
              Digite <span className="font-semibold">"{nomeEsperado}"</span> para confirmar
            </Label>
            <Input
              id={inputId}
              value={confirmacaoTexto}
              onChange={(event) => setConfirmacaoTexto(event.target.value)}
              placeholder="Digite o nome exato do produto"
              autoComplete="off"
              className={cn(
                confirmacaoTexto.length > 0 && !confirmacaoCorreta && 'border-destructive focus-visible:border-destructive focus-visible:ring-destructive/20',
              )}
            />
            {confirmacaoTexto.length > 0 && !confirmacaoCorreta && (
              <p className="text-xs text-destructive">O nome digitado nao confere.</p>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose} disabled={isPending}>
            Cancelar
          </Button>
          <Button
            type="button"
            onClick={() => onConfirmar(produto.id)}
            disabled={!confirmacaoCorreta || isPending}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isPending && <Loader2 className="size-4 animate-spin" />}
            Excluir permanentemente
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
