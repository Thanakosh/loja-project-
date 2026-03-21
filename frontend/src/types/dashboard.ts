export interface FiscalRiskDashboardSupplier {
  nome: string
  alertas: number
}

export interface FiscalRiskDashboardResponse {
  total_notas: number
  score_medio: number
  notas_risco_alto: number
  periodo_rotulo: string
  top_fornecedores_alertas: FiscalRiskDashboardSupplier[]
}
