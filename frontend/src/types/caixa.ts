export interface CaixaDiario {
  id: number
  data_abertura: string
  data_fechamento?: string | null
  valor_abertura: number
  valor_fechamento?: number | null
  status: 'aberto' | 'fechado'
  observacao?: string | null
  usuario_id: number
  usuario_abertura_id: number
  usuario_abertura_nome?: string | null
  usuario_fechamento_id?: number | null
  usuario_fechamento_nome?: string | null
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
