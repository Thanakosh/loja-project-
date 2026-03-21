---
task_id: TASK-022
title: "Implementar controle de caixa diario (abertura/fechamento)"
status: concluida
priority: media
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Conforme STRATEGY.md Fase 3 e RECOMENDACOES_TECNICAS.md item "Financeiro",
implementar o modulo de controle de caixa diario.

### Backend

1. Criar modelo `CaixaDiario` (id, data_abertura, data_fechamento, valor_abertura,
   valor_fechamento, status, usuario_id).
2. Endpoints:
   - `POST /api/v1/caixa/abrir` - abre caixa com valor inicial.
   - `POST /api/v1/caixa/fechar` - fecha caixa com conferencia.
   - `GET /api/v1/caixa/atual` - retorna caixa aberto do dia.
   - `GET /api/v1/caixa/historico` - listagem paginada.
3. Vincular vendas do PDV ao caixa aberto.

### Frontend

1. Nova pagina `CaixaDiario.tsx` com abertura, fechamento e historico.
2. Bloquear PDV se caixa nao estiver aberto (aviso visual).

### Criterio de aceite

- Nao e possivel registrar venda no PDV sem caixa aberto.
- Conferencia de fechamento exibe diferenca (se houver).
- Testes de backend para abrir, fechar e listar caixa.
