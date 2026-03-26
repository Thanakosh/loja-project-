export interface Fornecedor {
  id: number
  razao_social: string
  nome_fantasia?: string | null
  cnpj: string
  email?: string | null
  telefone?: string | null
  endereco?: string | null
  cidade?: string | null
  uf?: string | null
  cep?: string | null
}

export interface FornecedorPayload {
  razao_social: string
  nome_fantasia?: string
  cnpj: string
  email?: string
  telefone?: string
  endereco?: string
  cidade?: string
  uf?: string
  cep?: string
}
