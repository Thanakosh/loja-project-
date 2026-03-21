export type DuplicateLevel = 'duplicata' | 'alerta'

export type DuplicateResolutionMode = 'importado' | 'existente' | 'personalizado'

export interface SimilarItem {
  key: string
  nomeImportando: string
  nomeExistente: string
  produtoId: number
  similaridade: number
  nivel: DuplicateLevel
}

export interface DuplicateResolution {
  key: string
  mode: DuplicateResolutionMode
  resolvedName: string
  produtoId: number
}
