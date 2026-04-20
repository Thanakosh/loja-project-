import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

type AiStatus = 'idle' | 'checking' | 'duplicata_exata' | 'similar' | 'ok'

interface DuplicateCandidate {
  produto_id: number
  produto_nome: string
  similaridade: number
  nivel: 'duplicata' | 'alerta'
}

export interface AiResult {
  status: AiStatus
  candidato?: DuplicateCandidate
}

export function AiFeedback({ result }: { result: AiResult }) {
  if (result.status === 'idle') return null

  if (result.status === 'checking') {
    return (
      <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
        <Loader2 className="size-3 animate-spin" />
        <span>Verificando duplicatas...</span>
      </div>
    )
  }

  if (result.status === 'ok') {
    return (
      <Alert className="mt-2 border-primary/20 bg-primary/5 text-primary">
        <AlertTitle>Nome disponivel</AlertTitle>
        <AlertDescription className="text-primary/90">
          Nenhum produto parecido foi encontrado.
        </AlertDescription>
      </Alert>
    )
  }

  if (result.status === 'duplicata_exata' && result.candidato) {
    return (
      <Alert className="mt-2 border-sky-200 bg-sky-50 text-sky-900 dark:border-sky-800 dark:bg-sky-950/40 dark:text-sky-100">
        <AlertTitle>Produto ja existe no estoque</AlertTitle>
        <AlertDescription className="text-sky-800 dark:text-sky-200">
          "{result.candidato.produto_nome}" ja esta cadastrado. Ao salvar, a quantidade sera somada ao estoque existente.
        </AlertDescription>
      </Alert>
    )
  }

  if (result.status === 'similar' && result.candidato) {
    const similaridade = Math.round(result.candidato.similaridade * 100)
    const forte = result.candidato.nivel === 'duplicata'

    return (
      <Alert
        variant={forte ? 'destructive' : 'default'}
        className={cn(
          'mt-2',
          !forte && 'border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100',
        )}
      >
        <AlertTitle>
          {forte ? 'Possivel duplicata detectada' : 'Nome parecido encontrado'} · {similaridade}% similar
        </AlertTitle>
        <AlertDescription className={cn(!forte && 'text-amber-800 dark:text-amber-200')}>
          Ja existe "{result.candidato.produto_nome}". Revise antes de salvar.
        </AlertDescription>
      </Alert>
    )
  }

  return null
}
