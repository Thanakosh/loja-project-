import type { PaginatedResponse } from './common'

export interface ContaReceber {
  id: number
  cliente_id?: number
  cliente_nome?: string
  documento: number
  parcela: number
  total_parcelas?: number
  data_emissao?: string
  data_vencimento?: string
  data_pagamento?: string
  valor: number
  valor_pago: number
  saldo_em_aberto: number
  desconto: number
  juros: number
  historico?: string
  situacao: 'aberta' | 'parcial' | 'quitada'
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
