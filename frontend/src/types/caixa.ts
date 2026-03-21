export interface CaixaDiario {
  id: number
  data_abertura: string
  data_fechamento?: string | null
  valor_abertura: number
  valor_fechamento?: number | null
  status: 'aberto' | 'fechado'
  observacao?: string | null
  usuario_id: number
  diferenca?: number | null
}

export interface CaixaAberturaPayload {
  valor_abertura: number
  observacao?: string | null
}

export interface CaixaFechamentoPayload {
  valor_fechamento: number
  observacao?: string | null
}
