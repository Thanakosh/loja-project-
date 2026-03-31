import type { PaginatedResponse } from './common'

export interface VendaItem {
  id: number
  nome_produto: string
  quantidade: number
  preco_unitario: number
  preco_total: number
  unidade?: string
  desconto?: number
}

export interface VendaPagamento {
  forma_pagamento: number
  forma_pagamento_label?: string | null
  valor: number
  troco?: number
  valor_recebido?: number | null
}

export interface Venda {
  id: number
  numero_legado: number
  data: string
  total: number
  desconto: number
  forma_pagamento?: number | null
  forma_pagamento_label?: string | null
  troco?: number
  pagamentos?: VendaPagamento[]
  cancelada: boolean
  observacao?: string
  cliente_id?: number
  itens: VendaItem[]
}

export interface VendasParams {
  page?: number
  page_size?: number
  start_date?: string
  end_date?: string
}

export interface VendaPDVCreate {
  cliente_id?: number
  forma_pagamento?: number
  desconto_geral: number
  observacao?: string
  autorizacao_terceiro_nome?: string
  autorizacao_terceiro_documento?: string
  autorizacao_terceiro_observacao?: string
  parcelas: number
  pagamentos: VendaPagamento[]
  itens: {
    produto_id: number
    quantidade: number
    preco_unitario: number
    desconto: number
  }[]
}

export interface VendaPDVRead {
  id: number
  numero_legado?: string | number | null
  total: number
  forma_pagamento?: number | null
  forma_pagamento_label?: string | null
  total_recebido?: number
  troco?: number
  pagamentos?: VendaPagamento[]
}

export type VendasPaginadas = PaginatedResponse<Venda>
