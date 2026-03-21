export interface Fornecedor {
  id: number
  razao_social: string
  nome_fantasia?: string | null
  cnpj: string
  email?: string | null
  telefone?: string | null
}

export interface FornecedorPayload {
  razao_social: string
  nome_fantasia?: string
  cnpj: string
  email?: string
  telefone?: string
}
