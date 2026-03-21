import type { PaginatedResponse } from './common'

export interface Produto {
  id: number
  nome: string
  descricao?: string | null
  fornecedor: string
  preco_unitario: number
  preco_liquido: number
  codigo_barras?: string | null
  codigo_ncm?: string | null
  unidade?: string | null
  unidade_medida?: string | null
  estoque_atual: number
  estoque_baixo: boolean
  estoque_minimo: number
  ativo: boolean
  data_emissao?: string | null
  numero_nota?: string | null
  cnpj_fornecedor?: string | null
  categoria_id?: number | null
  permite_fracionado?: boolean
  preco_custo?: number | null
  preco_varejo?: number | null
  preco_atacado?: number | null
  qtd_minima_atacado?: number | null
}

export interface CategoriaTreeNode {
  id: number
  nome: string
  parent_id?: number | null
  ativo: boolean
  children: CategoriaTreeNode[]
}

export interface ProdutoFormPayload {
  nome: string
  fornecedor: string
  preco_unitario: number
  preco_liquido: number
  estoque_minimo: number
  quantidade_inicial?: number
  unidade?: string
  unidade_medida?: string
  codigo_ncm?: string
  descricao?: string
  categoria_id?: number
  preco_custo?: number
  preco_varejo?: number
  preco_atacado?: number
  qtd_minima_atacado?: number
}

export interface ProdutoDuplicateCandidate {
  produto_id: number
  produto_nome: string
  similaridade: number
  nivel: 'duplicata' | 'alerta'
}

export interface DuplicateCheckResponse {
  tem_duplicata: boolean
  tem_alerta: boolean
  metodo: string
  candidatos: ProdutoDuplicateCandidate[]
}

export interface ProdutoMutationResult {
  data: Produto
  acao: string
}

export type ProdutoListResponse = PaginatedResponse<Produto>
