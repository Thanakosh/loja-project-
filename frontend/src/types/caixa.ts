export type TipoMovimentacaoCaixa = 'sangria' | 'suprimento'

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
  total_sangrias: number
  total_suprimentos: number
  valor_em_dinheiro_vendas: number
  saldo_esperado: number
  diferenca?: number | null
}

export interface MovimentacaoCaixa {
  id: number
  caixa_id: number
  tipo: TipoMovimentacaoCaixa
  valor: number
  motivo: string
  observacao?: string | null
  usuario_id: number
  usuario_nome?: string | null
  created_at: string
}

export interface CaixaAberturaPayload {
  valor_abertura: number
  observacao?: string | null
}

export interface CaixaFechamentoPayload {
  valor_fechamento: number
  observacao?: string | null
}

export interface MovimentacaoCaixaPayload {
  tipo: TipoMovimentacaoCaixa
  valor: number
  motivo: string
  observacao?: string | null
}
