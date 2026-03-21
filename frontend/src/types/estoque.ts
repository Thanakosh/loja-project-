import type { PaginatedResponse } from './common'

export interface EstoqueResumo {
  id: number
  produto_id?: number
  nome: string
  nome_produto?: string
  codigo_barras?: string | null
  unidade?: string | null
  estoque_atual?: number
  quantidade_atual?: number
  estoque_minimo?: number
  quantidade_minima?: number
  estoque_baixo?: boolean
}

export interface EstoqueAlerta {
  id?: number
  produto_id?: number
  nome_produto?: string
  nome?: string
  produto_nome?: string
  quantidade_atual?: number
  estoque_atual?: number
  estoque_minimo?: number
  quantidade_minima?: number
  estoque_baixo?: boolean
}

export interface MovimentacaoEstoque {
  id: number
  produto_id: number
  tipo: 'entrada' | 'saida' | 'ajuste' | 'devolucao'
  quantidade: number
  motivo: string | null
  usuario_id: number | null
  data_transacao: string
}

export interface TransacaoEstoquePayload {
  produto_id: number
  tipo: 'entrada' | 'saida' | 'ajuste' | 'devolucao'
  quantidade: number
  motivo: string
}

export type EstoqueListResponse = PaginatedResponse<EstoqueResumo>
