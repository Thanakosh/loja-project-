import type { PaginatedResponse } from './common'

export interface ContaReceber {
  id: number
  cliente_id?: number
  documento: number
  parcela: number
  data_emissao?: string
  data_vencimento?: string
  data_pagamento?: string
  valor: number
  valor_pago: number
  desconto: number
  juros: number
  historico?: string
  em_aberto: boolean
}

export interface ContaReceberResumo {
  total_em_aberto: number
  total_vencido: number
  quantidade_em_aberto: number
}

export interface BaixaContaReceberPayload {
  data_pagamento: string
  valor_pago: number
  desconto: number
  juros: number
  historico: string | null
}

export type ContaReceberListResponse = PaginatedResponse<ContaReceber>
