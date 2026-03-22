export interface ConfiguracaoLoja {
  id: number
  cnpj: string | null
  razao_social: string | null
  nome_fantasia: string | null
  logradouro: string | null
  numero: string | null
  bairro: string | null
  municipio: string | null
  porte: 'ME' | 'EPP' | 'MEI' | null
  inscricao_estadual: string | null
  inscricao_municipal: string | null
  regime_tributario: 'simples_nacional' | 'regime_normal'
  uf: string
  cep: string | null
  pais: string | null
  fone: string | null
  email: string | null
  cnae: string | null
  updated_at: string
}

export interface ConfiguracaoLojaPayload {
  cnpj: string | null
  razao_social: string | null
  nome_fantasia: string | null
  logradouro: string | null
  numero: string | null
  bairro: string | null
  municipio: string | null
  porte: 'ME' | 'EPP' | 'MEI' | null
  inscricao_estadual: string | null
  inscricao_municipal: string | null
  regime_tributario: 'simples_nacional' | 'regime_normal'
  uf: string
  cep: string | null
  pais: string | null
  fone: string | null
  email: string | null
  cnae: string | null
}
