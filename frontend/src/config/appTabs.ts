export type AppTabId =
  | 'caixa'
  | 'pdv'
  | 'vendas'
  | 'produtos'
  | 'estoque'
  | 'orcamentos'
  | 'fornecedores'
  | 'notas_fiscais'
  | 'importar_nota'
  | 'clientes'
  | 'contas_receber'
  | 'relatorios'
  | 'configuracoes'

export interface AppTabDefinition {
  id: AppTabId
  label: string
  path: string
}

export const MANAGEABLE_TABS: AppTabDefinition[] = [
  { id: 'caixa', label: 'Caixa', path: '/caixa' },
  { id: 'pdv', label: 'PDV', path: '/pdv' },
  { id: 'vendas', label: 'Vendas', path: '/vendas' },
  { id: 'produtos', label: 'Produtos', path: '/produtos' },
  { id: 'estoque', label: 'Estoque', path: '/estoque' },
  { id: 'orcamentos', label: 'Orcamentos', path: '/orcamentos' },
  { id: 'fornecedores', label: 'Fornecedores', path: '/fornecedores' },
  { id: 'notas_fiscais', label: 'Notas Fiscais', path: '/notas-fiscais' },
  { id: 'importar_nota', label: 'Importar Nota', path: '/importar-nota' },
  { id: 'clientes', label: 'Clientes', path: '/clientes' },
  { id: 'contas_receber', label: 'Contas a Receber', path: '/contas-receber' },
  { id: 'relatorios', label: 'Relatorios', path: '/relatorios' },
  { id: 'configuracoes', label: 'Configuracoes', path: '/configuracoes/loja' },
]

const TAB_LABELS = new Map(MANAGEABLE_TABS.map((tab) => [tab.id, tab.label]))
const TAB_IDS = new Set(MANAGEABLE_TABS.map((tab) => tab.id))

export const isAppTabId = (value: string): value is AppTabId => TAB_IDS.has(value as AppTabId)

export const getTabLabel = (tabId: AppTabId): string => TAB_LABELS.get(tabId) ?? tabId
