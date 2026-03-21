import type { PaginatedResponse } from './common'

export type StatusOrcamento = 'aberto' | 'aprovado' | 'cancelado' | 'convertido'

export interface ClienteSugestao {
  id: number
  nome: string
  cpf_cnpj?: string | null
}

export interface ProdutoSugestao {
  id: number
  nome: string
  preco_unitario: number
  preco_liquido: number
  unidade_medida?: string | null
}

export interface OrcamentoItem {
  id: number
  descricao: string
  quantidade: number
  preco_unitario: number
  desconto: number
  preco_total: number
}

export interface Orcamento {
  id: number
  cliente_id?: number | null
  cliente_nome?: string | null
  status: StatusOrcamento
  desconto_geral: number
  observacao?: string | null
  data_criacao: string
  data_validade?: string | null
  venda_id?: number | null
  itens: OrcamentoItem[]
  total: number
}

export type OrcamentoListResponse = PaginatedResponse<Orcamento>
