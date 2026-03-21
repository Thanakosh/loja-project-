export interface Cliente {
  id: number
  nome: string
  cpf_cnpj?: string | null
  telefone?: string | null
  cidade?: string | null
  uf?: string | null
  observacao?: string | null
  historico_observacoes?: string | null
  codigo_legado?: number | null
}

export interface ClientePayload {
  nome: string
  cpf_cnpj?: string
  telefone?: string
  cidade?: string
  uf?: string
  codigo_legado?: number
}
